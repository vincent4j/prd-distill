# PRD 合同索引

合同是 PRD 中必须被测试、日志或运行证据证明的硬约束。

## 规则

- 合同必须放在 `docs/prd/contracts/` 下，按模块归档，例如 `<module>.md`。
- 合同草稿放在 `docs/prd/contracts/inbox/`，由 `new-contract` 或 harvest hook 首次写入时按需创建。
- 生效合同必须关联 PRD 章节、失败处理、测试和运行证据。
- 合同条目命名规范：`MOD-<DOMAIN>-<NNN>`（例如 `MOD-FIELD-001`），与 PRD 章节 ID 对齐。

## 新增合同

1. 用 `scripts/prd_distill.py new-contract --module <name> --title <title> --contract <rule>` 创建草稿到 `inbox/`。
2. 草稿包含失败处理、测试绑定和运行证据字段后，提升为 `docs/prd/contracts/<module>.md`。
3. 在下表登记一行。

## 模块合同

| 模块 | 合同文件 | 关联 PRD |
|---|---|---|
| example | [example.md](example.md) | [../example.md](../example.md) |

> 模板占位行：把第一行替换为项目真实模块后即生效；没有真实模块时保留示例便于了解结构。
