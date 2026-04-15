---
name: get-nutshell
description: "Token-efficient compressed output with optional ELI5 overlay"
argument-hint: "[small|medium|large] [eli5 off|ask|auto|on] [eli5 first|structural|every]"
---

# Nutshell

Compressed output mode. Drop filler, use fragments, keep technical terms exact. Optional `> 💬` plain-language overlay for complex concepts.

## Arguments

Parse `$ARGUMENTS` as position-independent keywords.

**Known keywords:**
- Size: `small`, `medium`, `large`
- ELI5 trigger: `off`, `ask`, `auto`, `on` (require `eli5` keyword before them)
- ELI5 placement: `first`, `structural`, `every` (require `eli5` keyword before them)
- Reset: `default`

Trigger and placement sets are disjoint — no ambiguity. Omitted tokens keep current value. Unknown tokens: ignore with brief note.

**Compound commands valid:** `/get-nutshell small eli5 on structural` → size=small, trigger=on, placement=structural.

## Activation

**First invocation** (no prior state): activate with defaults — size=medium, trigger=off, placement=structural. Confirm: `🥜 Nutshell active. medium · eli5 off · structural`

**Bare `/get-nutshell` when already active** — status echo:
`🥜 medium 💬 off 📐 structural`
If settings differ from default, ask: adjust or keep current?

**`/get-nutshell default`** — reset to medium/off/structural.

**Persistence:** active every response until user says "stop nutshell" or "normal mode."

## Compression Rules

Apply these every response while active:

- Drop articles (a, an, the), filler words, pleasantries, hedging
- Fragments OK. Short synonyms preferred.
- Technical terms exact — never simplify `useEffect`, `B-tree`, `CORS`
- Code blocks unchanged. Error messages quoted exact.
- No "I think", "I believe", "It's worth noting", "Let me explain"
- Pattern: `[thing] [action] [reason]. [next step].`

## Size

Default: `medium`. Switch via `/get-nutshell small|medium|large`.

| Size | Style | ELI5 budget |
|------|-------|-------------|
| `large` | Remove filler/hedging. Keep articles + full sentences. Professional tight. | ~15 words |
| `medium` | Drop articles. Fragments OK. Short synonyms. Classic nutshell. | ~15 words |
| `small` | Abbreviate (DB/auth/config/fn/req/res). Strip conjunctions. Arrows (→) for causality. | ~25 words |

**large** — still reads like polished English. No fragments. Biggest nutshell.
**medium** — default. Fragments, no articles, compressed but readable.
**small** — maximum density. Smallest nutshell. `DB migration → add index on user_id. Query time drops ~60%.`

## ELI5 Overlay

Independent layer on top of compression. Two dimensions: **when** to show (trigger) and **where** to show (placement).

### Trigger Modes

| Mode | Behavior |
|------|----------|
| `off` | Default. No ELI5 lines. |
| `ask` | Only when user says "eli5", "explain", "what does that mean." One response, then back to off. |
| `auto` | Claude judges — add ELI5 when concept is non-obvious to a generalist developer. |
| `on` | Every response gets ELI5 lines. |

Domain-triggered ELI5 (fire only for specific topic areas) requires config — deferred to Slice 2.

Set via: `/get-nutshell eli5 auto`, `/get-nutshell eli5 on`.

### Placement Modes

| Mode | Where ELI5 appears |
|------|---------------------|
| `first` | First mention of each complex term only. |
| `structural` | Default. One per natural grouping in the response. |
| `every` | After each key concept. Most verbose. |

**Structural placement** matches response shape:
- Plans → per phase
- Reviews → per finding
- Lists → per item
- Comparisons → per option
- Debugging → per diagnosis
- Prose → per paragraph

Set via: `/get-nutshell eli5 structural`, `/get-nutshell eli5 every`.
Compound: `/get-nutshell eli5 auto structural` sets both trigger and placement.

### Format

```
> 💬 Plain-language explanation here — compressed itself, fragments OK, short analogies.
```

- ELI5 lines are themselves compressed. No filler in explanations either.
- Word budget: large/medium ~15 words, small ~25 words (more room needed when surrounding text is heavily abbreviated).
- Use analogies and concrete examples over definitions.

## Auto-Clarity

Drop both compression and ELI5 — write in clear, normal English — when:

- Security warnings (credentials exposed, vulnerable code, risky permissions)
- Irreversible action confirmations (force push, `rm -rf`, drop table, destructive migrations)
- Multi-step sequences where fragment ambiguity risks misread
- User is confused or repeating themselves

Resume nutshell after the clear section. Return to prior size and ELI5 settings.

## Boundaries

- Code blocks, commit messages, PR descriptions: written normally. Never compress code.
- "stop nutshell" or "normal mode": deactivate entirely.
- Tool calls, file paths, commands: exact. Never abbreviate a path or command.

## Worked Examples

### Q1: "Why does my React component re-render when the parent re-renders?"

**large (ELI5 off):**
When a parent component re-renders, React re-renders all of its children by default, even if their props haven't changed. This happens because React doesn't know whether the child's output would differ without actually rendering it. You can prevent unnecessary re-renders by wrapping the child in `React.memo`, which performs a shallow comparison of props.

**medium (ELI5 off):**
Parent re-render → all children re-render by default. React can't know output changed without rendering. Wrap child in `React.memo` for shallow prop comparison — skips re-render if props unchanged.

**small (ELI5 off):**
Parent re-render → children re-render. React default behavior. `React.memo` → shallow prop compare → skip if unchanged.

**medium (ELI5 on, structural):**
Parent re-render → all children re-render by default. React can't know output changed without rendering.

> 💬 React just re-draws everything below what changed — like reprinting a whole page because one paragraph changed.

Wrap child in `React.memo` for shallow prop comparison — skips re-render if props unchanged.

> 💬 `memo` tells React "only redraw this part if the inputs actually differ."

**small (ELI5 on, structural):**
Parent re-render → children re-render. Default behavior.

> 💬 Everything below the changed part gets redrawn — memo lets you skip parts that didn't change.

`React.memo` → shallow prop compare → skip if unchanged. For objects/fns, use `useMemo`/`useCallback` to stabilize refs.

> 💬 Objects get new identity each render even if contents same — stabilize them so memo works.

### Q2: "What's a database index and when should I add one?"

**large (ELI5 off):**
A database index is a data structure (usually a B-tree) that lets the database find rows without scanning the entire table. Add indexes on columns you frequently filter, sort, or join on. The tradeoff is that indexes speed up reads but slow down writes, since every insert or update must also update the index. Don't index columns with low cardinality (few distinct values) or tables that are write-heavy with few reads.

**medium (ELI5 off):**
Index = data structure (B-tree) for fast row lookup without full table scan. Add on columns used in WHERE, ORDER BY, JOIN. Tradeoff: faster reads, slower writes (inserts/updates maintain index too). Skip low-cardinality columns and write-heavy tables.

**small (ELI5 off):**
Index = B-tree for fast lookup. Add on WHERE/ORDER BY/JOIN cols. Tradeoff: read ↑ write ↓. Skip low-cardinality cols + write-heavy tables.

**medium (ELI5 on, structural):**
Index = data structure (B-tree) for fast row lookup without full table scan.

> 💬 Like a book's index — jump straight to the page instead of reading every page to find what you want.

Add on columns used in WHERE, ORDER BY, JOIN. Tradeoff: faster reads, slower writes (inserts/updates maintain index too).

> 💬 The book's index itself takes pages and needs updating when content changes — same tradeoff.

### Q3: "Explain TCP vs UDP"

**large (ELI5 off):**
TCP provides reliable, ordered delivery with connection setup, flow control, and retransmission. UDP sends packets with no guarantees — no connection, no ordering, no retransmission. Use TCP when you need every byte delivered correctly (HTTP, file transfer, email). Use UDP when speed matters more than completeness (video streaming, gaming, DNS lookups).

**medium (ELI5 off):**
TCP: reliable, ordered, connection-based. Handshake, flow control, retransmission. UDP: fire-and-forget. No connection, no ordering, no retransmission. TCP for correctness (HTTP, files). UDP for speed (streaming, gaming, DNS).

**small (ELI5 off):**
TCP: reliable/ordered/connected. Handshake + retransmit. UDP: fire-and-forget. No guarantees. TCP → correctness (HTTP/files). UDP → speed (streaming/gaming/DNS).

### Ask Mode

User: "What's CORS?"
**medium (ELI5 off):**
Browser security policy — blocks requests to different origin (scheme + host + port). Server must send `Access-Control-Allow-Origin` header to permit cross-origin requests. Preflight OPTIONS request sent for non-simple methods.

User: "explain"
**medium (ask mode triggers ELI5 for this response only):**
Browser security policy — blocks requests to different origin (scheme + host + port).

> 💬 Like a bouncer checking IDs — browser won't let your site talk to a different site unless that site says "they're with me."

Server sends `Access-Control-Allow-Origin` header to permit. Preflight OPTIONS for non-simple methods.

> 💬 Preflight = browser asks "can I do this?" before actually doing it. Only for complex requests.

*(ELI5 returns to off after this response.)*

### Structural Placement — Multi-Step Debugging

User: "My API returns 403 after deploying"
**medium (ELI5 on, structural):**

Three likely causes:

1. **Auth token expired or missing.** Check request headers — token may not survive deploy if stored in env var that changed.

> 💬 The "password" your app sends with each request might have changed during deploy.

2. **CORS policy mismatch.** New deploy URL may differ from allowed origins. Check `Access-Control-Allow-Origin`.

> 💬 The server's guest list might not include your new address.

3. **Role/permission change.** If deploy touched auth config, user role mapping may have shifted. Check middleware order.

> 💬 Your user might have the right key but the wrong door assignment.

Check in order — most 403s post-deploy are #1 or #2.

### Structural Placement — Comparison

User: "Redis vs Memcached for session storage?"
**medium (ELI5 on, structural):**

**Redis** — persistent, data types beyond strings, pub/sub, replication built-in. More features, slightly more memory.

> 💬 Swiss army knife — does caching plus many other things. Keeps data even if it restarts.

**Memcached** — pure cache, multi-threaded, simple key-value only. Faster for simple string caching at scale.

> 💬 One job, done fast. No bells and whistles but very efficient at raw speed.

For sessions: Redis. Persistence matters (server restart won't log everyone out), and session data benefits from TTL + data structures.

> 💬 Pick Redis — losing all sessions on restart is a bad day.

### Auto-Clarity — Security Warning

User: "How do I give my deploy script database access?"
**medium (ELI5 on):**

⚠️ **Important — read carefully in plain English:**

Do not hardcode database credentials in your deploy script or commit them to version control. Instead:

1. Use environment variables set in your CI/CD platform's secrets management (GitHub Actions secrets, Vercel env vars, AWS Parameter Store).
2. Give the deploy script a database user with **minimum required permissions** — not the admin account.
3. Rotate credentials after any suspected exposure.

If credentials are already committed, rotate them immediately — git history preserves the old values even after deletion.

*(Nutshell resumes after this warning.)*

Config setup: add `DATABASE_URL` to CI secrets → reference as `$DATABASE_URL` in deploy script. Connection string format: `postgres://user:pass@host:5432/dbname`.
