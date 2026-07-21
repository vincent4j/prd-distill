---
name: prd-distill
description: "把需求碎片、代码变更、历史经验提炼成模块 PRD 和约束合同；用于 /prd-distill、整理合同、提交前 PRD 收尾、检查实现与 PRD/合同一致性、开发前读取模块合同。"
---

# PRD Distill

把分散的用户需求、计划、工作记录、实现 diff 和历史经验，提炼成可维护的模块 PRD、`docs/prd/README.md` 索引和 `docs/prd/contracts/<module>.md` 约束合同。保持 `context-keeper` 独立；有 plans / worklogs / memory 时只按需作为输入。

## 上下文预算与读取纪律

把 `rg` 当索引器，不当正文读取器。默认按三阶段读取：先定位文件，再收窄命中，最后小段读取。

1. **结构定位**
   - 优先运行 `scripts/prd_distill.py lookup --root <repo> --query '<模块|关键词|合同ID>'`，用限量 JSON 确定模块、主 PRD 和合同文件。
   - 如果脚本不可用，再检索 `docs/prd/README.md` 的命中行：`rg -n -m 20 '<模块|关键词|合同ID>' docs/prd/README.md`。
   - 如果入口不清，先用 `rg --files docs/prd docs/plans docs/worklog | rg '<模块|关键词|合同ID>'` 或 `rg -l '<关键词>' <高概率目录...>` 找候选文件，不直接打印正文。
2. **命中收窄**
   - 只在候选 PRD / 合同 / 少量历史文件里搜索：`rg -n -m 8 -C 1 '<关键词>' <目标文件...>`。
   - 如果命中超过 20 行或超过 3 个文件，先用模块名、文件名、接口名、字段名、错误码或合同 ID 再收窄。
3. **小段读取**
   - 用 `sed -n '<start>,<end>p' <file>` 读取命中相邻段落；单次读取通常不超过 80 行，discovery 总输出尽量不超过 120 行。
   - 大型 PRD、合同、worklog、memory、日志、JSON 和浏览器状态都不全文读取；原始证据先落盘到 `/tmp/<project>-*`，对话里只输出关键统计、路径和少量摘录。
4. **历史与 diff 输入**
   - 只有命中不足、合同冲突、高风险回归或用户明确要求追溯历史时，才读取 plans / worklogs / memory。
   - 代码变更输入先用 `git diff --name-only` 和 `git diff --stat`；需要语义判断时才对目标文件运行 scoped diff。
5. **禁止的默认形态**
   - 不默认运行 `rg '<关键词>' .`、`rg --hidden '<关键词>' .`，或把源码目录、测试目录、历史文档目录和全量 docs 一起宽扫。
   - 不默认搜索 archive / legacy / history 类目录。
   - 不用 `cat`、大范围 `tail` 或未过滤日志把大型文件正文灌进上下文。

## 合同验收门

开发已有模块、修 bug、改行为、UI / 数据 / API / 采集链路，或用户提到“之前约定 / PRD / 合同 / 需求”时，先检索生效合同。无命中只说 `未命中生效合同` 并继续；有命中时，编码前输出最多 5 条：

```text
受影响合同：
- <合同ID>：命中原因；证据：<测试/API/日志/截图/DOM/页面检查>
```

只为判断读取必要字段，不在对话里抄合同正文。命中超过 5 条时先按本轮改动收窄，仍无法收窄再请用户确认优先级。细节见 `references/module-entry-contract-protection.md`。

## 测试阶段边界

PRD Distill 里的“测试”默认发生在功能开发完成后的自测阶段，不默认挪到提交前补跑。

- **开发自测阶段**：实现完成后只按受影响合同验证；测试绑定不等于完成，运行证据才是验收依据。
- **UI / UX 合同**：触发 UI、视觉、交互或响应式时，必须保存截图、DOM 或页面检查证据到 `/tmp/<project>-*`。
- **提交前收尾阶段**：提交、保存并提交或推送前，主要做 PRD / 合同 / inbox 草稿收口和一致性检查；默认复用开发自测阶段已经产生的证据，不重复跑合同测试。
- **需要补测的例外**：没有可追溯自测证据、自测后又改了受影响代码、合同/PRD 发生实质变化、或用户明确要求提交前完整验证时，才在提交前补跑相关测试。
- **证据落点**：自测完成后，在最终回复中说明受影响合同、验证方式和结果；如有日志、截图、接口响应或大文件证据，先落盘到 `/tmp/<project>-*` 并在回复里给路径。只有项目已有且本轮正在使用 worklog / plans / memory 时，才同步写入这些记录；不要为了本 skill 强行创建 worklog。

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
- **检查一致性**：先运行 `scripts/prd_distill.py lookup --root <repo> --query '<模块|关键词|合同ID>'` 定位相关 PRD / 合同，再运行 `scripts/prd_distill.py check --root <repo>`；只在相关时对比生效合同、关联 PRD 章节和当前实现。`check` 返回 `not_initialized` 表示项目尚未启用 PRD Distill，不是结构 warning 或完成证明；返回 `initialized` 时再判断 errors / warnings。脚本只验证结构、草稿和生效合同必备字段；语义一致性必须结合当前实现、运行证据、PRD 和合同判断。
- **提交前收尾**：当用户要求提交、保存并提交、推送，或准备运行 `git commit` 时，读取 `references/pre-commit-closeout.md`；提交前默认检查证据与文档收口，不把它理解成重新跑一遍合同测试。
- **开发前模块入场 / 合同保护**：当用户要求开发已有模块、修 bug、调整模块行为，或提到陌生模块概念时，读取 `references/module-entry-contract-protection.md`。有合同命中才输出清单；无命中用一行说明。
- **安装、平台差异或 hooks**：只在用户询问或需要安装/排查时读取 `references/platforms.md` 或 `references/claude-code-hooks.md`。

一次只读取当前路由必需的 reference；不要为了预热同时读取全部 references。若任务跨路由，先完成主路由，再按缺口加载下一个 reference。

参考路由：

- 提交前：`references/pre-commit-closeout.md`
- 开发 / 修 bug 前：`references/module-entry-contract-protection.md`
- 合同整理：`references/contract-rules.md`
- 文档结构：`references/doc-model.md`
- 安装 / hooks：`references/platforms.md` / `references/claude-code-hooks.md`

## 核心工作流

1. **发现结构**
   - 检查 `docs/prd/` 是否存在，用文件列表或索引命中了解结构；不要为了发现结构全文读取。
   - 有关键词时优先用 `scripts/prd_distill.py lookup --root <repo> --query '<关键词>'` 做限量定位。
   - 如果用户要在当前项目启用 PRD Distill，而 PRD 结构缺失，运行 `scripts/prd_distill.py init --root <repo>`；其他任务遇到 `not_initialized` 时标记为不适用并继续，不强行初始化。
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
   - `status: not_initialized` 只表示项目尚未采用 `docs/prd/`；需要启用时先 `init`，否则把 PRD / 合同结构标为不适用，不报告缺索引 warning。
   - 检查一致性或提交前收尾时，只对受本轮改动影响的事实面标记 `无需修改 / 已更新并验证 / 待处理 / 范围外 / 不适用`；没有生效合同命中时仍要报告适用的 PRD、运行证据和入口桥接状态，但不强凑无关事实面。
   - 有受影响合同时只输出最小验收矩阵；无命中合同则不输出矩阵。`未验证` 不是完成态；UI / UX 无页面证据则标为未验证或部分通过。

```text
合同验收：
- <合同ID>：通过/部分通过/未验证/不适用；证据：<测试/API/DB/日志/截图/DOM/手动说明>
```

## 硬约束

- 不要让 `context-keeper` 依赖本 skill。
- 不要把用户每句话都变成生效 PRD 变更。
- 不要正式化模糊或仍有争议的想法；先放进 inbox 或合同草稿。
- 没有测试或运行证据时，不要创建生效合同，只能标记为草稿。
- 生效合同是完成标准；有命中则最终逐项报告状态，没有匹配证据时不得宣称完成。
- 不要把合同放在 `docs/prd` 平级；必须放在 `docs/prd/contracts/` 下。
- 优先使用模块级合同文档，例如 `docs/prd/contracts/<module>.md`，不要按类型创建全局合同文件。
- 项目特定的高风险路径、合同 ID、平台名、接口名和业务字段，不写入本通用 skill；应写入目标项目的入口规则、模块 PRD 或模块合同。
- 只维护 PRD、合同、索引及 PRD Distill 受控入口桥接块；不要把一致性检查扩展为项目通用 README、Agent 记忆、规则文件或工作区清场。发现范围外残留只报告，不删除。
