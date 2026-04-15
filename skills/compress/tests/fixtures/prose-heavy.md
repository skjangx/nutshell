---
title: Prose Heavy Fixture
tags: [test, nutshell, compress]
---

# Prose Heavy Fixture

This fixture is used for testing the happy path of the nutshell compressor.
It contains a healthy amount of natural language prose, a few headings, and
a couple of URLs, but no code blocks. The compressor should be able to reduce
this file by a significant margin because there is plenty of redundant filler
to remove.

## Overview

The compressor should successfully reduce this file by a significant amount
because there is plenty of redundant filler to remove from the prose. It
should of course preserve all headings exactly as they appear in the input,
and it should also preserve all URLs exactly as they appear in the input.

## References

For more information about how markdown compression works in general, you
can take a look at the nutshell project repository, which lives at
https://github.com/skjangx/nutshell. The reference implementation that
nutshell adapts is caveman-compress, which lives at
https://github.com/JuliusBrussee/caveman.

## Notes

- The compressor should preserve the YAML frontmatter at the top of this
  file byte-exact, because it is extracted before compression and then
  re-attached afterwards.
- The three level-2 headings in this file must all survive compression.
- Both URLs mentioned in the references section above must appear in the
  compressed output.
- The number of bullet items is only validated as a warning, so a large
  change to the bullet count would be flagged but would not cause the
  compressor to fail the validation pass.
