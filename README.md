```
                ,;;;,
               ;;;;;;;
              ;;;;;;;;;
              `;;;;;;;'
         /\ /\  `;;;;
         (o_o)   ;;;
         _\v/_   ;;
        / 🥜  \  ;
        \_____/ ;
        /     \
```

# 🐿️🥜 Nutshell

**Token-efficient Claude Code. Compress prose, keep the signal. Drop a nut where it helps.**

---

## What it is

*"In a nutshell"* — that's the whole idea.

Nutshell is a Claude Code plugin that teaches Claude to speak concisely — dropping filler, using fragments, keeping technical terms exact — while (optionally) adding plain-language blockquotes when jargon shows up.

Four presets: **dense** (max compression), **compact** (dense + always-on ELI5), **teach** (default — medium + auto ELI5), **explain** (full ELI5 everywhere). One command to switch.

Code, commands, and tool calls are never compressed. Compression drops automatically around security warnings, irreversible actions, and confused users.

---

## Demos

### 🐿️ Debugging — `dense`

> **You:** My jest test fails with `Cannot find module './utils'`

**Normal Claude:**

> There are a few common reasons why Jest might fail to resolve a module path like this. First, make sure the file actually exists at the expected location. Second, check your `tsconfig.json` paths and your Jest `moduleNameMapper` configuration, since Jest doesn't automatically honor TypeScript path aliases...

**Nutshell (dense):**

> Jest ignores `tsconfig` paths. Mirror them in `jest.config.js` under `moduleNameMapper`.
> Check actual path: `jest --showConfig | grep moduleNameMapper`.

---

### 🥜 Concept — `teach` (default)

> **You:** What's a React Server Component?

**Nutshell (teach):**

> Renders on server, ships HTML — not JS. Zero client bundle cost. Direct DB/filesystem access. No hooks, no state, no events. For interactivity, mark a child `"use client"`.
>
> > 💬 **ELI5:** regular React components ship their code to the browser, which runs them to build the page. Server Components skip that — the server builds the HTML, browser just displays it. Faster loads, smaller downloads, but they can't be interactive. When you need a button or form, you mix in a `"use client"` component.

---

### 🌰 Learning — `explain`

> **You:** Walk me through adding a database index

**Nutshell (explain):**

> 1. Find the slow query: `EXPLAIN ANALYZE SELECT …`
>    > 💬 **ELI5:** runs the query and reports what Postgres actually did — which tables it scanned, row counts, time per step. Tells you whether an index would help.
>
> 2. Pick column(s) matching your `WHERE`, `JOIN`, or `ORDER BY`.
>    > 💬 **ELI5:** indexes only help queries that filter or sort on the indexed column. Indexing `email` doesn't speed up `WHERE last_name = '…'`.
>
> 3. Create it:
>    ```sql
>    CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
>    ```
>    > 💬 **ELI5:** `CONCURRENTLY` avoids locking the table while the index builds. Takes longer, but no downtime on a big table.

---

## Presets

| Preset | Size | ELI5 | Placement | When |
|--------|------|------|-----------|------|
| `dense` | small | off | structural | Max token savings, no explanations |
| `compact` | small | on | structural | Dense + always explain |
| `teach` | medium | auto | structural | **Default.** Smart explanations when needed |
| `explain` | large | on | every | Learning mode — explain everywhere |

Switch with: `/nutshell:config-nut preset dense` (or `compact`/`teach`/`explain`).
Fine-grain: `/nutshell:config-nut small eli5 auto structural`. See `/nutshell:config-nut` for the full surface.

---

## Install

**Recommended** (GitHub, two commands):

```bash
claude plugin marketplace add skjangx/nutshell
claude plugin install nutshell@nutshell
```

**Dev / local testing** (session-only, not a persistent install):

```bash
git clone https://github.com/skjangx/nutshell
claude --plugin-dir ./nutshell
```

Restart your Claude Code session after installing — hooks load on session start.

**First run:** Claude will welcome you once and point to `/nutshell:config-nut setup` for a guided 4-turn wizard (preset or custom → custom dials if needed → scope → confirm).

---

## Uninstall

```bash
claude plugin uninstall nutshell@nutshell
```

To fully reset (also removes the first-run welcome marker so a future reinstall re-greets you):

```bash
rm ~/.claude/.nutshell-installed
rm ~/.claude/.nutshell.json          # if you ran setup globally
```

---

## Bonus: `/nutshell:compress`

Crush existing markdown files in-place. Prose-heavy docs typically shrink ~46% with technical accuracy preserved.

```bash
/nutshell:compress path/to/doc.md
```

Code blocks, commands, and frontmatter are passed through untouched. Files over 250 KB, symlinks, and anything under a sensitive path (`.env`, `secrets/`, etc.) are refused. Backup written alongside. See [`SECURITY.md`](./SECURITY.md) for the full trust boundary.

---

## Troubleshooting

- **Nutshell isn't activating.** Check the hook fired: `cat /tmp/nutshell-$SESSION_ID` should exist after session start. Restart your session if you just installed.
- **Output conflicts with another style plugin.** Nutshell and other output-rewriting plugins can fight. Disable the other, or narrow nutshell to per-project scope.
- **`.nutshell.json` showed up in a commit.** Add it to your repo's `.gitignore` — config is for you, not the project.

---

## Scope

Claude Code only for v0.1.0. No Cursor, Windsurf, or Codex support yet.

## License

MIT. See [`LICENSE`](./LICENSE).
