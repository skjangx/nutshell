#!/usr/bin/env bash
# Nutshell SessionEnd hook
# Removes session flag file and per-cwd pointer (if it still points to us).

set -euo pipefail

STDIN_JSON=$(cat)
SESSION_ID=$(echo "$STDIN_JSON" | jq -r '.session_id // empty' 2>/dev/null || true)

if [ -n "$SESSION_ID" ]; then
  rm -f "/tmp/nutshell-${SESSION_ID}" 2>/dev/null || true

  # --- Remove per-cwd pointer only if it still points to this session ---
  POINTER_DIR="${HOME}/.claude/.nutshell-pointers"
  CWD_KEY="${CLAUDE_PROJECT_DIR:-$PWD}"
  if command -v shasum &>/dev/null; then
    CWD_HASH=$(printf '%s' "$CWD_KEY" | shasum -a 256 | cut -c1-16)
  elif command -v sha256sum &>/dev/null; then
    CWD_HASH=$(printf '%s' "$CWD_KEY" | sha256sum | cut -c1-16)
  else
    CWD_HASH=$(printf '%s' "$CWD_KEY" | tr '/' '_' | tr -cd '[:alnum:]_-' | cut -c1-32)
  fi
  POINTER_FILE="${POINTER_DIR}/${CWD_HASH}"

  if [ -f "$POINTER_FILE" ]; then
    POINTED=$(cat "$POINTER_FILE" 2>/dev/null || true)
    if [ "$POINTED" = "$SESSION_ID" ]; then
      rm -f "$POINTER_FILE" 2>/dev/null || true
    fi
  fi
fi

exit 0
