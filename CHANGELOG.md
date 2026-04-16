# Changelog

## 0.1.0 — 2026-04-16

Initial release.

- Compression rules and `/nutshell:config-nut` skill (SKILL.md is the single source of truth)
- `/nutshell:compress` skill for compressing existing markdown files in-place (~46% typical savings)
- 4-turn setup wizard (`/nutshell:config-nut setup`) — preset or custom, global or per-project scope
- SessionStart and UserPromptSubmit hooks that activate compression per session and reinforce settings per prompt
- 4 presets: `dense`, `compact`, `teach` (default), `explain`
- Optional ELI5 overlay with 5 trigger modes (`off`, `ask`, `auto`, `domain`, `on`) and 3 placement modes (`first`, `structural`, `every`)
- First-run welcome nudge (once per user, tracked via `~/.claude/.nutshell-installed` marker)
