# 提交前收尾

当用户要求提交、保存并提交、推送，或 agent 准备运行 `git commit` 时，必须在提交前执行 PRD Distill 收尾。

## 步骤

1. 运行 `scripts/prd_distill.py scan --root <repo>`，检查待处理的 PRD / 合同 inbox 草稿。
2. `scan` 只用于发现候选输入。scan 后必须按模块名、文件名、合同 ID 或当前变更路径收窄读取范围；不能因为 scan 发现 plans / worklogs / memory 存在，就全文读取这些文件。
3. 如果存在需求碎片、强约束，或会影响 PRD 的实现变更，先运行对应动作：
   - 用提炼 PRD 处理模块行为、工作流、字段、验收标准和决策变化。
   - 用整理约束合同处理必须被测试或运行证据证明的硬约束。
   - 在最后一次提交前使用检查实现与文档是否一致。
4. 将生成或更新的 PRD / 合同文件和代码变更一起 stage。
5. 只提交一次，让代码和 PRD / 合同收尾进入同一个 commit。

## context-keeper 输入

如果本轮会话刚运行过 `context-keeper`，或当前变更里出现新的 `docs/plans/`、`docs/worklog/`、`docs/memory-keeper.md`，并且用户要求提交、保存并提交或推送，必须把这些文件视为 PRD Distill 输入：

- 先用本轮模块名、触发词、文件名和合同候选检索。
- 只读取相关命中内容。
- 判断是否需要进入 PRD / 合同草稿或生效合同。
- 不要让 plans / worklog / memory 单独提交而未检查是否需要提炼到 `docs/prd/`。

## 提交时机

- 不要等 `git commit` hook 失败后才开始 PRD 收尾。
- 成功提交后不要再生成 PRD 或合同文件。
- 如果提交后、推送前才发现缺文档，优先 amend 同一个 commit。
- 如果已经推送，只有在用户明确同意时才创建后续提交。
- Claude Code 全局 hooks 可能会在存在 PRD / 合同草稿时阻止 `git commit`。把这个阻止视为最后兜底：在同一个 agent 回合里继续运行本 skill 收尾、stage 生成的文档，并自动重试 `git commit`。
