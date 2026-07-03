# 2026-07-03 PRD Distill 自测边界修正

## 任务概述

本轮修正 `prd-distill` skill 对“测试”的阶段理解：用户明确指出，合同相关测试应该发生在功能开发完成后的自测阶段，而不是提交代码时再把当天改动涉及的约束合同全部测试一遍。

## 完成的工作

- 在 `skills/prd-distill/SKILL.md` 新增“测试阶段边界”说明。
- 将提交前收尾定义为 PRD / 合同 / inbox 草稿收口和证据核验，而不是默认合同测试阶段。
- 在 `references/module-entry-contract-protection.md` 中明确开发自测阶段才覆盖受影响合同。
- 在 `references/pre-commit-closeout.md` 中明确提交前默认复用已有自测证据，只在证据缺失、自测后又改代码、合同或 PRD 发生实质变化、用户明确要求时补测。
- 明确自测证据不强依赖 worklog：最终回复是最低可追溯落点；有截图、日志、接口响应或大文件证据时落到 `/tmp/<project>-*`；只有项目已有且本轮正在使用 worklog / plans / memory 时才同步记录。

## 问题和解决方案

- 问题：原 skill 文案容易让 agent 把“提交前收尾”理解成“提交前把合同测试全部重跑一遍”。
- 解决：把“开发自测覆盖合同”和“提交前证据核验 / 文档收口”拆成两个阶段，并写入主入口和两个 reference。
- 问题：最初方案里提到“自测结果要写到回复 / worklog / 运行证据”，容易被误解为必须依赖 worklog。
- 解决：改成“必须有可追溯落点，但不强制创建 worklog”，最低落点是最终回复。

## 本次对话复盘

用户先指出当前 skill 的问题：agent 把“测试”理解成提交前全量补测，导致和开发阶段自测重复。随后又指出不能把 worklog 当成自测证据的强依赖。最终收敛为：开发完成后自测覆盖本次实际影响的合同，提交前只做证据核验和 PRD / 合同收尾。

## 复盘分级

重要经验。

## 文件清单

- `skills/prd-distill/SKILL.md`
- `skills/prd-distill/references/module-entry-contract-protection.md`
- `skills/prd-distill/references/pre-commit-closeout.md`
- `docs/memory-keeper.md`

## 技术决策

- 保持 `prd-distill` 和 `context-keeper` 独立；PRD Distill 不要求项目必须有 worklog。
- 提交前阶段不默认重跑合同测试，只核验开发自测证据是否仍然覆盖当前 diff。
- 自测证据最低可追溯落点是最终回复；运行证据路径和项目记录机制按需补充。

## 下一步

- 本轮代码/文档改动已本地提交为 `ebd1fb9 Clarify PRD Distill self-test boundary`。
- 执行本次 Context Keeper 保存后，需要再提交新增的 `docs/worklog/` 和 `docs/memory-keeper.md`。
- 如果仍需同步远端，需要后续执行 `git push`；此前一次 push 被用户中断，当前仓库仍有未推送提交。

## 快速摘要（用于下次对话）

**类型：** config | 项目：prd-distill  
**完成：** 修正 PRD Distill 测试阶段边界：合同测试属于开发完成后的自测，提交前只核验证据和收口文档。  
**问题：** 原规则易导致提交前重复跑合同测试；已拆成开发自测和提交前收尾两阶段，并取消 worklog 强依赖。  
**经验：** 自测证据最低落点是最终回复；有运行证据再落 `/tmp/<project>-*`，只有项目已有且正在使用 worklog/plans/memory 时才同步记录。  
**下一步：** 如需远端同步，执行 `git push`。  
**文件：** `skills/prd-distill/SKILL.md`, `skills/prd-distill/references/module-entry-contract-protection.md`, `skills/prd-distill/references/pre-commit-closeout.md`
