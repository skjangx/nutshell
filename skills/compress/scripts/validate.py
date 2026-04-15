#!/usr/bin/env python3
"""Validator for nutshell-compressed markdown files.

Five checks:
  - Heading integrity (count AND text/order must match)     error
  - Code blocks byte-identical                              error
  - URL set bidirectional match (no losses, no additions)   error
  - File path set match                                     warning
  - Bullet count change >15%                                warning

Frontmatter is NOT validated. The compressor extracts frontmatter before
calling Claude and re-attaches it byte-exact to the output, so Claude
never sees or modifies it.
"""

import re
from pathlib import Path

URL_REGEX = re.compile(r"https?://[^\s)]+")
FENCE_OPEN_REGEX = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
BULLET_REGEX = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
PATH_REGEX = re.compile(r"(?:\./|\.\./|/|[A-Za-z]:\\)[\w\-/\\\.]+|[\w\-\.]+[/\\][\w\-/\\\.]+")


class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []

    def add_error(self, msg):
        self.is_valid = False
        self.errors.append(msg)

    def add_warning(self, msg):
        self.warnings.append(msg)


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_headings(text):
    return [(level, title.strip()) for level, title in HEADING_REGEX.findall(text)]


def extract_code_blocks(text):
    """Line-based fenced code block extractor.

    Handles ``` and ~~~ fences with variable length. Closing fence must use
    the same char and be at least as long as opening (CommonMark). Supports
    nested fences (outer 4-backtick block wrapping inner 3-backtick content).
    """
    blocks = []
    lines = text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        m = FENCE_OPEN_REGEX.match(lines[i])
        if not m:
            i += 1
            continue
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        open_line = lines[i]
        block_lines = [open_line]
        i += 1
        closed = False
        while i < n:
            close_m = FENCE_OPEN_REGEX.match(lines[i])
            if (
                close_m
                and close_m.group(2)[0] == fence_char
                and len(close_m.group(2)) >= fence_len
                and close_m.group(3).strip() == ""
            ):
                block_lines.append(lines[i])
                closed = True
                i += 1
                break
            block_lines.append(lines[i])
            i += 1
        if closed:
            blocks.append("\n".join(block_lines))
    return blocks


def extract_urls(text):
    return set(URL_REGEX.findall(text))


def extract_paths(text):
    return set(PATH_REGEX.findall(text))


def count_bullets(text):
    return len(BULLET_REGEX.findall(text))


def validate_heading_integrity(orig, comp, result):
    """Heading count AND text/order must match. Any difference is an error.

    Both checks fire independently so the fix prompt receives all relevant
    information. If counts differ AND text differs, the fix prompt learns
    both - otherwise Claude would only know about the count and have to
    guess which heading text changed.
    """
    h1 = extract_headings(orig)
    h2 = extract_headings(comp)

    count_diff = len(h1) != len(h2)
    order_diff = h1 != h2

    if count_diff:
        result.add_error(f"Heading count mismatch: {len(h1)} vs {len(h2)}")

    if order_diff and not count_diff:
        # Same count, text or order changed - report per-position diffs.
        diffs = [f"'{a[1]}' -> '{b[1]}'" for a, b in zip(h1, h2) if a != b]
        result.add_error(f"Heading text/order changed: {'; '.join(diffs[:3])}")
    elif order_diff and count_diff:
        # Count differs AND content differs - report missing/added sets so
        # the fix prompt knows which headings to restore or remove.
        orig_titles = [t for _, t in h1]
        comp_titles = [t for _, t in h2]
        missing = [t for t in orig_titles if t not in comp_titles]
        added = [t for t in comp_titles if t not in orig_titles]
        if missing or added:
            details = []
            if missing:
                details.append(f"missing={missing[:3]}")
            if added:
                details.append(f"added={added[:3]}")
            result.add_error(f"Heading content changed ({'; '.join(details)})")


def validate_code_blocks(orig, comp, result):
    c1 = extract_code_blocks(orig)
    c2 = extract_code_blocks(comp)

    if c1 != c2:
        result.add_error("Code blocks not preserved exactly")


def validate_urls(orig, comp, result):
    """Bidirectional: all original URLs must appear AND no new URLs may be added."""
    u1 = extract_urls(orig)
    u2 = extract_urls(comp)

    if u1 != u2:
        result.add_error(f"URL mismatch: lost={u1 - u2}, added={u2 - u1}")


def validate_paths(orig, comp, result):
    p1 = extract_paths(orig)
    p2 = extract_paths(comp)

    if p1 != p2:
        result.add_warning(f"Path mismatch: lost={p1 - p2}, added={p2 - p1}")


def validate_bullets(orig, comp, result):
    b1 = count_bullets(orig)
    b2 = count_bullets(comp)

    if b1 == 0:
        return

    diff = abs(b1 - b2) / b1

    if diff > 0.15:
        result.add_warning(f"Bullet count changed too much: {b1} -> {b2}")


def validate(original_path: Path, compressed_path: Path) -> ValidationResult:
    result = ValidationResult()

    orig = read_file(original_path)
    comp = read_file(compressed_path)

    validate_heading_integrity(orig, comp, result)
    validate_code_blocks(orig, comp, result)
    validate_urls(orig, comp, result)
    validate_paths(orig, comp, result)
    validate_bullets(orig, comp, result)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python validate.py <original> <compressed>")
        sys.exit(1)

    orig = Path(sys.argv[1]).resolve()
    comp = Path(sys.argv[2]).resolve()

    res = validate(orig, comp)

    print(f"\nValid: {res.is_valid}")

    if res.errors:
        print("\nErrors:")
        for e in res.errors:
            print(f"  - {e}")

    if res.warnings:
        print("\nWarnings:")
        for w in res.warnings:
            print(f"  - {w}")
