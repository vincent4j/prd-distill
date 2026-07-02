---
name: prd-distill
description: "把需求碎片、代码变更、历史经验提炼成模块 PRD 和约束合同；用于 /prd-distill、整理合同、提交前 PRD 收尾、检查实现与 PRD/合同一致性、开发前读取模块合同。"
---

# PRD Distill

把分散的用户需求、计划、工作记录、实现 diff 和历史经验，提炼成可维护的模块 PRD、`docs/prd/README.md` 索引和 `docs/prd/contracts/<module>.md` 约束合同。保持 `context-keeper` 独立；有 plans / worklogs / memory 时只按需作为输入。

## 上下文预算与读取纪律

默认使用渐进式读取：先定位模块，再读取目标段落，最后验证。不要为了“稳妥”宽扫全仓或全文加载大型文档。

1. 先检索 `docs/prd/README.md` 的命中行，用来确定模块、主 PRD 和合同文件。
2. 再检索目标 PRD / 合同中的命中章节和相邻上下文。
3. 只有命中不足、合同冲突、高风险回归或用户明确要求追溯历史时，才读取 plans / worklogs / memory。
4. 不要把源码目录、测试目录、历史文档目录和全量 docs 一起宽扫。
5. 不要默认搜索 archive / legacy / history 类目录。
6. 不要默认全文读取大型 PRD、合同、worklog 或 memory 文件。
7. 单次 discovery 输出尽量不超过 120 行；命中过多时先收窄关键词、模块名、文件名或合同 ID。
8. 优先用 `rg -n -C 2 "<关键词>" <目标文件...>` 定位，再用 `sed -n '<start>,<end>p'` 读取小段。

## 任务路由

当用户只调用 `/prd-distill`、`$prd-distill`，或只点名本 skill 但没有给出具体任务时，展示菜单并等待选择：

```text
PRD Distill - 从会话中提炼和萃取出结构化的 PRD

1. 提炼 PRD
2. 整理约束合同
3. 检查实现与文档是否一致

请选择操作（输入 1-3）：
```

- **提炼 PRD**：运行 `scripts/prd_distill.py scan --root <repo>`；按模块收窄读取；更新模块 PRD 和 `docs/prd/README.md`；运行 `scripts/prd_distill.py check --root <repo>`。需要文档边界时读 `references/doc-model.md`。
- **整理约束合同**：读取 `references/contract-rules.md`，再处理合同草稿、生效条件、测试绑定和运行证据。
- **检查一致性**：运行 `scripts/prd_distill.py check --root <repo>`；只在相关时对比生效合同、关联 PRD 章节和当前实现。
- **提交前收尾**：当用户要求提交、保存并提交、推送，或准备运行 `git commit` 时，读取 `references/pre-commit-closeout.md`。
- **开发前模块入场 / 合同保护**：当用户要求开发已有模块、修 bug、调整模块行为，或提到陌生模块概念时，读取 `references/module-entry-contract-protection.md`。
- **安装、平台差异或 hooks**：只在用户询问或需要安装/排查时读取 `references/platforms.md` 或 `references/claude-code-hooks.md`。

参考路由：

- 提交前：`references/pre-commit-closeout.md`
- 开发 / 修 bug 前：`references/module-entry-contract-protection.md`
- 合同整理：`references/contract-rules.md`
- 文档结构：`references/doc-model.md`
- 安装 / hooks：`references/platforms.md` / `references/claude-code-hooks.md`

## 核心工作流

1. **发现结构**
   - 检查 `docs/prd/` 是否存在，用文件列表或索引命中了解结构；不要为了发现结构全文读取。
   - 如果 PRD 结构缺失，运行 `scripts/prd_distill.py init --root <repo>`。
   - 如果 PRD 结构已存在但项目入口文件缺少 PRD Distill 受控块，运行 `scripts/prd_distill.py install-bridge --root <repo>`。

2. **识别模块**
   - 优先用关键词检索 `docs/prd/README.md` 里的已有模块名。
   - 否则从用户请求和受影响文件推断短模块名。
   - 多个模块同样可能时先问用户确认。

3. **收集输入**
   - 按优先级收集：用户当前明确需求、当前 `git diff --name-only` / `git diff --stat`、PRD 索引命中、目标 PRD / 合同命中段落、plans / worklogs / memory 的窄命中段落。
   - 不要从历史文件开始收集输入，除非用户要求追溯历史、当前问题是回归，或 PRD / 合同命中不足。

4. **提炼**
   - 临时调试细节放到 worklog，不放进 PRD。
   - PRD 只保留当前有效行为。
   - 只有当旧决策能防止未来复发时，才保留已被替代的背景。

5. **更新产物**
   - 更新或创建模块 PRD。
   - 更新 `docs/prd/README.md`，确保模块和文档路径可发现。
   - 将成熟合同候选提炼到模块合同；不成熟的继续留作草稿或历史经验。

6. **验证**
   - 运行 `scripts/prd_distill.py check --root <repo>`。
   - 确认生效合同关联 PRD 章节、测试和运行证据。
   - 如果实现有变更，运行项目自身相关测试。

## 硬约束

- 不要让 `context-keeper` 依赖本 skill。
- 不要把用户每句话都变成生效 PRD 变更。
- 不要正式化模糊或仍有争议的想法；先放进 inbox 或合同草稿。
- 没有测试或运行证据时，不要创建生效合同，只能标记为草稿。
- 不要把合同放在 `docs/prd` 平级；必须放在 `docs/prd/contracts/` 下。
- 优先使用模块级合同文档，例如 `docs/prd/contracts/<module>.md`，不要按类型创建全局合同文件。
- 项目特定的高风险路径、合同 ID、平台名、接口名和业务字段，不写入本通用 skill；应写入目标项目的入口规则、模块 PRD 或模块合同。
