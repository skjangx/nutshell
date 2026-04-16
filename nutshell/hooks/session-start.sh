#!/usr/bin/env bash
# Nutshell SessionStart hook
# Reads config, creates session flag file, injects SKILL.md via additionalContext

set -euo pipefail

# --- Capture stdin JSON (contains session_id, consumed once) ---
STDIN_JSON=$(cat)

SKILL_PATH="${CLAUDE_PLUGIN_ROOT}/skills/config-nut/SKILL.md"
SESSION_ID=$(echo "$STDIN_JSON" | jq -r '.session_id // empty' 2>/dev/null || true)
FLAG_FILE="/tmp/nutshell-${SESSION_ID:-unknown}"
GLOBAL_CONFIG="${HOME}/.claude/.nutshell.json"
PROJECT_CONFIG="${CLAUDE_PROJECT_DIR:-.}/.nutshell.json"
INSTALL_MARKER="${HOME}/.claude/.nutshell-installed"

# --- jq fallback ---
if ! command -v jq &>/dev/null; then
  touch "$FLAG_FILE"
  NOJQ_CTX="Nutshell active (minimal mode — install jq for full features). Compressed output mode: drop filler, use fragments, keep technical terms exact. Size: medium. ELI5: auto. Placement: structural. Available commands: /nutshell:config-nut (view/change settings), /nutshell:compress (compress markdown files)."
  if [ ! -f "$INSTALL_MARKER" ]; then
    mkdir -p "$(dirname "$INSTALL_MARKER")" 2>/dev/null && touch "$INSTALL_MARKER" 2>/dev/null || true
    NOJQ_CTX="${NOJQ_CTX} This is a fresh install. Welcome the user to nutshell and suggest /nutshell:config-nut setup to customize."
  fi
  # Output JSON without jq — string is known-safe (no quotes/backslashes)
  cat << FALLBACK
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${NOJQ_CTX}"
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
  *)       P_SIZE=medium; P_TRIGGER=auto; P_PLACEMENT=structural ;;
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

${SETTINGS_MSG}

Available commands: /nutshell:config-nut (view/change settings), /nutshell:compress (compress markdown files)."

# --- First-run nudge (persistent marker) ---
# Marker write is best-effort — failure degrades to no nudge, not a crash
if [ ! -f "$INSTALL_MARKER" ]; then
  mkdir -p "$(dirname "$INSTALL_MARKER")" 2>/dev/null && touch "$INSTALL_MARKER" 2>/dev/null || true
  CONTEXT="${CONTEXT}

This is a fresh install. Welcome the user to nutshell and suggest /nutshell:config-nut setup to customize their experience."
fi

jq -n --arg ctx "$CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'

exit 0
