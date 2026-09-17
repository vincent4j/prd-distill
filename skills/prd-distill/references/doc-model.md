# PRD Distill 文档模型

## 目录约定

PRD Distill 维护的目录：

```text
docs/prd/
  README.md                  # 模块索引
  <module-prd>.md            # 当前有效的产品 PRD 或技术 PRD
  contracts/
    README.md                # 合同索引和规则
    <module>.md              # 生效模块合同
    inbox/                   # 合同候选草稿
  inbox/                     # PRD 需求碎片草稿
```

可选的 context-keeper 目录（独立于 PRD Distill）：

```text
context-keeper/              # 新版 context-keeper 记录目录
  memory-keeper.md
  plans/
  worklogs/
  evolution/
```

历史遗留路径（不再兼容读取，仅作识别用）：

```text
docs/plans/                  # 旧版每日/会话需求碎片
docs/worklog/                # 旧版每日/会话执行记录
docs/memory-keeper.md        # 旧版跨会话历史经验
```

项目根目录还可以包含入口桥接规则：

```text
AGENTS.md                    # Codex / OpenAI agents 常驻项目规则
CLAUDE.md                    # Claude Code 常驻项目规则
```

`AGENTS.md` 和 `CLAUDE.md` 不是 PRD 正文，也不是合同来源。它们只保存 PRD Distill 的受控桥接块，让新会话知道开发前要去 `docs/prd/` 查模块 PRD 和合同。

写入策略：

- 两个文件都存在：两个都写入同一段 `prd-distill` 受控块。
- 只存在一个：只写入已有文件。
- 两个都不存在：默认创建两个。
- 正式模块 PRD、合同正文、合同索引仍然只放在 `docs/prd/` 下。
- PRD Distill 不写入 `context-keeper/` 任何子目录；context-keeper 文件由 context-keeper 自身维护。

## plans 和 PRD 的边界

`plans` 是按时间组织的。这里保留原始用户碎片、本地上下文、被拒绝方案、临时范围和当天验证标准。

`PRD` 是按模块组织的。这里只保留当前有效行为、稳定工作流、字段定义、决策规则、异常处理、非目标和验收标准。

一次性需求、被拒绝方案、待确认事项和会话实施步骤可以永久停留在历史层，不要求进入模块 PRD。当前仍有效且确实需要产品规范化的部分才进入 PRD。

## memory-keeper 和 PRD 的边界

`context-keeper/memory-keeper.md`（旧版 `docs/memory-keeper.md`）是可选的历史经验索引，由 context-keeper 维护。PRD Distill 不要求安装 context-keeper；没有该文件时直接跳过 memory 检索。该文件可以包含模块、触发词、任务、关键经验和合同候选，用于帮助后续 agent 快速想起类似问题。

`memory-keeper.md` 不是生效约束来源。命中的条目只能作为排查线索和合同候选；需要长期保护的规则必须经过 PRD Distill 提炼，进入 `docs/prd/contracts/inbox/` 或生效模块合同。

PRD Distill 默认不读取 `context-keeper/` 或旧版 `docs/memory-keeper.md`；如需消费，按需从 `context-keeper/`（或用户自定义的存储目录）定位具体文件后交给 PRD Distill 处理。

`scan` 通过全项目 rglob `memory-keeper.md` 提示 context-keeper 是否存在，但不假设存储目录位置——用户 init 时通过 `--store-dir` 或配置文件指定的任意路径都能被发现。`plans` / `worklogs` / `evolution` 等子目录内容仍由 `--evidence` 显式提供。

转换关系：

```text
context-keeper/evolution 经验(已验证) -> contracts/inbox 草稿 -> 生效模块合同
```

## 约束合同和 PRD 的关系

约束合同是 PRD 中必须可测试、可观察或可用运行证据证明的硬约束。

```text
PRD = 完整模块规格
约束合同 = PRD 约束 + 来源/失败规则 + 测试 + 运行证据
```

合同草稿放在 `docs/prd/contracts/inbox/`。
生效合同放在 `docs/prd/contracts/<module>.md`。

## docs/prd/README.md 格式

使用模块索引表：

```md
# PRD 模块索引

## 模块列表

| 模块 | 说明 | 主 PRD | 合同 / 不变量 | 相关 plans |
|---|---|---|---|---|
| <模块名> | <模块职责和边界> | [<module-prd>.md](<module-prd>.md) | [contracts/<module>.md](contracts/<module>.md) | [../plans/...](../plans/...) |
```

`docs/prd/README.md` 是模块开发的入口。后续 agent 开发模块功能、修复模块 bug、或遇到陌生模块术语时，先用关键词、文件名、接口名、字段名、错误现象或合同 ID 检索这个索引，只读取命中行和相邻上下文来定位主 PRD 与合同文件，再继续局部读取相关章节 / 合同条目。不要默认全文加载 README、大型 PRD 或合同文件。

## 模块合同格式

```md
# <模块> 合同

## 关联 PRD

- 主 PRD：../<module-prd>.md
- 技术 PRD：../<tech-prd>.md
- 不变量：../<module-invariants>.md

## 合同列表

### MOD-FIELD-001：关键输入必须来自权威数据源

- **类型：** field
- **状态：** 生效
- **来源：** 用户要求 / 运行联调
- **PRD 章节：** ../<module-prd>.md#<section>
- **要求：** 进入核心流程的记录必须包含 `<required_field>`，且该字段必须来自 `<authoritative_source>`。
- **字段来源：**
  - `<required_field>`：`<authoritative_source>`
- **禁止：** 用推测值、派生临时值或非权威来源替代 `<required_field>`
- **失败处理：** 记录缺字段原因，跳过预选
- **测试：** `tests/...::test_...`
- **运行证据：** 运行日志显示缺字段记录被跳过
```

## 提升规则

草稿只有同时具备以下条件时，才能提升为生效：

1. 稳定要求。
2. 已关联 PRD 章节。
3. 有失败处理规则。
4. 至少一个测试，或明确命名的待补测试。
5. 有运行证据或日志合同。
