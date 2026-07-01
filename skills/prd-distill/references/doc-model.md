# PRD Distill 文档模型

## 目录约定

```text
docs/plans/                  # 每日/会话需求碎片，通常来自 context-keeper
docs/worklog/                # 每日/会话执行记录
docs/lessons-learned.md      # 跨会话经验教训

docs/prd/
  README.md                  # 模块索引
  <module-prd>.md            # 当前有效的产品 PRD 或技术 PRD
  contracts/
    README.md                # 合同索引和规则
    <module>.md              # 生效模块合同
    inbox/                   # 合同候选草稿
  inbox/                     # PRD 需求碎片草稿
```

## plans 和 PRD 的边界

`plans` 是按时间组织的。这里保留原始用户碎片、本地上下文、被拒绝方案、临时范围和当天验证标准。

`PRD` 是按模块组织的。这里只保留当前有效行为、稳定工作流、字段定义、决策规则、异常处理、非目标和验收标准。

转换关系：

```text
聊天碎片 -> 每日 plans -> 模块 PRD
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
| 小红书本地采集 | 本地客户端驱动真实账号采集小红书内容 | [strategy-collector-xhs.md](strategy-collector-xhs.md) | [contracts/xhs-local-collector.md](contracts/xhs-local-collector.md) | [../plans/...](../plans/...) |
```

## 模块合同格式

```md
# <模块> 合同

## 关联 PRD

- 主 PRD：../<module-prd>.md
- 技术 PRD：../<tech-prd>.md
- 不变量：../collector-invariants.md

## 合同列表

### XHS-FIELD-001：预选候选必须包含标题和有效封面

- **类型：** field
- **状态：** 生效
- **来源：** 用户要求 / 真实账号联调
- **PRD 章节：** ../strategy-collector-xhs.md#专业模型预选输入合同
- **要求：** 进入专业模型预选的候选必须包含 `title` 和有效 `cover_url`。
- **字段来源：**
  - `title`：列表 DOM 当前卡片标题
  - `cover_url`：列表 DOM 当前卡片主封面图
- **禁止：** LLM 生成 `cover_url`；用 `cover_text` 替代 `cover_url`
- **失败处理：** 记录缺字段原因，跳过预选
- **测试：** `tests/...::test_...`
- **运行证据：** 运行日志显示缺封面候选被跳过
```

## 提升规则

草稿只有同时具备以下条件时，才能提升为生效：

1. 稳定要求。
2. 已关联 PRD 章节。
3. 有失败处理规则。
4. 至少一个测试，或明确命名的待补测试。
5. 有运行证据或日志合同。
