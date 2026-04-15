#!/usr/bin/env python3
"""Nutshell compress orchestrator.

Reads a markdown file, extracts YAML frontmatter, sends the body to Claude
via the claude --print CLI for compression into nutshell-speak, validates
the result against the original, retries once with a targeted cherry-pick
fix prompt if validation fails, and restores the original from memory on
final failure.

See skills/config-nut/SKILL.md (Compression Rules section) for the
canonical human-readable rule spec. build_compress_prompt() below embeds
the same rules as a string - keep in sync with the SKILL.md file by hand.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

from .detect import should_compress
from .validate import validate

# MAX_RETRIES = 2 means 2 total attempts: attempt 0 validates the initial
# compression; attempt 1 validates a targeted fix. If attempt 1 fails, the
# original is restored from the in-memory original_bytes variable.
MAX_RETRIES = 2

# 250KB. Halved from caveman's 500KB because the fix prompt embeds both
# original and compressed together - a 250KB original keeps the combined
# fix-prompt payload within safe subprocess and context bounds.
MAX_FILE_SIZE = 250_000

SUBPROCESS_TIMEOUT = 300  # seconds

# Truncate subprocess stderr before re-raising to reduce the chance of
# leaking secrets via error messages (e.g. auth tokens printed on failure).
STDERR_SCRUB_LIMIT = 100

OUTER_FENCE_REGEX = re.compile(
    r"\A\s*(`{3,}|~{3,})[^\n]*\n(.*)\n\1\s*\Z", re.DOTALL
)

# Matches a YAML frontmatter block at the start of the file. Accepts both
# Unix (\n) and Windows (\r\n) line endings - a \n-only pattern silently
# failed on Windows files and shipped the frontmatter to Claude.
FRONTMATTER_REGEX = re.compile(r"\A(---\r?\n.*?\r?\n---\r?\n)", re.DOTALL)

# Filenames and paths that almost certainly hold secrets or PII. Compressing
# them would ship raw bytes to the Anthropic API - a third-party boundary
# that developers on sensitive codebases cannot cross. The (\..+)? anchor
# (widened from caveman's (\.pub)?) catches .bak / .old / .backup variants.
#
# NOTE: This is a FILENAME-based heuristic only. It cannot catch files with
# innocent names (e.g. notes.md) that contain embedded secrets. The cli.py
# disclosure line ("file contents are sent to the Anthropic API") is the
# complementary defense - users must know the boundary is crossed.
SENSITIVE_BASENAME_REGEX = re.compile(
    r"(?ix)^("
    r"\.env(\..+)?"
    r"|\.netrc"
    r"|credentials(\..+)?"
    r"|secrets?(\..+)?"
    r"|passwords?(\..+)?"
    r"|id_(rsa|dsa|ecdsa|ed25519)(\..+)?"
    r"|authorized_keys"
    r"|known_hosts"
    r"|.*\.(pem|key|p12|pfx|crt|cer|jks|keystore|asc|gpg)"
    r")$"
)

SENSITIVE_PATH_COMPONENTS = frozenset({".ssh", ".aws", ".gnupg", ".kube", ".docker"})

SENSITIVE_NAME_TOKENS = (
    "secret", "credential", "password", "passwd",
    "apikey", "accesskey", "token", "privatekey",
    # SSH key variants after name normalization strips _/-/./space separators
    "idrsa", "iddsa", "idecdsa", "ided25519",
)


def is_sensitive_path(filepath: Path) -> bool:
    """Filename/path-based denylist for files that must never be shipped
    to a third-party API. Does NOT scan file content - see note on the
    SENSITIVE_BASENAME_REGEX declaration for the rationale and mitigation.
    """
    name = filepath.name
    if SENSITIVE_BASENAME_REGEX.match(name):
        return True
    lowered_parts = {p.lower() for p in filepath.parts}
    if lowered_parts & SENSITIVE_PATH_COMPONENTS:
        return True
    lower = re.sub(r"[_\-\s.]", "", name.lower())
    return any(tok in lower for tok in SENSITIVE_NAME_TOKENS)


def strip_llm_wrapper(text: str) -> str:
    """Strip outer ```markdown ... ``` fence when Claude wraps the entire output.

    Claude wraps ~30% of responses in a fence despite being told not to.
    Without this cleanup the compressed file would start with a literal
    ```markdown opener, breaking downstream consumers.
    """
    m = OUTER_FENCE_REGEX.match(text)
    if m:
        return m.group(2)
    return text


def extract_frontmatter(text: str) -> tuple[str, str]:
    """Split YAML frontmatter from body.

    Returns (frontmatter_block_with_trailing_newline, body). Frontmatter is
    never sent to Claude - it's re-attached byte-exact to the compressed
    body before writing. This eliminates the entire class of frontmatter-
    preservation failures and skips a validator check.
    """
    m = FRONTMATTER_REGEX.match(text)
    if m:
        return m.group(1), text[len(m.group(1)):]
    return "", text


def call_claude(prompt: str) -> str:
    """Invoke the claude CLI with prompt on stdin.

    CLI-only. Plugin users always have the CLI by definition - see
    a-claude-cli-available in the Slice 3 plan.
    """
    try:
        result = subprocess.run(
            ["claude", "--print"],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT,
            check=True,
        )
        return strip_llm_wrapper(result.stdout.strip())
    except FileNotFoundError:
        raise RuntimeError(
            "claude CLI not found on PATH. Install Claude Code "
            "(https://claude.com/claude-code) or ensure the 'claude' binary "
            "is on your shell PATH."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"claude --print timed out after {SUBPROCESS_TIMEOUT}s. "
            "Check network connectivity or Anthropic API status."
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "")[:STDERR_SCRUB_LIMIT]
        raise RuntimeError(f"claude call failed (exit {e.returncode}):\n{stderr}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error calling claude: {type(e).__name__}: {e}")


def _maybe_inject_failure(compressed: str) -> str:
    """Debug hook for deterministic retry-path testing.

    If NUTSHELL_DEBUG_INJECT_FAIL is set in env, corrupt the compressed
    output to force a specific validation failure. Enables Test 2 in the
    manual test plan. Prints a loud warning to stderr so the corruption
    mode is never silent (prevents confusion if the var is set by accident
    in a shell or CI environment).

    Values: 'url' (deletes first URL), 'heading' (rewords first heading),
    'codeblock' (mangles first code block fence).
    """
    mode = os.environ.get("NUTSHELL_DEBUG_INJECT_FAIL", "")
    if not mode:
        return compressed
    print(
        f"WARNING: NUTSHELL_DEBUG_INJECT_FAIL={mode} is active - corrupting "
        "compressed output to force a validation failure. This is a debug "
        "mode for testing the retry path; unset the env var for normal use.",
        file=sys.stderr,
    )
    if mode == "url":
        return re.sub(r"https?://[^\s)]+", "", compressed, count=1)
    if mode == "heading":
        return re.sub(
            r"^(#{1,6})\s+(.*)$",
            lambda m: f"{m.group(1)} {m.group(2)} REPHRASED",
            compressed,
            count=1,
            flags=re.MULTILINE,
        )
    if mode == "codeblock":
        return re.sub(r"^```(\w*)$", "```MANGLED", compressed, count=1, flags=re.MULTILINE)
    return compressed


def build_compress_prompt(body: str) -> str:
    # NUTSHELL-SPEAK COMPRESSION RULES. Hand-synced with:
    #   - skills/compress/SKILL.md (Compression Rules section)
    #   - skills/config-nut/SKILL.md (Compression Rules section - canonical)
    # If you edit rules here, update both SKILL.md files too.
    return f"""Compress this markdown into nutshell-speak.

STRICT RULES:
- Do NOT modify anything inside ``` code blocks
- Do NOT modify anything inside inline backticks
- Preserve ALL URLs exactly
- Preserve ALL headings exactly (count AND text; any rephrasing is an error)
- Preserve file paths, commands, and technical terms exactly
- Return ONLY the compressed markdown body. Do NOT wrap the output in a ```markdown fence or any other outer fence. Inner code blocks from the original stay as-is; do not add a new outer fence around the whole file.

COMPRESSION RULES:
- Drop articles (a, an, the), filler words, pleasantries, hedging
- Fragments OK. Short synonyms preferred.
- Technical terms exact - never simplify useEffect, B-tree, CORS
- No "I think", "I believe", "It's worth noting", "Let me explain"
- Pattern: [thing] [action] [reason]. [next step].
- Merge redundant bullets that say the same thing differently
- Keep one example where multiple examples show the same pattern

TEXT:
{body}
"""


def build_fix_prompt(original_body: str, compressed_body: str, errors: List[str]) -> str:
    errors_str = "\n".join(f"- {e}" for e in errors)
    return f"""You are fixing a nutshell-compressed markdown file. Specific validation errors were found.

CRITICAL RULES:
- DO NOT recompress or rephrase the file
- ONLY fix the listed errors - leave everything else exactly as-is
- The ORIGINAL is provided as reference only (to restore missing content)
- Preserve nutshell style in all untouched sections

ERRORS TO FIX:
{errors_str}

HOW TO FIX:
- Missing URL: find it in ORIGINAL, restore it exactly where it belongs in COMPRESSED
- Added URL: remove any URL in COMPRESSED that does not appear in ORIGINAL
- Code block mismatch: find the exact code block in ORIGINAL, restore it in COMPRESSED
- Heading mismatch: restore exact heading text and order from ORIGINAL into COMPRESSED
- Do not touch any section not mentioned in the errors

ORIGINAL (reference only):
{original_body}

COMPRESSED (fix this):
{compressed_body}

Return ONLY the fixed compressed body. No explanation, no outer fence.
"""


def compress_file(filepath: Path) -> bool:
    """Main orchestration: detect, compress, validate, retry, restore-on-failure.

    Returns True on successful compression, False if skipped (not natural
    language, backup exists, validation failed after retries).
    Raises ValueError on guard failures (symlink, size, sensitive path).
    Raises FileNotFoundError if file doesn't exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if not filepath.is_file():
        raise ValueError(f"Not a regular file: {filepath}")

    # Symlink guard: refuse a leaf symlink before .resolve() would silently
    # follow it. A .md symlinked to ~/.aws/credentials would otherwise ship
    # secrets to the API. For ancestor-directory symlinks, the sensitive-path
    # check below runs on the RESOLVED path and catches any symlink target
    # inside SENSITIVE_PATH_COMPONENTS (.ssh, .aws, .gnupg, .kube, .docker).
    #
    # Intentionally NOT checking filepath.absolute() != filepath.resolve():
    # that catches ancestor symlinks, but on macOS /tmp is itself a symlink
    # to /private/tmp, so the strict check rejects every /tmp path and
    # breaks common dev workflows. The residual gap (ancestor symlink into
    # a non-blocklisted directory holding a file with an innocent name)
    # overlaps with the inherent filename-heuristic limitation documented
    # on SENSITIVE_BASENAME_REGEX - content scanning is the real fix there.
    if filepath.is_symlink():
        target = filepath.resolve()
        raise ValueError(
            f"Refusing to compress symlink: {filepath}\n"
            f"  target: {target}\n"
            "Symlinks are not supported for safety. Copy the file if you want to compress it."
        )

    filepath = filepath.resolve()

    if filepath.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large to compress safely (max {MAX_FILE_SIZE // 1000}KB): {filepath}"
        )

    if is_sensitive_path(filepath):
        raise ValueError(
            f"Refusing to compress {filepath}: filename or path looks sensitive "
            "(credentials, keys, secrets, or known private paths like .ssh/). "
            "Compression sends file contents to the Anthropic API. "
            "Rename the file if this is a false positive."
        )

    print(f"Processing: {filepath}")

    if not should_compress(filepath):
        # Defensive: cli.py also pre-checks this. Return False so callers
        # can distinguish skip from success, but cli.py will have already
        # exited 0 before reaching this path in the normal flow.
        print("Skipping (not natural language)")
        return False

    # Byte-exact backup source. read_text(errors="replace") is used only for
    # frontmatter extraction and the compression prompt body; any non-UTF-8
    # bytes become U+FFFD there. The backup and the restore path both use
    # original_bytes so user data is preserved byte-exact.
    original_bytes = filepath.read_bytes()
    original_text = filepath.read_text(encoding="utf-8", errors="replace")

    backup_path = filepath.with_name(filepath.stem + ".original.md")

    # Skip-and-reinject frontmatter: Claude never sees the YAML header.
    frontmatter, body = extract_frontmatter(original_text)

    # Atomic backup-exists guard via O_EXCL. 'xb' raises FileExistsError if
    # the backup already exists, closing the TOCTOU race an exists() check
    # would leave open. Writing bytes (not text) preserves the source file
    # byte-for-byte including any non-UTF-8 content.
    #
    # Runs BEFORE the expensive Claude call so a pre-existing backup fails
    # fast (no wasted API call, no ~30s wall-clock burn).
    try:
        with open(backup_path, "xb") as f:
            f.write(original_bytes)
    except FileExistsError:
        print(f"Backup file already exists: {backup_path}")
        print("The original backup may contain important content.")
        print("Aborting to prevent data loss. Remove or rename the backup to proceed.")
        return False
    except OSError as e:
        # Write failed mid-flight (disk full, quota, I/O error). Remove the
        # partial backup so the next run isn't blocked by the 'xb' guard.
        backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to write backup file: {e}")

    print("Compressing with Claude...")
    compressed_body = call_claude(build_compress_prompt(body))
    compressed_body = _maybe_inject_failure(compressed_body)

    compressed = frontmatter + compressed_body
    filepath.write_text(compressed, encoding="utf-8")

    # Validate + retry loop. Wrapped in try/except to restore the original
    # byte-exact on any unhandled exception (e.g. timeout in the fix call,
    # I/O error during validation). Without this, a mid-retry exception
    # would leave the broken compressed file on disk with no automatic
    # recovery even though the backup exists.
    try:
        for attempt in range(MAX_RETRIES):
            print(f"\nValidation attempt {attempt + 1} of {MAX_RETRIES}")

            result = validate(backup_path, filepath)

            if result.is_valid:
                print("Validation passed")
                if result.warnings:
                    print("Warnings (non-blocking):")
                    for w in result.warnings:
                        print(f"  - {w}")
                break

            print("Validation failed:")
            for err in result.errors:
                print(f"  - {err}")

            if attempt == MAX_RETRIES - 1:
                # Restore via byte-exact rewrite from original_bytes.
                # write_bytes (not write_text) preserves any non-UTF-8
                # content that errors="replace" mangled when we read
                # original_text for the prompt.
                filepath.write_bytes(original_bytes)
                backup_path.unlink(missing_ok=True)
                print("Failed after retries - original restored, backup removed")
                return False

            print("Fixing with Claude...")
            compressed_body = call_claude(
                build_fix_prompt(body, compressed_body, result.errors)
            )
            compressed = frontmatter + compressed_body
            filepath.write_text(compressed, encoding="utf-8")
    except Exception:
        # Unhandled exception during retry loop. Restore original byte-exact
        # and clean up the backup so the user is never left with a broken
        # compressed file. Re-raise so caller sees the actual failure cause.
        filepath.write_bytes(original_bytes)
        backup_path.unlink(missing_ok=True)
        raise

    return True
