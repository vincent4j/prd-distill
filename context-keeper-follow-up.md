# PRD Distill 与 Context Keeper 边界及后续修改说明

本文件记录本次会话已经确认的职责边界、PRD Distill 当前实现与边界不一致的地方，以及后续修改方案。本次会话只更新这份说明，不修改 PRD Distill 的 Skill 指令、脚本、hooks、测试或功能。

## 0. 状态

本次 follow-up 已全量落地，包含两批 commit：

第一批按 follow-up 第 3 节 3.1–3.7 主体修改（边界收窄、删除 --include-history、
hook 触发词收紧、合同候选规则、提交前收尾、文档模型与路径兼容、单向写入边界）。
该 commit message 显式标注 3.1–3.7 各点的对应修改。

第二批补齐 follow-up 第 4 节验收标准与第 5 节完成定义：
- 3.2 第 3–5 条：新增 `--evidence <file>` 显式参数（可重复）。evidence 命中
  在 lookup 输出中用 `type: "evidence"` 单独标识；文件不存在或越界时
  给清晰错误；零命中不扩大搜索。
- 3.3 末尾：harvest hook 见到"之前解决过/又复现/上次怎么/上次遗漏"等
  历史词时整体不写 inbox；混合消息由 Agent 显式提炼。
- 4.5 / 5.5：新增 `ContextKeeperWriteProtectionTests`，跑遍 PRD Distill
  所有命令与 harvest hook，断言 `context-keeper/` 下任何文件指纹不变。
- 5.7：测试覆盖 4.1 独立运行、4.2 纯历史消息、混合消息抑制、有限
  evidence（含不同类型标识/零命中/越界报错）、4.4 新旧路径、4.5 单向
  写入边界。

测试：23 个全过。

未落地的需求：
- 4.6 合同状态边界：要求 PRD Distill 拒绝从"待验证/已替代" evolution
  经验直接晋升为生效合同。evolution 文件由 context-keeper 维护, 状态
  字段语义属 context-keeper, 跨 skill 验证依赖双方协议, 本轮未做。
- 5.4 独立运行测试加强：5.1 隐含覆盖（lookup 接受空项目根, scan /
  check 对未初始化项目 not_initialized）。

## 1. 已确认的职责边界

### 1.1 独立运行原则

- Context Keeper 与 PRD Distill 必须可以分别安装、分别运行。
- 未安装 Context Keeper 时，PRD Distill 仍可根据当前对话、当前代码、当前产品文档和运行证据维护 PRD 与合同。
- 未安装 PRD Distill 时，Context Keeper 仍可保存用户需求、实施计划、工作过程、历史事实、未完成事项和可复用经验。
- 两个 Skill 同时存在时允许传递证据，但不能重复搜索同一历史问题、写入同一类产物或维护两份“当前生效事实”。

### 1.2 唯一职责

| 问题或产物 | Context Keeper | PRD Distill |
|---|---|---|
| 以前发生了什么、试过什么、结果怎样 | 唯一负责 | 不做通用历史搜索 |
| 上次做到哪里、还有什么没有完成 | 唯一负责 | 不维护进度记录 |
| 原始对话、工作日志和历史证据定位 | 唯一负责 | 只消费已经定位的有限证据 |
| 用户在本次会话真实表达的需求 | 保存到 `plans/`，并保留来源与变化 | 作为当前 PRD 的输入之一 |
| 围绕已确认需求形成的实施计划 | 保存到 `plans/`，不得发散用户需求 | 不维护会话级实施计划 |
| 实际工作过程、结果、纠正和未完成事项 | 保存到 `worklogs/` 和 `memory-keeper.md` | 不写入这些文件 |
| 可复用经验、适用范围和失效关系 | 保存到 `evolution/` | 只把成熟且需要长期约束的部分正式化 |
| 当前产品应该怎样运行 | 只保存来源或历史记录，不宣称为生效规范 | 唯一负责模块 PRD |
| 当前必须长期遵守的约束 | 提供历史证据和规则候选 | 唯一负责合同草稿、生效合同和合同索引 |
| 实现是否符合当前 PRD、合同和验收标准 | 不负责 | 唯一负责 |

### 1.3 文档语义边界

- `plans/` 是会话事实：记录用户真实诉求、范围、确认、否定、待确认事项，以及围绕这些事实形成的实施计划。它不是当前生效 PRD。
- `worklogs/` 是执行事实：记录做了什么、结果怎样、用户如何反馈及证据在哪里。它不是当前生效 PRD。
- `memory-keeper.md` 是进度和历史入口，不是约束来源。
- `evolution/` 是经验层。经验可以是待验证、已验证或已替代，但不能因写入经验文件就自动成为产品合同。
- `docs/prd/` 保存当前有效的模块行为、边界、流程和验收标准。
- `docs/prd/contracts/` 保存需要长期保护、能够测试或观察的生效约束。
- 历史上发生过的事实，不自动等于现在仍然有效的需求；历史经验也不自动等于生效合同。

### 1.4 两个 Skill 的交接规则

Context Keeper 向 PRD Distill 提供证据时：

1. 先由 Context Keeper 定位与当前问题有关的少量历史记录。
2. 明确区分原文、历史摘要、用户纠正、运行证据和 Agent 推断。
3. PRD Distill 只读取已定位的相关片段，不再次宽扫全部 plans、worklogs、memory 或原始对话。
4. PRD Distill 根据当前用户要求、当前实现和运行证据，独立判断是否需要更新 PRD、创建合同草稿或修改生效合同。
5. PRD Distill 只写 `docs/prd/`、合同目录、PRD inbox 及自身入口区块，不写 Context Keeper 的文件。

典型路由：

- “上次为什么放弃这条路线？”只使用 Context Keeper。
- “现在允许使用哪些路线？”只检索 PRD Distill 的当前 PRD 与合同。
- “把上次教训变成以后必须遵守的规则。”先由 Context Keeper 提供证据，再由 PRD Distill 判断是否形成合同草稿或生效合同。
- 一条消息同时包含历史背景和明确新要求时，Context Keeper 负责历史背景；PRD Distill 只记录用户本次新增或修改的当前要求。
- 纯历史问题，例如“以前解决过吗”“这个是不是又复现了”，不得自动生成 PRD 需求草稿。

## 2. 当前现状中不符合边界的地方

以下结论来自对当前 PRD Distill 仓库的只读检查，不是推测。

### 2.1 PRD Distill 仍承担通用历史搜索

当前位置：

- `skills/prd-distill/SKILL.md` 的上下文读取规则允许直接搜索 `docs/plans/`、`docs/worklog/` 和 memory。
- `skills/prd-distill/SKILL.md` 的“收集输入”会在回归、命中不足或追溯历史时自行读取 plans、worklogs 和 memory。
- `skills/prd-distill/references/module-entry-contract-protection.md` 要求 PRD Distill 在历史信号出现时检索 `docs/memory-keeper.md`。
- `skills/prd-distill/scripts/prd_distill.py` 的 `lookup --include-history` 会自行遍历 memory、plans 和 worklog。

问题：这些行为与 Context Keeper 的“历史事实检索和原始证据定位”职责重叠。两个 Skill 同时安装时，可能分别搜索同一问题，产生不同候选和重复 Token 消耗。

### 2.2 纯历史表达会被误收集为 PRD 需求

当前位置：

- `skills/prd-distill/scripts/claude_hooks/harvest_prd_prompt.py` 把“之前解决过”和“又复现”列为需求触发词。
- `skills/prd-distill/references/claude-code-hooks.md` 把“之前解决过”描述为强需求触发词。

问题：用户只是在询问历史或报告复现时，Claude hook 也会把整条消息追加到 `docs/prd/inbox/YYYY-MM-DD-requirement-fragments.md`。这会把历史检索问题错误地变成 PRD 需求草稿。

### 2.3 历史复现被直接当作合同触发信号

当前位置：

- `skills/prd-distill/references/contract-rules.md` 把“之前解决过又复现”列为写合同草稿的强约束表达。

问题：“又复现”只能证明某个历史问题再次发生，不能单独证明用户已经提出新的长期产品约束。它可以成为调查证据或合同候选来源，但不能仅凭这句话触发合同草稿。

### 2.4 提交前收尾会强制吸收 Context Keeper 文件

当前位置：

- `skills/prd-distill/references/pre-commit-closeout.md` 规定：只要本轮运行过 Context Keeper，或出现新的 plans、worklog、memory，并且用户要求提交或推送，就“必须”把这些文件作为 PRD Distill 输入，并检查是否需要提炼。

问题：Context Keeper 保存一次进度，并不表示当前产品行为、PRD 或合同发生变化。该规则会让普通历史保存自动触发 PRD Distill 工作，增加耗时，也模糊两个 Skill 的独立边界。

### 2.5 文档模型暗示 plans 会自然转换成 PRD

当前位置：

- `skills/prd-distill/references/doc-model.md` 使用“聊天碎片 -> 每日 plans -> 模块 PRD”的单向转换表达。
- 同一文件把 plans、worklog、memory 作为 PRD Distill 能直接发现和检索的固定输入。

问题：这容易把每份 Context Keeper plan 理解成等待进入 PRD 的草稿。实际上，plan 可以只是一次性需求、被否定方案、待确认事项或会话级实施步骤，只有当前仍有效且确实需要产品规范化的部分才进入 PRD。

### 2.6 当前脚本只识别旧 Context Keeper 路径

当前位置：

- `skills/prd-distill/scripts/prd_distill.py` 的 `scan` 和历史 lookup 只识别：
  - `docs/plans/`
  - `docs/worklog/`
  - `docs/memory-keeper.md`
- Skill 和 references 也主要使用上述旧路径。

问题：本次会话已经确定 Context Keeper 新项目默认使用：

```text
context-keeper/
├── memory-keeper.md
├── plans/
├── worklogs/
└── evolution/
```

PRD Distill 当前无法识别已经由 Context Keeper 定位的新路径证据。同时，直接把新路径加入通用扫描又会继续造成职责重叠，因此不能只做路径替换。

### 2.7 README 对“历史”的表述仍可能造成职责重叠

当前位置：

- `README.md` 和 `skills/prd-distill/SKILL.md` 把“历史经验”列为 PRD Distill 的常规输入，并表达“不让后续 Agent 重新猜历史”。

问题：PRD Distill 应避免的是重新猜测“当前有效规范”，而不是承担所有历史事实的搜索。历史经验可以作为外部证据输入，但不应成为 PRD Distill 自己的通用检索职责。

### 2.8 当前符合边界、后续应保留的行为

- PRD Distill 当前没有写入 Context Keeper 的 plans、worklogs、memory 或 evolution 文件。
- PRD Distill 可以在没有 Context Keeper 的项目中初始化、扫描、检查和维护 PRD。
- `memory-keeper.md` 当前没有被当成生效合同来源。
- PRD 与合同仍集中在 `docs/prd/` 下。
- hooks 不会直接把需求碎片提升为生效 PRD 或合同。

后续修改不能破坏这些已经正确的边界。

## 3. 后续应该怎样修改

### 3.1 收窄 Skill 的总职责

修改：

- `README.md`
- `skills/prd-distill/SKILL.md`
- `skills/prd-distill/agents/openai.yaml`

要求：

- 将 PRD Distill 的核心输入表述调整为“当前用户要求、当前代码变更、当前产品文档、运行证据，以及已经定位的有限历史证据”。
- 删除 PRD Distill 自己承担通用历史搜索、原始对话追溯或项目进度恢复的暗示。
- 明确 PRD Distill 只决定当前 PRD、合同和实现一致性。
- 保持独立运行：没有 Context Keeper 时直接从当前会话、当前代码和已有产品文档工作，不把缺少历史记录当作阻断条件。

### 3.2 将历史输入改成显式、有限的证据输入

修改：

- `skills/prd-distill/scripts/prd_distill.py`
- `skills/prd-distill/SKILL.md`
- `skills/prd-distill/references/module-entry-contract-protection.md`

建议实现：

1. `lookup` 默认且始终只搜索 `docs/prd/`、当前 PRD 和合同。
2. 删除或废弃会遍历全部历史目录的 `--include-history` 行为。
3. 如需保留历史输入能力，改为显式参数，例如重复传入 `--evidence <file>`；只读取用户、当前会话或 Context Keeper 已经定位的具体文件。
4. 对 evidence 输出明确标记“历史证据”，不得与当前 PRD 或生效合同命中混在同一类型中。
5. evidence 文件不存在、不可读或超出项目边界时，给出清晰错误，不自动扩大搜索范围。
6. 不在 PRD Distill 内接入 Codex 数据库、Claude Code 会话目录或其他 Agent 的原始历史格式；原始证据定位继续由 Context Keeper 负责。

### 3.3 修复 Claude Code 需求采集 hook

修改：

- `skills/prd-distill/scripts/claude_hooks/harvest_prd_prompt.py`
- `skills/prd-distill/references/claude-code-hooks.md`
- 对应测试。

要求：

- 从 PRD 需求触发词中删除单独的“之前解决过”“又复现”等纯历史信号。
- 只有用户同时表达当前行为要求、禁止项、边界、验收条件或明确修改请求时，才写入 PRD inbox。
- “这个以前解决过吗？”、“为什么又复现了？”、“查一下上次怎么处理的”不得生成 requirement fragment。
- “这个又复现了，以后重试前必须检查幂等键”只记录“以后重试前必须检查幂等键”这一新增要求；历史背景保留为来源，不把整段历史叙述当需求。
- 如果 hook 无法可靠区分混合消息，宁可不自动收集，由 Agent 在 PRD Distill 流程中显式提炼，避免制造错误草稿。

### 3.4 修正合同候选规则

修改：

- `skills/prd-distill/references/contract-rules.md`

要求：

- 删除“之前解决过又复现”作为独立强约束触发词。
- 将复现记录定义为证据来源，而不是合同本身。
- 只有当前要求、失败处理、适用范围、测试或运行证据足够清楚时，才能形成合同草稿。
- Context Keeper 的 evolution 经验只作为候选证据；状态为待验证或已替代时不得直接提升为生效合同。

### 3.5 收窄提交前收尾

修改：

- `skills/prd-distill/references/pre-commit-closeout.md`

要求：

- 删除“运行过 Context Keeper 或出现新的 Context Keeper 文件，就必须作为 PRD Distill 输入”的规则。
- 改为：只有本轮明确改变当前产品行为、验收标准或长期约束，或者用户明确要求正式化时，才把已定位的 Context Keeper 证据交给 PRD Distill。
- 单纯保存进度、补工作日志、记录失败或新增待验证经验，不触发 PRD 更新。
- Context Keeper 文件可以与代码一起提交，但不能因为它们存在就强制产生 PRD 或合同改动。

### 3.6 更新文档模型和路径兼容

修改：

- `skills/prd-distill/references/doc-model.md`
- `skills/prd-distill/scripts/prd_distill.py` 的 `scan` 输出结构。

要求：

- 把 Context Keeper 新路径记录为可选证据位置：
  - `context-keeper/plans/`
  - `context-keeper/worklogs/`
  - `context-keeper/memory-keeper.md`
  - `context-keeper/evolution/`
- 继续识别旧路径，但只作为兼容证据位置：
  - `docs/plans/`
  - `docs/worklog/` 与 `docs/worklogs/`
  - `docs/memory-keeper.md`
- `scan` 可以报告 Context Keeper 是否存在、使用新布局还是旧布局，但不要默认枚举或读取全部历史文件。
- 删除“聊天碎片必经 plans 转换成 PRD”的暗示，改为“当前有效需求经判断后可以进入模块 PRD”。
- 明确 plans 中的一次性需求、被拒绝方案、待确认事项和会话实施步骤可以永久停留在历史层，不要求正式化。

### 3.7 保持单向写入边界

PRD Distill 后续仍只能写：

- `docs/prd/README.md`
- `docs/prd/*.md`
- `docs/prd/inbox/`
- `docs/prd/contracts/`
- PRD Distill 自己的 Agent 入口受控区块

不得写入：

- `context-keeper/plans/`
- `context-keeper/worklogs/`
- `context-keeper/memory-keeper.md`
- `context-keeper/evolution/`
- 旧版 `docs/plans/`、`docs/worklog/`、`docs/worklogs/` 或 `docs/memory-keeper.md`

如需记录“某条历史经验已正式化”，由 Context Keeper 在自己的后续保存流程中记录 PRD 或合同链接，PRD Distill 不反向修改历史文件。

## 4. 后续测试与验收标准

### 4.1 独立运行

- 未安装 Context Keeper 时，PRD Distill 的初始化、PRD lookup、合同 lookup、检查、草稿创建和提交前收尾正常运行。
- 只有 Context Keeper、没有 PRD Distill 时，Context Keeper 仍能保存 plans、worklogs、memory 和 evolution，不需要创建 `docs/prd/`。

### 4.2 历史问题不进入 PRD

以下消息不得产生 PRD inbox 草稿：

- “这个以前解决过吗？”
- “为什么又复现了？”
- “查一下上次怎么处理的。”
- “我记得之前成功过，你先找原文。”

以下消息只记录当前新增要求，不把历史叙述整体写成需求：

- “这个又复现了，以后重试前必须检查幂等键。”
- “上次遗漏了整体复盘，从现在开始整组验收后必须检查是否已经交付。”

### 4.3 有限证据交接

- PRD lookup 默认只返回当前 PRD 和合同。
- 未显式提供 evidence 时，不搜索 Context Keeper 目录。
- 显式提供一至两个 Context Keeper 文件时，只读取这些文件的有限命中片段。
- evidence 结果与当前 PRD、合同命中使用不同类型标识。
- evidence 零命中时停止，不自动扫描其他历史目录或原始对话。

### 4.4 新旧路径兼容

- 只有新 `context-keeper/` 目录的项目能报告其存在并接收明确指定的证据文件。
- 只有旧 `docs/plans/`、`docs/worklog/`、`docs/memory-keeper.md` 的项目仍能接收明确指定的证据文件。
- 新旧目录同时存在时不合并为一套当前事实，不批量读取，不自动迁移。

### 4.5 提交前边界

- 只新增 Context Keeper 工作日志时，不要求修改 PRD 或合同。
- 当前产品行为或长期约束发生变化时，PRD Distill 能根据当前需求、代码和显式历史证据更新对应 PRD 或合同。
- PRD Distill 的任何命令和 hook 都不会修改 Context Keeper 文件。

### 4.6 合同状态边界

- 待验证 evolution 经验不能直接成为生效合同。
- 已替代 evolution 经验不能作为当前约束来源。
- 已验证经验仍需结合当前用户要求、当前实现和适用范围判断，不能自动晋升。

## 5. 本次后续修改的完成定义

只有同时满足以下条件，才能认为 PRD Distill 与 Context Keeper 的边界调整完成：

1. PRD Distill 不再承担通用历史搜索或原始对话追溯。
2. 纯历史消息不会进入 PRD inbox 或合同草稿。
3. Context Keeper 文件只有在被明确定位并与当前规范有关时，才作为有限证据输入。
4. PRD Distill 继续独立运行，不要求安装 Context Keeper。
5. PRD Distill 不写入或改写任何 Context Keeper 文件。
6. 新旧 Context Keeper 路径都能作为可选证据来源，但不会被默认全量扫描。
7. 自动测试覆盖独立运行、纯历史消息、混合消息、有限 evidence、新旧路径和单向写入边界。
