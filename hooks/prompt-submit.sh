#!/usr/bin/env bash
# Nutshell UserPromptSubmit hook
# Checks session flag file — reinforces settings if active, does nothing if deactivated

set -euo pipefail

# --- Capture stdin JSON (contains session_id, consumed once) ---
STDIN_JSON=$(cat)
SESSION_ID=$(echo "$STDIN_JSON" | jq -r '.session_id // empty' 2>/dev/null || true)
FLAG_FILE="/tmp/nutshell-${SESSION_ID:-unknown}"

# --- Flag file missing = nutshell deactivated ---
if [ ! -f "$FLAG_FILE" ]; then
  exit 0
fi

# --- Read settings from flag file ---
if command -v jq &>/dev/null; then
  SIZE=$(jq -r '.size // "medium"' "$FLAG_FILE" 2>/dev/null || echo "medium")
  TRIGGER=$(jq -r '.eli5.trigger // "auto"' "$FLAG_FILE" 2>/dev/null || echo "auto")
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
    "systemMessage": "Nutshell active: size=medium, eli5=auto, placement=structural."
  }
}
NOJQ
fi

exit 0
