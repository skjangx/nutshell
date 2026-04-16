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

  # --- Per-size directive (imperative, anchors compression behavior) ---
  case "$SIZE" in
    small)
      MSG="Nutshell active (small). Drop articles/filler/hedging. Arrows for causality. Abbreviate (DB/auth/config/fn). Fragments preferred. Code/commits/security: normal."
      ;;
    large)
      MSG="Nutshell active (large). Drop filler/hedging. Keep articles + full sentences. Code/commits/security: normal."
      ;;
    *)
      MSG="Nutshell active (medium). Drop articles/filler. Fragments OK, short synonyms. Code/commits/security: normal."
      ;;
  esac

  # --- ELI5 directive (appended based on trigger) ---
  case "$TRIGGER" in
    on)
      MSG="${MSG} ELI5 (> 💬) per concept."
      ;;
    auto)
      MSG="${MSG} ELI5 (> 💬) when concept non-obvious."
      ;;
    domain)
      if [ -n "$DOMAINS" ]; then
        MSG="${MSG} ELI5 (> 💬) for [${DOMAINS}] terms only."
      else
        MSG="${MSG} ELI5 disabled (domain mode, no domains set)."
      fi
      ;;
    ask)
      MSG="${MSG} ELI5 (> 💬) only on user request."
      ;;
    off|*)
      ;;
  esac

  jq -n --arg msg "$MSG" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: $msg
    }
  }'
else
  # No jq — output hardcoded defaults
  cat << 'NOJQ'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Nutshell active: size=medium, eli5=auto, placement=structural."
  }
}
NOJQ
fi

exit 0
