# Security

## Trust boundary

Nutshell has two components with different risk profiles:

- **Hooks + config-nut skill** — local only. Read files under `~/.claude/` and `$CLAUDE_PROJECT_DIR`, inject context into your session. No network, no subprocesses. Run only when you start a Claude Code session or submit a prompt.
- **`/nutshell:compress` skill** — **crosses a trust boundary.** Reads a markdown file you pointed it at and sends the file body to the Anthropic API via the `claude --print` subprocess for compression. The result is written back in-place with a byte-exact `.original.md` backup.

If you're auditing nutshell, the `/nutshell:compress` skill is what matters.

## What `/nutshell:compress` does and doesn't do

**Does:**
- Reads the file path you pass it, plus the `.original.md` backup it writes alongside (validator reads the backup to compare against the compressed output).
- Sends the file body to the Anthropic API via `claude --print` for compression. On validation failure, sends a targeted fix prompt that embeds **both the original body and the compressed body** — the original content can leave the machine twice across a single compress run.
- Writes the compressed output back to the same path.
- Writes a `.original.md` byte-exact backup alongside the file.

**Does not:**
- Read any file outside the target file path and its `.original.md` backup.
- Execute file contents as code.
- Use `shell=True` or string interpolation in subprocess calls. The `claude` invocation uses a fixed argument list; file content is passed via stdin.
- Make network requests except to the Anthropic API via the `claude` subprocess.
- Collect telemetry.

## Guards before any API call

These run before the file body leaves your machine. If any fails, no subprocess is spawned.

- **Size limit:** 250 KB (`MAX_FILE_SIZE = 250_000`). Larger files are refused up-front. (The fix/retry prompt embeds both original and compressed body — 250 KB keeps the combined payload manageable.)
- **Symlink refusal:** leaf symlinks are refused outright. Ancestor-directory symlinks targeting a known-sensitive path are caught via the resolved-path check. **Residual gap:** an ancestor symlink into a non-sensitive directory that contains an innocuous-named file is not caught — the filename heuristic limitation (below) applies there too.
- **Sensitive-path denylist** — source of truth is `nutshell/skills/compress/scripts/compress.py`. Includes (non-exhaustive summary):
  - Private directories: `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`, `~/.docker/`
  - Credential filename patterns: `.env` (and `.env.*` suffixes), `credentials`, `secrets`, `id_rsa`/`id_dsa`/`id_ecdsa`/`id_ed25519` (and `.bak`/`.old`/`.backup`/`.pub` variants), `authorized_keys`, `known_hosts`, `.netrc`
  - Cert/key extensions: `*.pem`, `*.key`, `*.crt`, `*.cer`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.asc`, `*.gpg`
  - Name-token soft match (filename contains any of these tokens after normalizing separators): `secret`, `credential`, `password`, `passwd`, `apikey`, `accesskey`, `token`, `privatekey`, `idrsa`, `iddsa`, `idecdsa`, `ided25519`
- **Filetype guard:** only natural-language files are compressed — `.md`, `.txt`, `.markdown`, `.rst`. All common code/config extensions are refused up-front.

**Filename heuristics are not a complete defense.** If a `.md` file with an innocuous name contains secrets, do not compress it. The disclosure print before each run tells you the file is about to be sent to the Anthropic API — it is a notification, not a blocking gate.

## API boundary and auth

Nutshell does **not** read `ANTHROPIC_API_KEY` directly. The `claude` subprocess inherits the standard shell environment for CLI authentication — whatever auth you already use for `claude` is what compress uses. File contents leave your machine via that subprocess.

On subprocess failure, stderr is truncated to 100 chars (`STDERR_SCRUB_LIMIT`) before being surfaced in error messages. This reduces the risk of auth tokens or internal paths leaking into error output, but is a best-effort scrub, not a guarantee.

If you run compress, the file body is sent to the Anthropic API. There is no local-only mode.

## Debug environment variables

`NUTSHELL_DEBUG_INJECT_FAIL` and `NUTSHELL_DEBUG_INJECT_FAIL_ALWAYS` are debug-only hooks used by tests to force validation failures. If accidentally set in a shared shell or CI environment, compress will corrupt its own output and log a `WARNING:` line. Unset them in any non-test environment.

## Reporting a vulnerability

If you believe you've found a genuine security issue, email **skjangx@gmail.com** with subject `nutshell security`. Please do not open a public issue for exploitable bugs until a fix is available. This is a personal project — expect best-effort response, not an SLA.
