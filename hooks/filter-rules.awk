# Filter SKILL.md to active-only ruleset for SessionStart injection.
# Inputs (env vars): SIZE, TRIGGER, PLACEMENT
# Output: trimmed SKILL.md keeping intro + rules + active rows + auto-clarity
#         + boundaries + Q4 only. Targets ~2KB to stay under documented
#         additionalContext limit (history log entry [12] 2026-04-15).

BEGIN {
  state = "frontmatter"
  fm_count = 0
}

# --- Strip YAML frontmatter (--- ... ---) ---
state == "frontmatter" {
  if (/^---$/) {
    fm_count++
    if (fm_count == 2) { state = "keep_intro" }
  }
  next
}

# --- Section transitions (## headings) ---

/^## Arguments/        { state = "drop"; next }
/^## Activation/       { state = "drop"; next }
/^## Compression Rules/ { state = "keep"; print; next }
/^## Size$/            { state = "size_table"; print; next }
/^## Presets/          { state = "drop"; next }
/^## Config/           { state = "drop"; next }
/^## Setup Wizard/     { state = "drop"; next }
/^## ELI5 Overlay/     { state = "drop"; next }
/^## Auto-Clarity/     { state = "keep"; print; next }
/^## Boundaries/       { state = "keep"; print; next }
/^## Worked Examples/  { state = "drop"; next }
/^## Domain Reference/ { state = "drop"; next }

# --- Subsection transitions (### headings) ---

/^### Trigger Modes/   { state = "trigger_table"; print; next }
/^### Domain Mode Rules/ { state = "drop"; next }
/^### Placement Modes/ { state = "placement_table"; print; next }
/^### Format/          { state = "drop"; next }
/^### Discussion\/Decision/ { state = "drop"; next }

# --- Per-state line handling ---

# Skip the "Apply these every response while active:" preamble (wrapper says it)
state == "keep" && /^Apply these every response/ { next }

state == "keep_intro" { print; next }
state == "keep" { print; next }

state == "size_table" {
  if (/^\| Size /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" SIZE "`")) { print; next }
  next
}

state == "trigger_table" {
  if (/^\| Mode /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" TRIGGER "`")) { print; next }
  next
}

state == "placement_table" {
  if (/^\| Mode /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" PLACEMENT "`")) { print; next }
  next
}

# Drop everything else
{ next }
