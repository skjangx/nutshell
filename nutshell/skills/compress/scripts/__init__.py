"""Nutshell compress scripts.

Compresses natural language markdown files into nutshell-speak to save
input tokens. Preserves code blocks, URLs, headings, and YAML frontmatter
byte-exact. Sends body text to Claude via the claude --print CLI.
"""

__all__ = ["cli", "compress", "detect", "validate"]
