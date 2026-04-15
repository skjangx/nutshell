#!/usr/bin/env bash
# Nutshell UserPromptSubmit hook
# Checks session flag file — reinforces settings if active, does nothing if deactivated

set -euo pipefail

FLAG_FILE="/tmp/nutshell-${CLAUDE_SESSION_ID:-unknown}"

# --- Flag file missing = nutshell deactivated ---
if [ ! -f "$FLAG_FILE" ]; then
  exit 0
fi

# --- Read settings from flag file ---
if command -v jq &>/dev/null; then
  SIZE=$(jq -r '.size // "medium"' "$FLAG_FILE" 2>/dev/null || echo "medium")
  TRIGGER=$(jq -r '.eli5.trigger // "off"' "$FLAG_FILE" 2>/dev/null || echo "off")
  PLACEMENT=$(jq -r '.eli5.placement // "structural"' "$FLAG_FILE" 2>/dev/null || echo "structural")
  DOMAINS=$(jq -r '.eli5.domains // [] | join(", ")' "$FLAG_FILE" 2>/dev/null || echo "")

  MSG="Nutshell active: size=${SIZE}, eli5=${TRIGGER}, placement=${PLACEMENT}"
  if [ -n "$DOMAINS" ]; then
    MSG="${MSG}, domains=[${DOMAINS}]"
  fi
  MSG="${MSG}."

  jq -n --arg msg "$MSG" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      systemMessage: $msg
    }
  }'
else
  # No jq — output hardcoded defaults
  cat << 'NOJQ'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "systemMessage": "Nutshell active: size=medium, eli5=off, placement=structural."
  }
}
NOJQ
fi

exit 0
