# Nutshell

Claude Code plugin for token-efficient compressed output with optional ELI5 overlay.

## What This Is

Nutshell teaches Claude to speak concisely — dropping filler, using fragments, keeping technical terms exact — while optionally adding plain-language explanations (`> 💬` blockquotes) for complex concepts. Three intensity levels (lite/full/ultra) and four ELI5 trigger modes (off/ask/auto/on).

Activated via `/nutshell` in any Claude Code session. Not auto-injected — user must invoke per session (hooks come in Slice 2).

## File Structure

```
.claude-plugin/plugin.json   — Plugin manifest (name, version, author)
skills/nutshell/SKILL.md     — All compression rules, ELI5 overlay, examples (SINGLE SOURCE OF TRUTH)
CLAUDE.md                    — This file (contributor guide)
```

Future slices add: `hooks/hooks.json`, `presets/`, `skills/compress/`.

## Rules

- **`skills/nutshell/SKILL.md` is the single source of truth.** All compression rules, intensity levels, ELI5 logic, and examples live there. Do not duplicate rules elsewhere.
- **Don't create files the current slice doesn't need.** No empty directories, no placeholder files, no stubs for future features.
- **Worked examples in SKILL.md are high-leverage.** They're how Claude learns the style. Edit with care — bad examples train wrong behavior.
- **Auto-clarity is a safety feature.** Never weaken the rule that drops compression for security warnings, irreversible actions, or confused users.
