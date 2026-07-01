# prd-distill

`prd-distill` distills chat fragments, daily plans, worklogs, and implementation diffs into module-level PRDs and executable contracts under `docs/prd/contracts/`.

It is one shared skill package with first-class support for both Codex and Claude Code.

## Install

Normal install:

```bash
python3 scripts/install.py
```

The installer detects local runtimes and installs the skill where it can be used:

- Codex only installed: installs for Codex.
- Claude Code only installed: installs for Claude Code.
- Both installed: installs for both.
- Later you install the other runtime: run the same command again to add it.

Force install for both Codex and Claude Code:

```bash
python3 scripts/install.py --all
```

Install for Codex only:

```bash
python3 scripts/install.py --codex
```

Install for Codex with an explicit skills directory:

```bash
python3 scripts/install.py --codex --codex-dir ~/.agents/skills
```

Install for Claude Code only:

```bash
python3 scripts/install.py --claude
```

Install into a Claude Code project with hooks:

```bash
python3 scripts/install.py --all --claude-project /path/to/project --install-claude-hooks
```

Claude Code hooks are optional. The core skill works without hooks; hooks add deterministic prompt harvesting and commit-time checks.

## Layout

```text
skills/prd-distill/       # skill package shared by Codex and Claude Code
scripts/install.py        # installer for both runtimes
```

## Runtime Entry Points

Codex:

```text
[$prd-distill] 整理最近 plans 到 PRD
```

Claude Code:

```text
/prd-distill 整理最近 plans 到 PRD
```

## Core Outputs

```text
docs/prd/README.md
docs/prd/contracts/
docs/prd/contracts/inbox/
docs/prd/inbox/
```
