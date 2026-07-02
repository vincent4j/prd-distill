---
name: prd-distill
description: "把需求碎片提炼成 PRD 和约束合同"
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

保持 `context-keeper` 独立。PRD Distill 不要求先安装或运行 `context-keeper`；如果项目里已经存在 `docs/plans/`、`docs/worklog/` 或 `docs/memory-keeper.md`，可以把它们作为按需输入，但没有这些文件时仍然必须能基于用户消息、`git diff`、现有 PRD / 合同和 inbox 草稿工作。

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
   - 检索近期 `docs/plans/`、`docs/worklog/`、已有模块 PRD 和相关 `git diff`，只读取与目标模块命中的内容。
   - 只有在无法推断目标模块时才询问用户。
   - 更新模块 PRD 和 `docs/prd/README.md`。
   - 运行 `scripts/prd_distill.py check --root <repo>`。

2. **整理约束合同**
   - 检查用户消息、`docs/prd/inbox/`、近期 plans/worklogs、`docs/memory-keeper.md` 的“合同候选”和已有合同中的强约束；优先检索模块名和触发词，只读命中条目。
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

如果本轮会话刚运行过 `context-keeper`，或当前变更里出现新的 `docs/plans/`、`docs/worklog/`、`docs/memory-keeper.md`，并且用户要求提交、保存并提交或推送，必须把这些文件视为 PRD Distill 输入：先用本轮模块名、触发词、文件名和合同候选检索，只读取相关内容，判断是否需要进入 PRD / 合同草稿或生效合同，再提交。不要让 `context-keeper` 生成的 plans/worklog/memory 单独提交而未检查是否需要提炼到 `docs/prd/`。

这是正常路径。不要等 `git commit` hook 失败后才开始 PRD 收尾。

成功提交后不要再生成 PRD 或合同文件。如果提交后、推送前才发现缺文档，优先 amend 同一个 commit。如果已经推送，只有在用户明确同意时才创建后续提交。

Claude Code 全局 hooks 可能会在存在 PRD / 合同草稿时阻止 `git commit`。把这个阻止视为最后兜底：在同一个 agent 回合里继续运行本 skill 收尾、stage 生成的文档，并自动重试 `git commit`，不要要求用户再次触发提交。

## 开发前模块学习与合同保护

当用户要求开发已有模块的新功能、修复模块 bug、调整模块行为，或提到当前会话不熟悉的模块概念时，先把 PRD Distill 当作模块入场检查使用：

1. **定位模块**
   - 如果存在 `docs/prd/README.md`，先用用户提到的模块名、术语、接口、页面、数据字段、受影响文件或 `git diff` 关键词检索模块索引。
   - 只读取命中的索引行和相邻上下文，用来定位模块、主 PRD 和合同文件。
   - 如果多个模块同样可能，先问用户确认；不要在没确认的情况下猜模块边界。

2. **索引与按需读取**
   - 不要默认全文加载大型 PRD、合同、worklog 或 memory 文件。
   - 根据模块索引命中结果找到主 PRD 和合同文件路径。
   - 使用关键词、受影响文件名、接口名、字段名、页面名、合同 ID 或近义词，在 PRD / 合同中检索相关章节。
   - 如果存在 `docs/memory-keeper.md`，只在 bug、回归、用户说“以前遇到过”、高风险模块或 PRD 命中不足时，用当前模块名、错误现象、字段名、接口名、文件名、模型名和合同 ID 等关键词检索相关条目；命中的内容只作为历史经验和合同候选，生效约束仍以 `docs/prd/contracts/` 为准。没有 `memory-keeper.md` 时直接跳过，不要求用户安装 context-keeper。
   - 只读取命中的章节、相邻上下文和相关合同条目。
   - 只有命中不明确、改动跨模块、触碰核心流程 / 数据字段 / 安全边界、或合同冲突时，才扩大读取范围。
   - 如果用户提到陌生概念，先在模块索引、模块 PRD 和合同中搜索该词和近义词；只有文档里找不到时才问用户解释。

3. **保护既有合同**
   - 改代码前列出本次可能受影响的生效合同或关键 PRD 规则。
   - 不要做会破坏生效合同的实现改动。
   - 如果新需求与既有 PRD / 合同冲突，停止实现，明确列出冲突点、受影响的 PRD / 合同条目、继续修改可能造成的后果，并请求用户确认是否变更规则。
   - 只有用户明确确认后，才能同步更新 PRD / 合同并继续实现。
   - 实现完成后，按本次实际影响的合同条目逐条做回归验证：合同条目绑定了测试命令的，必须运行对应测试；合同条目要求运行证据的，必须检查或补充日志、截图、接口响应等证明；如果某个受影响合同暂时无法验证，必须明确说明原因、风险和后续需要补的测试。
   - 如果合同没有测试绑定，但本次改动触碰了合同覆盖的行为，要补测试或在收尾中明确记录测试缺口。

4. **收尾证明**
   - 最终回复或提交前说明读取了哪些模块 PRD 章节 / 合同条目。
   - 说明哪些合同被本次改动影响、跑了哪些测试、还有哪些风险未闭环。

## 文档模型

使用以下边界：

- `docs/plans/`：按日期/会话保存的原始需求碎片。
- `docs/worklog/`：实际做了什么，以及为什么这么做。
- `docs/memory-keeper.md`：历史经验、触发词和合同候选；用于辅助检索，不是生效约束来源。
- `docs/prd/*.md`：当前有效的模块级产品或技术事实。
- `docs/prd/README.md`：模块索引，映射模块、PRD 和合同文档。
- `docs/prd/contracts/`：带测试和运行证据的硬约束。
- `docs/prd/contracts/inbox/`：合同候选草稿，尚未生效。

详细格式见 `references/doc-model.md`。

## 工作流

1. 发现仓库结构：
   - 检查 `docs/prd/` 是否存在，并用文件列表或索引命中结果了解结构；不要为了发现结构而全文读取。
   - `docs/plans/`、`docs/worklog/` 和 `docs/memory-keeper.md` 开发前不默认读取，只有继续上下文、提交前收尾、命中不足或用户要求时才按关键词检索。
   - 如果 PRD 结构缺失，运行 `scripts/prd_distill.py init --root <repo>`；该命令会同时安装项目入口桥接规则。
   - 如果 PRD 结构已存在但项目入口文件缺少 PRD Distill 受控块，运行 `scripts/prd_distill.py install-bridge --root <repo>`。

2. 识别模块：
   - 优先用关键词检索 `docs/prd/README.md` 里的已有模块名。
   - 否则从用户请求和受影响文件推断短模块名。
   - 只有多个模块同样合理时才询问用户。

3. 收集输入：
   - 与模块相关的近期 plans / worklogs；先检索文件名、标题和快速摘要，只在需要判断规则来源时读取相关段落。
   - 如果存在 `docs/memory-keeper.md`，只读取按模块名、触发词或当前问题命中的历史经验和合同候选；不存在则跳过。
   - 现有模块 PRD 和合同文档中的命中章节。
   - 用户纠正、被拒绝方案、强约束和实现 diff。

4. 提炼，不做原文堆砌：
   - 临时调试细节放到 worklog，不放进 PRD。
   - PRD 只保留当前有效行为。
   - 只有当旧决策能防止未来复发时，才保留已被替代的背景。

5. 更新 PRD 产物：
   - 更新或创建模块 PRD。
   - 更新 `docs/prd/README.md`，确保模块和文档路径可发现。
   - 将 `memory-keeper.md` 中成熟的合同候选提炼到 `docs/prd/contracts/inbox/` 或生效模块合同；不成熟的继续留作历史经验。

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

## 项目入口桥接规则

使用 `scripts/prd_distill.py install-bridge --root <repo>` 安装常驻桥接规则。

写入策略：

- 如果 `AGENTS.md` 和 `CLAUDE.md` 都存在，两个都写入同一段规则，保持内容一致。
- 如果只存在其中一个，只写入已有文件。
- 如果两个都不存在，默认创建两个。
- 使用 `<!-- prd-distill:start -->` 和 `<!-- prd-distill:end -->` 包住受控块；重复运行时只替换这个受控块，不要改写文件里的其他项目规则。
- 如果项目原有规则与 PRD / 合同桥接规则冲突，先向用户说明冲突并确认，不要自行覆盖原规则。

桥接规则的职责只限于告诉 Codex / Claude Code 在开发已有模块、修复模块 bug、遇到陌生模块术语时，先去 `docs/prd/` 检索模块 PRD 和合同，并在存在 `docs/memory-keeper.md` 时把它作为历史经验和合同候选的辅助检索源。不要把正式 PRD、合同正文或 memory 条目复制到 `AGENTS.md` / `CLAUDE.md`。

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
