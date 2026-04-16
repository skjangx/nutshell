---
title: Code Heavy Fixture
type: test-fixture
---

# Code Heavy Fixture

Mostly code blocks. Small reduction expected because there is very little
natural language to compress.

## Bash

```bash
#!/bin/bash
set -euo pipefail

echo "Starting backup..."
tar -czf backup.tar.gz ./src
echo "Done."
```

## Python

```python
import json
import sys

def parse_input(path):
    with open(path) as f:
        return json.load(f)

if __name__ == "__main__":
    data = parse_input(sys.argv[1])
    print(json.dumps(data, indent=2))
```

## Config

```yaml
version: 1
services:
  compress:
    image: python:3.11
    command: python3 -m scripts
```

See also: https://example.com/docs
