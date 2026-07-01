# PRD Distill Document Model

## Directory Contract

```text
docs/plans/                  # daily/session fragments, usually from context-keeper
docs/worklog/                # daily/session execution record
docs/lessons-learned.md      # cross-session lessons

docs/prd/
  README.md                  # module index
  <module-prd>.md            # current effective PRD or technical PRD
  contracts/
    README.md                # contract index and rules
    <module>.md              # active module contracts
    inbox/                   # draft contract candidates
  inbox/                     # PRD fragment drafts
```

## Plans vs PRD

`plans` are time-based. Keep raw user fragments, local context, rejected proposals, temporary scope, and same-day validation criteria there.

`PRD` files are module-based. Keep only current effective behavior, stable workflows, field definitions, decision rules, exception handling, non-goals, and acceptance criteria.

Use this transformation:

```text
chat fragments -> daily plans -> module PRD
```

## Contracts vs PRD

Contracts are PRD hard constraints that must be testable or observable.

```text
PRD = complete module specification
contract = PRD constraint + source/failure rules + tests + runtime evidence
```

Draft contracts live in `docs/prd/contracts/inbox/`.
Active contracts live in `docs/prd/contracts/<module>.md`.

## docs/prd/README.md Format

Use a module index table:

```md
# PRD 模块索引

## 模块列表

| 模块 | 说明 | 主 PRD | 合同 / Invariants | 相关 plans |
|---|---|---|---|---|
| 小红书本地采集 | 本地客户端驱动真实账号采集小红书内容 | [strategy-collector-xhs.md](strategy-collector-xhs.md) | [contracts/xhs-local-collector.md](contracts/xhs-local-collector.md) | [../plans/...](../plans/...) |
```

## Module Contract Format

```md
# <模块> 合同

## 关联 PRD

- 主 PRD：../<module-prd>.md
- 技术 PRD：../<tech-prd>.md
- Invariants：../collector-invariants.md

## 合同列表

### XHS-FIELD-001：预选候选必须包含标题和有效封面

- **类型：** field
- **状态：** active
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

## Promotion Rule

Only promote a draft to active when it has:

1. A stable requirement.
2. A linked PRD section.
3. A failure rule.
4. At least one test or a clearly named pending test.
5. Runtime evidence or a log contract.
