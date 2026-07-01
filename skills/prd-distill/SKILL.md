---
name: prd-distill
description: "把聊天里的片段需求、每日 plans、工作日志、代码变更和用户纠正，提炼成模块级 PRD、docs/prd 模块索引，以及 docs/prd/contracts 下的约束合同。用户调用 /prd-distill 或 $prd-distill，要求整理 PRD、同步 plans 到 PRD、提炼需求、归并需求、检查 PRD 和实现一致性、生成/更新合同，或在需求密集工作后准备 git commit / 保存并提交时使用。"
---

# PRD Distill

## 目标

把分散的需求碎片沉淀成可长期维护的模块规格：

```text
聊天碎片 / docs/plans / docs/worklog / git diff
  -> 模块 PRD
  -> docs/prd/README.md 模块索引
  -> docs/prd/contracts/<module>.md 约束合同
```

保持 `context-keeper` 独立。这个 skill 可以读取 `context-keeper` 生成的 `docs/plans/`、`docs/worklog/` 和 `docs/lessons-learned.md`，但不能依赖它才能工作。

同时支持 Codex 和 Claude Code：

- Codex：安装到 `~/.codex/skills/prd-distill`，或其他 Codex skills 目录，例如 `~/.agents/skills/prd-distill`。
- Claude Code：安装到 `~/.claude/skills/prd-distill`。
- Claude Code hooks 由安装器默认安装为全局 hooks，位置是 `~/.claude/settings.json` 和 `~/.claude/hooks/prd-distill/`；核心流程不能依赖 hooks。

安装方式和平台差异见 `references/platforms.md`。

## 主动触发菜单

当用户调用 `/prd-distill`、`$prd-distill`，或只点名这个 skill 但没有给出具体任务时，展示菜单并等待用户选择：

```text
PRD Distill - 从会话中提炼和萃取出结构化的 PRD

1. 提炼 PRD
2. 整理约束合同
3. 检查实现与文档是否一致

请选择操作（输入 1-3）：
```

按以下规则处理选择：

1. **提炼 PRD**
   - 运行 `scripts/prd_distill.py scan --root <repo>`，发现待处理碎片。
   - 检查近期 `docs/plans/`、`docs/worklog/`、已有模块 PRD 和相关 `git diff`。
   - 只有在无法推断目标模块时才询问用户。
   - 更新模块 PRD 和 `docs/prd/README.md`。
   - 运行 `scripts/prd_distill.py check --root <repo>`。

2. **整理约束合同**
   - 检查用户消息、`docs/prd/inbox/`、近期 plans/worklogs 和已有合同中的强约束。
   - 当约束还不稳定时，用 `scripts/prd_distill.py new-contract ...` 创建草稿合同。
   - 只有当要求、失败处理、测试绑定、运行/日志证据都清楚时，才提升为生效模块合同。

3. **检查实现与文档是否一致**
   - 运行 `scripts/prd_distill.py check --root <repo>`。
   - 在相关时，对比生效合同、关联 PRD 章节和当前实现。
   - 报告缺失的 PRD 链接、缺失测试、缺失运行证据、过期 inbox 草稿，以及实现和文档漂移。

## 提交前收尾

当用户要求提交、保存并提交、推送，或 agent 准备运行 `git commit` 时，必须在提交前执行 PRD Distill 收尾：

1. 运行 `scripts/prd_distill.py scan --root <repo>`，检查待处理的 PRD / 合同 inbox 草稿。
2. 如果存在需求碎片、强约束，或会影响 PRD 的实现变更，先运行对应菜单动作：
   - 用 **提炼 PRD** 处理模块行为、工作流、字段、验收标准和决策变化。
   - 用 **整理约束合同** 处理必须被测试或运行证据证明的硬约束。
   - 在最后一次提交前使用 **检查实现与文档是否一致**。
3. 将生成或更新的 PRD / 合同文件和代码变更一起 stage。
4. 只提交一次，让代码和 PRD / 合同收尾进入同一个 commit。

这是正常路径。不要等 `git commit` hook 失败后才开始 PRD 收尾。

成功提交后不要再生成 PRD 或合同文件。如果提交后、推送前才发现缺文档，优先 amend 同一个 commit。如果已经推送，只有在用户明确同意时才创建后续提交。

Claude Code 全局 hooks 可能会在存在 PRD / 合同草稿时阻止 `git commit`。把这个阻止视为最后兜底：在同一个 agent 回合里继续运行本 skill 收尾、stage 生成的文档，并自动重试 `git commit`，不要要求用户再次触发提交。

## 文档模型

使用以下边界：

- `docs/plans/`：按日期/会话保存的原始需求碎片。
- `docs/worklog/`：实际做了什么，以及为什么这么做。
- `docs/prd/*.md`：当前有效的模块级产品或技术事实。
- `docs/prd/README.md`：模块索引，映射模块、PRD 和合同文档。
- `docs/prd/contracts/`：带测试和运行证据的硬约束。
- `docs/prd/contracts/inbox/`：合同候选草稿，尚未生效。

详细格式见 `references/doc-model.md`。

## 工作流

1. 发现仓库结构：
   - 检查 `docs/prd/`、`docs/plans/`、`docs/worklog/` 和近期 `git diff`。
   - 如果 PRD 结构缺失，运行 `scripts/prd_distill.py init --root <repo>`。

2. 识别模块：
   - 优先使用 `docs/prd/README.md` 里的已有模块名。
   - 否则从用户请求和受影响文件推断短模块名。
   - 只有多个模块同样合理时才询问用户。

3. 收集输入：
   - 与模块相关的近期 plans / worklogs。
   - 现有模块 PRD 和合同文档。
   - 用户纠正、被拒绝方案、强约束和实现 diff。

4. 提炼，不做原文堆砌：
   - 临时调试细节放到 worklog，不放进 PRD。
   - PRD 只保留当前有效行为。
   - 只有当旧决策能防止未来复发时，才保留已被替代的背景。

5. 更新 PRD 产物：
   - 更新或创建模块 PRD。
   - 更新 `docs/prd/README.md`，确保模块和文档路径可发现。
   - 在 `docs/prd/contracts/` 下添加合同候选或生效合同。

6. 验证：
   - 运行 `scripts/prd_distill.py check --root <repo>`。
   - 确认生效合同关联 PRD 章节、测试和运行证据。
   - 如果实现有变更，运行项目自身相关测试。

## 约束合同

把合同视为 PRD 的可执行约束层，而不是独立系统。

当用户给出强约束时，先写 **草稿合同**：

```text
必须 / 不能 / 每个 / 一定 / 不能靠猜 / 之前解决过又复现 / 为什么会没有
```

只有满足至少一个条件时，才提升为 **生效合同**：

- 根因已经确认。
- 行为足够稳定，可以成为长期规则。
- 回归代价高或风险高。

生效合同必须包含：

- ID 和标题
- 类型：field、decision、runtime、quality、safety、API 或 UX
- 关联 PRD 章节
- 要求
- 相关字段/来源合同
- 失败处理
- 测试绑定
- 运行/日志证据
- 状态

使用 `scripts/prd_distill.py new-contract ...` 创建草稿合同。

## Claude Code Hooks

这个 skill 包含 Claude Code hook 脚本。使用本仓库安装器时，hooks 默认安装为全局 hooks：

- `scripts/claude_hooks/harvest_prd_prompt.py`：把强需求片段收集到 `docs/prd/inbox/`。
- `scripts/claude_hooks/guard_prd_commit.py`：当 PRD 或合同 inbox 草稿待处理时，阻止 `git commit`。

hooks 安装位置是 `~/.claude/settings.json` 和 `~/.claude/hooks/prd-distill/`。如需跳过，安装时传 `--no-claude-hooks`。详细行为见 `references/claude-code-hooks.md`。

Codex 没有 Claude Code 这种 prompt/tool 生命周期 hooks。在 Codex 会话中，直接运行 skill 工作流，并在提交前运行 `scripts/prd_distill.py check --root <repo>`；不要把 Codex 描述成支持等价自动 hook。

## 约束

- 不要让 `context-keeper` 依赖这个 skill。
- 不要把用户每句话都变成生效 PRD 变更。
- 不要正式化模糊或仍有争议的想法；先放进 inbox。
- 没有测试或运行证据时，不要创建生效合同，只能标记为草稿。
- 不要把合同放在 `docs/prd` 平级；必须放在 `docs/prd/contracts/` 下。
- 优先使用模块级合同文档，例如 `docs/prd/contracts/xhs-local-collector.md`，不要按类型创建全局合同文件。
