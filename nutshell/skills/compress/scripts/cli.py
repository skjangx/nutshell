#!/usr/bin/env python3
"""Nutshell compress CLI.

Usage:
    python3 -m scripts <filepath>

Exit codes:
    0 - success, or file skipped (not natural language)
    1 - usage error, file not found, or runtime error
    2 - compression failed after retries (original restored)
"""

import sys
from pathlib import Path

from .compress import compress_file
from .detect import detect_file_type, should_compress


def print_usage():
    print("Usage: python3 -m scripts <filepath>")


def main():
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    if not filepath.is_file():
        print(f"Error: Not a file: {filepath}")
        sys.exit(1)

    # Classify + pre-check. Matches caveman's pattern: skip non-natural-language
    # files with exit code 0 (a legitimate no-op, not a failure). Without this
    # pre-check, compress_file()'s False return for skip would conflate with
    # actual compression failures at sys.exit(2) below.
    file_type = detect_file_type(filepath)
    print(f"Detected: {file_type}")

    if not should_compress(filepath):
        print("Skipping: file is not natural language (code/config)")
        sys.exit(0)

    try:
        original_size = filepath.stat().st_size
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        success = compress_file(filepath)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

    if not success:
        # compress_file returned False for a non-skip reason - backup exists,
        # or validation failed after retries. User-facing message was already
        # printed inside compress_file.
        sys.exit(2)

    abs_path = filepath.resolve()
    compressed_size = abs_path.stat().st_size
    backup_path = abs_path.with_name(abs_path.stem + ".original.md")
    reduction_pct = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

    print()
    print(f"Compressed via Anthropic API - {reduction_pct:.1f}% smaller")
    print(f"  original   ({original_size:,} bytes): {backup_path}")
    print(f"  compressed ({compressed_size:,} bytes): {abs_path}")


if __name__ == "__main__":
    main()
