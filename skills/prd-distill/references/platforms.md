# Platform Support

`prd-distill` must work in both Codex and Claude Code.

## Shared Core

Both runtimes use the same skill folder:

```text
prd-distill/
  SKILL.md
  scripts/
  references/
  assets/
```

Keep all core workflow instructions in `SKILL.md` and references. Do not rely on Claude Code hooks for correctness.

## Codex

Normal install:

```bash
python3 scripts/install.py
```

This auto-detects installed runtimes:

- Codex only: install Codex skill.
- Claude Code only: install Claude Code skill.
- Both: install both.
- Neither detected: preinstall both default user skill directories.
- If the user installs another runtime later, rerun the same command.

Force install for both Codex and Claude Code:

```bash
python3 scripts/install.py --all
```

Install globally for the current Codex home layout:

```bash
python3 scripts/install.py --codex
```

Install into a custom or agent-skills-standard Codex skills directory:

```bash
python3 scripts/install.py --codex --codex-dir ~/.agents/skills
```

Codex usage:

```text
[$prd-distill] 整理最近 plans 到 PRD
```

Codex has no Claude Code hook lifecycle. Use the skill workflow plus the deterministic checker:

```bash
python3 ~/.codex/skills/prd-distill/scripts/prd_distill.py check --root <repo>
```

## Claude Code

Install globally:

```bash
python3 scripts/install.py --claude
```

Install into a project:

```bash
python3 scripts/install.py --claude-project /path/to/project
```

Optional hooks:

```bash
python3 scripts/install.py --claude-project /path/to/project --install-claude-hooks
```

Claude Code usage:

```text
/prd-distill 整理最近 plans 到 PRD
```

With hooks installed:

- `UserPromptSubmit` captures strong requirement fragments into `docs/prd/inbox/`.
- `PreToolUse` observes Bash calls and blocks `git commit` if PRD/contract inbox drafts are pending.

## Compatibility Rules

- Keep hook scripts optional and Claude-specific.
- Keep `agents/openai.yaml` optional and harmless for Claude Code.
- Keep core scripts standard-library Python.
- Do not put platform-specific assumptions into the document model.
- Do not put Claude-only frontmatter in `SKILL.md` unless it is also safe for Codex to ignore.
