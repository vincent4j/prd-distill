---
name: prd-distill
description: Distill fragmented chat requirements, daily plans, worklogs, implementation diffs, and user corrections into module-level PRDs, docs/prd module indexes, and executable contracts under docs/prd/contracts. Use when the user invokes /prd-distill or $prd-distill, asks to 整理 PRD, 同步 plans 到 PRD, 提炼需求, 归并需求, 检查 PRD 和实现一致性, 生成/更新合同, or when starting implementation after many requirement fragments or strong constraints like 必须/不能/每个/之前解决过又复现.
---

# PRD Distill

## Purpose

Turn scattered requirement fragments into durable module specifications:

```text
chat fragments / docs/plans / docs/worklog / git diff
  -> module PRD
  -> docs/prd/README.md module index
  -> docs/prd/contracts/<module>.md executable contracts
```

Keep `context-keeper` independent. This skill may read its `docs/plans/`, `docs/worklog/`, and `docs/lessons-learned.md` outputs when present, but must also work without them.

Support both Codex and Claude Code:

- Codex: install this folder as `~/.codex/skills/prd-distill`, or another Codex skills directory such as `~/.agents/skills/prd-distill`.
- Claude Code: install this folder as `~/.claude/skills/prd-distill` or `<project>/.claude/skills/prd-distill`.
- Claude Code hooks are optional automation. Do not require hooks for the core workflow.

For installation and platform differences, read `references/platforms.md`.

## Interactive Menu

When the user invokes `/prd-distill`, `$prd-distill`, or names this skill without a specific task, show this menu and wait for the user's choice:

```text
PRD Distill - 从会话中提炼和萃取出结构化的 PRD

1. 提炼 PRD
2. 整理需求合同
3. 检查实现与文档是否一致

请选择操作（输入 1-3）：
```

Handle choices as follows:

1. **提炼 PRD**
   - Run `scripts/prd_distill.py scan --root <repo>` to discover pending fragments.
   - Inspect recent `docs/plans/`, `docs/worklog/`, existing module PRDs, and relevant `git diff`.
   - Ask for the target module only if it cannot be inferred.
   - Update the module PRD and `docs/prd/README.md`.
   - Run `scripts/prd_distill.py check --root <repo>`.

2. **整理需求合同**
   - Inspect strong constraints in user messages, `docs/prd/inbox/`, recent plans/worklogs, and existing contracts.
   - Create draft contracts with `scripts/prd_distill.py new-contract ...` when the constraint is not yet stable.
   - Promote to active module contract only when the requirement, failure handling, test binding, and runtime/log evidence are clear.

3. **检查实现与文档是否一致**
   - Run `scripts/prd_distill.py check --root <repo>`.
   - Compare active contracts with linked PRD sections and current implementation when relevant.
   - Report missing PRD links, missing tests, missing runtime evidence, stale inbox drafts, and implementation drift.

## Document Model

Use this boundary:

- `docs/plans/`: time-based raw fragments for a day or session.
- `docs/worklog/`: what happened and why.
- `docs/prd/*.md`: current module-level product or technical truth.
- `docs/prd/README.md`: module index mapping modules to PRDs and contract docs.
- `docs/prd/contracts/`: hard PRD constraints with tests and runtime evidence.
- `docs/prd/contracts/inbox/`: draft contract candidates, not yet active.

For detailed formats, read `references/doc-model.md`.

## Workflow

1. Discover repository structure:
   - Inspect `docs/prd/`, `docs/plans/`, `docs/worklog/`, and recent `git diff`.
   - If the PRD structure is missing, run `scripts/prd_distill.py init --root <repo>`.

2. Identify the module:
   - Prefer existing module names from `docs/prd/README.md`.
   - Otherwise infer a short module name from the request and affected files.
   - Ask only if several modules are equally plausible.

3. Collect inputs:
   - Recent plans/worklogs relevant to the module.
   - Existing module PRD and contract docs.
   - User corrections, rejected approaches, strong constraints, and implementation diff.

4. Distill, do not dump:
   - Move transient debugging details to worklogs, not PRDs.
   - Keep PRDs as current effective behavior.
   - Preserve superseded decisions only when they prevent future regressions.

5. Update PRD artifacts:
   - Update or create the module PRD.
   - Update `docs/prd/README.md` so the module and document paths are discoverable.
   - Add contract candidates or active contracts under `docs/prd/contracts/`.

6. Validate:
   - Run `scripts/prd_distill.py check --root <repo>`.
   - Ensure active contracts cite PRD section, tests, and runtime evidence.
   - Run project-specific tests if implementation was changed.

## Contracts

Treat contracts as the executable constraint layer of PRDs, not as a separate system.

Write a **draft contract** when the user gives strong constraints:

```text
必须 / 不能 / 每个 / 一定 / 不能靠猜 / 之前解决过又复现 / 为什么会没有
```

Promote a draft to an **active contract** only when at least one is true:

- The root cause is confirmed.
- The behavior is stable enough to become a long-term rule.
- A regression would be expensive or high-risk.

An active contract must include:

- ID and title
- Type: field, decision, runtime, quality, safety, API, or UX
- Linked PRD section
- Requirement
- Field/source contract if relevant
- Failure handling
- Test binding
- Runtime/log evidence
- Status

Use `scripts/prd_distill.py new-contract ...` to create draft contracts.

## Claude Code Hooks

This skill includes optional Claude Code hook scripts for stricter automation:

- `scripts/claude_hooks/harvest_prd_prompt.py`: capture strong user requirement fragments into `docs/prd/inbox/`.
- `scripts/claude_hooks/guard_prd_commit.py`: block `git commit` when PRD or contract inbox drafts are pending.

Read `references/claude-code-hooks.md` before installing hooks.

Codex does not use Claude Code hooks. In Codex sessions, run the skill workflow directly and use `scripts/prd_distill.py check --root <repo>` before committing.

## Guardrails

- Do not make `context-keeper` depend on this skill.
- Do not turn every user sentence into an active PRD change.
- Do not formalize ambiguous or disputed ideas; put them in inbox.
- Do not create contracts without tests or runtime evidence unless marked `draft`.
- Do not place contracts beside `docs/prd`; keep them under `docs/prd/contracts/`.
- Prefer module-based contract docs such as `docs/prd/contracts/xhs-local-collector.md` over type-based global files.
