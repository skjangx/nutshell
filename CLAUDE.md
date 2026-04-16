# Acorn (repo) — Nutshell (plugin)

This repo is the `acorn` marketplace — currently hosts one plugin, `nutshell`. Designed to host more (nut/tree-themed plugins) as they ship.

## What Nutshell does

Teaches Claude to speak concisely — dropping filler, using fragments, keeping technical terms exact — while optionally adding plain-language explanations (`> 💬` blockquotes) for complex concepts. Three sizes (small/medium/large), five ELI5 trigger modes (off/ask/auto/domain/on), and four presets (dense/compact/teach/explain).

Auto-activated via SessionStart hook when plugin is installed. `/nutshell:config-nut` is available for settings changes and status.

## File Structure

```
.claude-plugin/marketplace.json         — Marketplace manifest (name: acorn, lists plugins)
nutshell/                               — The nutshell plugin
├── .claude-plugin/plugin.json          — Plugin manifest (name, version, author)
├── hooks/hooks.json                    — Hook manifest (SessionStart, UserPromptSubmit)
├── hooks/session-start.sh              — Reads config, injects SKILL.md via additionalContext
├── hooks/prompt-submit.sh              — Reinforces settings each prompt via systemMessage
├── skills/config-nut/SKILL.md          — All compression rules, ELI5 overlay, examples (SINGLE SOURCE OF TRUTH)
├── skills/compress/SKILL.md            — /nutshell:compress skill — compress .md prose, saves ~46% file size
├── skills/compress/scripts/            — Python package: detect, compress, validate, retry loop
└── skills/compress/tests/fixtures/     — Committed fixtures for reproducible testing
README.md                               — User-facing docs (currently nutshell; move to nutshell/README.md when 2nd plugin lands)
SECURITY.md                             — Security disclosure
CHANGELOG.md                            — Release notes
CLAUDE.md                               — This file (contributor guide)
LICENSE                                 — MIT
```

## Rules

- **`nutshell/skills/config-nut/SKILL.md` is the single source of truth.** All compression rules, size levels, ELI5 logic, and examples live there. Do not duplicate rules elsewhere.
- **Don't create files the current slice doesn't need.** No empty directories, no placeholder files, no stubs for future features.
- **Worked examples in SKILL.md are high-leverage.** They're how Claude learns the style. Edit with care — bad examples train wrong behavior.
- **Auto-clarity is a safety feature.** Never weaken the rule that drops compression for security warnings, irreversible actions, or confused users.
- **Hook scripts must use `$CLAUDE_PLUGIN_ROOT`** — never hardcode paths.
