---
name: compress
description: "Compress .md prose to save ~46% file size. Preserves code blocks, URLs, headings, and YAML frontmatter byte-exact. Overwrites original; backup saved as FILE.original.md."
argument-hint: "<filepath>"
---

# Nutshell Compress

Compress natural language markdown files (CLAUDE.md, notes, memory files, docs) into nutshell-speak. Shaves ~46% on file size so they're cheaper to feed to Claude in future sessions. Preserves code, URLs, headings, and frontmatter byte-exact.

## Trigger

`/nutshell:compress <filepath>` or natural language like "compress this file" / "nutshell this doc".

## API Disclosure

File contents are sent to the Anthropic API (via `claude --print`) for compression. Only the file body is sent — YAML frontmatter is extracted locally and re-attached byte-exact to the output. The skill refuses to compress files whose names or paths look sensitive (see Boundaries below), but filename heuristics can't catch every case. If a file contains secrets with an innocent filename, do not compress it.

## Process

1. Locate the `scripts/` directory adjacent to this SKILL.md. The scripts package lives next to this file on disk.

2. Run:

   ```
   cd "<directory_containing_this_SKILL.md>" && python3 -m scripts "<absolute_filepath>"
   ```

   Paths are quoted to handle spaces and special characters. The filepath argument must be absolute (resolve it from the user's input before running).

3. Report the result to the user — success (with byte-reduction %, file paths), skip (not natural language), refusal (sensitive path / symlink / too large / backup exists), or failure (validation failed after retries, original restored from memory).

The scripts handle detection, compression, validation, retry with targeted fix, and byte-exact restore-on-failure. Claude Code just runs the command and surfaces the output.

## Compression Rules

The `build_compress_prompt()` function in `scripts/compress.py` embeds these rules as the literal prompt sent to Claude. The rules are **hand-synced across three places**: this SKILL.md, `scripts/compress.py`, and the canonical human-readable copy in `skills/config-nut/SKILL.md` (Compression Rules section). If you change them in one, update the other two.

### Preserve EXACTLY (never modify)

- Code blocks (fenced ``` and indented) — byte-identical required, validator enforces
- Inline code (`` `backtick content` ``)
- URLs and links (markdown links, bare URLs) — validator enforces bidirectionally (no losses, no hallucinated additions)
- File paths (`/src/...`, `./config.yaml`)
- Commands (`npm install`, `git commit`)
- Technical terms (library names, API names, protocols) — `useEffect`, `B-tree`, `CORS`
- Proper nouns, dates, version numbers, environment variables (`$HOME`, `NODE_ENV`)

### Preserve STRUCTURE

- All markdown headings — count AND text must match exactly (any rephrasing is a validator error)
- Bullet hierarchy (keep nesting level)
- Numbered lists (keep numbering)
- Tables (compress cell text, keep shape)
- YAML frontmatter — extracted before compression and re-attached byte-exact; Claude never sees it

### Compress

- Drop articles (a, an, the), filler words, pleasantries, hedging
- Fragments OK. Short synonyms preferred.
- No "I think", "I believe", "It's worth noting", "Let me explain"
- Pattern: `[thing] [action] [reason]. [next step].`
- Merge redundant bullets that say the same thing differently
- Keep one example where multiple show the same pattern

### Critical Rules

- Anything inside ``` ... ``` must be copied EXACTLY — no comment removal, no reordering, no shortening
- Inline code must be preserved EXACTLY
- If the file has mixed content (prose + code), only compress the prose
- If unsure whether something is code or prose, leave it unchanged

## Pattern

**Prose paragraph:**

Original:
> You should always make sure to run the test suite before pushing any changes to the main branch. This is important because it helps catch bugs early and prevents broken builds from being deployed to production.

Compressed:
> Run tests before push to main. Catches bugs early, prevents broken prod deploys.

**Bullet list:**

Original:
- The application uses a microservices architecture with the following components.
- The API gateway handles all incoming requests and routes them to the appropriate service.
- The authentication service is responsible for managing user sessions and JWT tokens.

Compressed:
- Microservices architecture.
- API gateway routes incoming requests to services.
- Auth service manages user sessions + JWT tokens.

## Boundaries

- Only compress `.md`, `.txt`, and extensionless natural-language files (detector classifies by extension first, content heuristics for extensionless)
- Never modify code/config: `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.toml`, `.env`, `.lock`, `.sh`, `.sql`, `.css`, `.html`, etc.
- Skip `.original.md` backup files (would double-compress)
- Refuse symlinks (leaf OR ancestor) — prevents exfiltration attacks
- Refuse sensitive filenames (`credentials.md`, `secrets.md`, `id_rsa*`, `*.pem`, `*.key`, etc.) and files under `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.kube/`, `~/.docker/`
- Refuse files over 250KB (retry prompt embeds original + compressed; larger files risk subprocess failure)
- Refuse if backup `<stem>.original.md` already exists (prevents clobbering a prior backup on second run — rename or delete the backup to proceed)

## Output Invariants

- Original file is overwritten with compressed content on success
- Backup saved as `<stem>.original.md` in the same directory, byte-exact from the source (preserves any non-UTF-8 bytes)
- Backup file is gitignored via repo-wide `*.original.md` rule (Slice 1)
- On validation failure after retries, the original is restored byte-exact from memory and the backup is removed — no orphan files
- Exit codes: `0` success or skip (not natural language), `1` usage/runtime error, `2` compression failed after retries
