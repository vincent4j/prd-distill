# 项目记忆索引

## 主题摘要（按类型）

- **config：** PRD Distill 测试阶段边界；提交前收尾只核验证据；自测证据不强依赖 worklog。

---

## 时间线（最新在前）

## 2026-07-03 - PRD Distill 自测边界修正 `config`
- **模块：** prd-distill skill 工作流
- **触发词：** 提交前收尾、自测、合同测试、worklog、运行证据、pre-commit-closeout、module-entry-contract-protection
- **任务：** 修正 skill 对“测试”的阶段理解，避免 agent 在提交前重复跑当天相关合同测试。
- **关键经验：** 合同覆盖应在开发完成后的自测阶段完成；提交前只核验证据是否存在且仍适用于当前 diff。自测证据不强依赖 worklog，最终回复是最低可追溯落点。
- **合同候选：** PRD Distill 不应把提交前收尾默认解释成合同测试阶段；不应为了保存自测证据强制创建 worklog。
- **详见：** [worklog/2026-07-03-prd-distill-self-test-boundary.md](worklog/2026-07-03-prd-distill-self-test-boundary.md)

---
