---
description: Consolidate session learnings into memory, repo CLAUDE.md, global CLAUDE.md, and reference files. Use this at the end of a work session, when the user says "let's wrap up", "save what we learned", "remember this for next time", or after a session with significant discoveries, mistakes, or design decisions worth preserving. Accepts an optional hint to focus on specific topics (e.g., "/consolidate focus on the Docker issues we hit").
---

Review this session and persist anything worth keeping for future conversations.

$ARGUMENTS

If the user provided a hint above, treat it as a priority lens: surface learnings related to that topic first, dig deeper into those areas of the conversation, and make sure nothing relevant to the hint is missed. Still capture other significant learnings, but weight your attention toward the hinted topics.

## Step 1: Read existing persistence files

Before proposing changes, read these to avoid duplication:
- The auto-memory `MEMORY.md` index (and any topic files that overlap with session learnings)
- The repo `CLAUDE.md` (project root), if it exists
- The global `~/.claude/CLAUDE.md`

Knowing what's already saved lets you propose only net-new information — and sets you up for the audit in Step 2b.

## Step 2: Identify and categorize learnings

Scan the session for things worth persisting. For each learning, pick exactly one destination based on scope and type:

### Auto-memory files (`memory/` directory)

Use for project-specific context that helps future conversations understand the work. Each memory file needs YAML frontmatter with `name`, `description`, and `type`. The type determines what kind of memory it is:

- **user** — role, preferences, expertise, responsibilities (e.g., "user is a data scientist focused on single-cell genomics")
- **feedback** — corrections or confirmed approaches from the user. Structure as: the rule, then **Why:** and **How to apply:** lines. Save both when the user corrects you *and* when they confirm a non-obvious approach worked.
- **project** — ongoing work context: who's doing what, why, deadlines, decisions. Convert relative dates to absolute. Structure as: fact/decision, then **Why:** and **How to apply:** lines.
- **reference** — pointers to external resources (Linear projects, Slack channels, dashboards, documentation URLs)

### Repo CLAUDE.md (project root)

For reusable patterns and conventions specific to this project:
- Architecture decisions that affect how new code should be written
- Coding conventions and testing patterns for this project
- Project-specific pitfalls (wrong function, wrong parameter, wrong order of operations)

### Global ~/.claude/CLAUDE.md

For cross-project rules — tool quirks, environment gotchas, workflow preferences confirmed across sessions. Keep entries to one line where possible.

### Reference files (~/.claude/references/)

For detailed how-to content that's too long for a CLAUDE.md one-liner but worth preserving. Detailed workarounds, multi-step procedures, specific flag combinations. CLAUDE.md gets a short pointer to the reference file.

## Step 2b: Audit CLAUDE.md for restructuring opportunities

You read the CLAUDE.md files in Step 1. Now check whether any *existing* entries would benefit from restructuring. CLAUDE.md files are loaded into every conversation, so keeping them lean and high-signal is important — detailed content should live behind pointers where it's read on demand.

### Entries to move to reference files

Look for CLAUDE.md entries that are longer than ~2 lines and contain implementation specifics (exact flags, multi-step procedures, code snippets, specific error messages). These add context weight to every conversation but only matter in narrow situations.

**Move to:** `~/.claude/references/<topic>.md`
**Replace with:** a one-line pointer, e.g., `For X details, read ~/.claude/references/x.md`

### Entries to convert to skills

Look for entries that describe a multi-step workflow or checklist — something Claude should *do*, not just *know*. Good candidates:
- Numbered steps or decision trees
- Procedures triggered by a specific context ("when rendering PDFs...", "when deploying...")
- Workflows where Claude needs to make situational decisions

**Convert to:** a skill in `~/.claude/commands/<name>.md` with YAML frontmatter
**Replace with:** a one-line pointer, e.g., `When doing X, run /x to apply the checklist.`
**Offer to use:** `/skill-creator:skill-creator` to build and test the new skill

### When to leave entries alone

Not everything needs restructuring. Leave an entry in CLAUDE.md if it's:
- Short (one line) and broadly applicable across many conversations
- A simple rule that doesn't require a decision tree or checklist
- Already a pointer to a reference file or skill

The goal is to keep each CLAUDE.md file under ~30 lines of high-signal content while making detailed guidance available on demand.

## Step 3: Present proposed changes

Show exactly what will be added or updated and where:

### Auto-memory changes
- `<filename>.md`: <what will be added/updated, including the type>
- `MEMORY.md`: <index entry>

### Repo CLAUDE.md changes
- <bullet points or diff of additions>

### Global CLAUDE.md changes
- <bullet points or diff of additions>

### Reference file changes
- `~/.claude/references/<filename>.md`: <what and why>
- Corresponding CLAUDE.md pointer line

### Restructuring proposals
- Entries to extract to reference files (with before/after)
- Entries to convert to skills (with brief description of what the skill would do)

**Wait for user approval before writing anything.**

## Step 4: Execute approved changes

After approval:
1. Create or update auto-memory topic files (with proper frontmatter)
2. Update `MEMORY.md` index (keep under 200 lines, one line per entry)
3. Edit repo CLAUDE.md if needed
4. Edit global CLAUDE.md if needed
5. Create or update reference files if needed
6. For approved skill conversions, offer to run `/skill-creator:skill-creator` to build the skill properly

## What to skip

Don't save:
- Things derivable from the code or git history (file paths, architecture, who changed what)
- Session-specific state or in-progress work details
- Information already in any of the target files
- Debugging steps or fix recipes — the fix is in the code, the context is in the commit message
- Speculative or unverified conclusions
