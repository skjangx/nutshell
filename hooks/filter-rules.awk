# Filter SKILL.md to active-only ruleset for SessionStart injection.
# Inputs (env vars): SIZE, TRIGGER, PLACEMENT
# Output: stripped SKILL.md keeping intro + rules + active rows + auto-clarity
#         + boundaries + paired discussion examples. Caveman-style footprint (~3KB).

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
/^## ELI5 Overlay/     { state = "keep"; print; next }
/^## Auto-Clarity/     { state = "keep"; print; next }
/^## Boundaries/       { state = "keep"; print; next }
/^## Worked Examples/  { state = "drop"; next }
/^## Domain Reference/ { state = "drop"; next }

# --- Subsection transitions (### headings) ---

/^### Trigger Modes/   { state = "trigger_table"; print; next }
/^### Domain Mode Rules/ { state = "drop"; next }
/^### Placement Modes/ { state = "placement_table"; print; next }
/^### Format/          { state = "keep"; print; next }
/^### Discussion\/Decision/ { state = "discussion_examples"; print; next }
/^### / {
  # Any other ### in dropped or examples sections ends the include
  if (state == "discussion_examples") { state = "drop"; next }
}

# --- Per-state line handling ---

state == "keep_intro" { print; next }
state == "keep" { print; next }
state == "discussion_examples" { print; next }

state == "size_table" {
  if (/^\| Size /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" SIZE "`")) { print; next }
  # Keep elaboration paragraphs after table only for active size
  if ($0 ~ ("^\\*\\*" SIZE "\\*\\*")) { print; next }
  next
}

state == "trigger_table" {
  if (/^\| Mode /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" TRIGGER "`")) { print; next }
  if (/^Set via:/) { print; next }
  next
}

state == "placement_table" {
  if (/^\| Mode /) { print; next }
  if (/^\|------/) { print; next }
  if ($0 ~ ("^\\| `" PLACEMENT "`")) { print; next }
  # Keep "Structural placement" elaboration only when placement=structural
  if (PLACEMENT == "structural" && /^\*\*Structural placement\*\*/) { state = "structural_elab"; print; next }
  if (/^Set via:/) { print; next }
  if (/^Compound:/) { print; next }
  next
}

state == "structural_elab" {
  print
  if (/^Set via:/ || /^Compound:/) { state = "drop" }
  next
}

# Drop everything else
{ next }
