#!/usr/bin/env bash
# Nutshell SessionStart hook
# Reads config, creates session flag file, injects SKILL.md via additionalContext

set -euo pipefail

SKILL_PATH="${CLAUDE_PLUGIN_ROOT}/skills/config-nut/SKILL.md"
FLAG_FILE="/tmp/nutshell-${CLAUDE_SESSION_ID:-unknown}"
GLOBAL_CONFIG="${HOME}/.claude/.nutshell.json"
PROJECT_CONFIG="${CLAUDE_PROJECT_DIR:-.}/.nutshell.json"

# --- jq fallback ---
if ! command -v jq &>/dev/null; then
  touch "$FLAG_FILE"
  cat << 'FALLBACK'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Nutshell active (minimal mode — install jq for full features). Compressed output mode: drop filler, use fragments, keep technical terms exact. Size: medium. ELI5: off. Placement: structural."
  }
}
FALLBACK
  exit 0
fi

# --- Read and merge configs ---
G_CFG=$(cat "$GLOBAL_CONFIG" 2>/dev/null || echo '{}')
P_CFG=$(cat "$PROJECT_CONFIG" 2>/dev/null || echo '{}')
MERGED=$(echo "$G_CFG" "$P_CFG" | jq -s '.[0] * .[1]')

# --- Resolve preset defaults ---
PRESET=$(echo "$MERGED" | jq -r '.preset // empty')
case "$PRESET" in
  dense)   P_SIZE=small;  P_TRIGGER=off;  P_PLACEMENT=structural ;;
  compact) P_SIZE=small;  P_TRIGGER=on;   P_PLACEMENT=structural ;;
  teach)   P_SIZE=medium; P_TRIGGER=auto; P_PLACEMENT=structural ;;
  explain) P_SIZE=large;  P_TRIGGER=on;   P_PLACEMENT=every ;;
  *)       P_SIZE=medium; P_TRIGGER=off;  P_PLACEMENT=structural ;;
esac

# --- Extract settings (explicit fields override preset defaults) ---
SIZE=$(echo "$MERGED" | jq -r --arg def "$P_SIZE" '.size // $def')
TRIGGER=$(echo "$MERGED" | jq -r --arg def "$P_TRIGGER" '.eli5.trigger // $def')
PLACEMENT=$(echo "$MERGED" | jq -r --arg def "$P_PLACEMENT" '.eli5.placement // $def')
DOMAINS=$(echo "$MERGED" | jq -r '.eli5.domains // [] | join(", ")')

# --- Create session flag file with settings ---
echo "$MERGED" > "$FLAG_FILE"

# --- Build settings summary ---
SETTINGS_MSG="Nutshell is active. Current settings: size=${SIZE}, eli5 trigger=${TRIGGER}, placement=${PLACEMENT}"
if [ -n "$DOMAINS" ]; then
  SETTINGS_MSG="${SETTINGS_MSG}, domains=[${DOMAINS}]"
fi
SETTINGS_MSG="${SETTINGS_MSG}."

# --- Brief directive + tell model to read SKILL.md on first response ---
# additionalContext has a ~2KB limit — can't inject full SKILL.md.
# Model reads the file on first response, getting full rules into context.

SKILL_ABS_PATH=$(cd "$(dirname "$SKILL_PATH")" && pwd)/$(basename "$SKILL_PATH")

CONTEXT="NUTSHELL COMPRESSED OUTPUT MODE IS ACTIVE.

On your very first response this session, silently read the full rules from:
${SKILL_ABS_PATH}

Apply those rules to EVERY response. Key points until you read the file:
- Drop articles, filler, hedging. Fragments OK. Technical terms exact.
- Code blocks and tool calls: never compress.
- \"stop nutshell\" or \"normal mode\" to deactivate.

${SETTINGS_MSG}"

jq -n --arg ctx "$CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'

exit 0
