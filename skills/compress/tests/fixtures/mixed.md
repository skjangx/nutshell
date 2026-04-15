---
title: Mixed Content Fixture
type: test-fixture
---

# Mixed Content Fixture

This fixture intentionally mixes natural language prose with fenced code
blocks. It exercises the validator's code-block byte-identity check alongside
the heading and URL checks.

## Python Example

The following Python snippet should pass through the compressor completely
untouched, because code blocks must be preserved byte-for-byte:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("world"))
```

## Shell Example

Here is a shell command that illustrates how to invoke the compressor from
the command line:

```bash
cd skills/compress
python3 -m scripts tests/fixtures/prose-heavy.md
```

For further reading on the Anthropic messages API that the CLI uses under
the hood, refer to https://docs.anthropic.com/en/api/messages.
