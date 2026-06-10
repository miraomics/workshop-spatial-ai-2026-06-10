# consolidate

A single-file Claude Code **slash command**. At the end of a work session it
reviews the conversation and persists what's worth keeping into the right place:
auto-memory files, the repo `CLAUDE.md`, the global `~/.claude/CLAUDE.md`, or
`~/.claude/references/`. It also audits your `CLAUDE.md` files for entries that
should be moved behind pointers or converted into skills.

```
consolidate/
├── consolidate.md   # the command — drop this into a commands/ directory
└── README.md
```

## Install

`consolidate.md` is a command file, so it goes in a **`commands/`** directory (a
flat `.md` becomes a command; a true *skill* would need its own folder with a
`SKILL.md`). Copy it to one of:

- **Global** — `~/.claude/commands/consolidate.md`
  Available in every project on your machine.
- **Project** — `<your-repo>/.claude/commands/consolidate.md`
  Scoped to that one repo (use this to share it with collaborators via the repo).

```
# global
cp consolidate.md ~/.claude/commands/consolidate.md

# or per-project
mkdir -p /path/to/your-repo/.claude/commands
cp consolidate.md /path/to/your-repo/.claude/commands/consolidate.md
```

Then invoke it with `/consolidate`. It also self-triggers when you say things like
"let's wrap up" or "remember this for next time". You can pass a focus hint:
`/consolidate focus on the Docker issues we hit`.

## CLAUDE.md wiring (recommended)

The command works on its own, but it's most useful when Claude knows to reach for
it and when your `CLAUDE.md` follows the conventions it writes into.

### 1. Add a pointer so Claude offers it at the right time

Add one line to a `CLAUDE.md`. Choose the scope:

- **Global** (`~/.claude/CLAUDE.md`) — applies to every project on your machine.
  Best if you want this as a default habit everywhere.
- **Project** (`<your-repo>/CLAUDE.md`) — applies only in that repo. Best if only
  some projects should use it, or you're sharing the repo with others.

Line to add:

```
- At the end of a work session, run /consolidate to persist session learnings
  into memory and CLAUDE.md files.
```

### 2. Conventions the command assumes

The command routes learnings into four destinations. They work best if you already
use:

- **Auto-memory** — a `memory/` directory with a `MEMORY.md` index, one fact per
  file with `name` / `description` / `type` frontmatter. This is a Claude Code
  memory convention; if you don't use it, the command simply won't write there.
- **`~/.claude/references/`** — a directory for long-form how-to content that
  `CLAUDE.md` points to with one-liners. Create it on first use; nothing to
  pre-configure.

Neither is required for the command to run — missing destinations are just skipped.
The repo and global `CLAUDE.md` edits work as long as those files exist (or the
command will propose creating them).
