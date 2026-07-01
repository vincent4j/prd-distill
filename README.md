# prd-distill

PRD Distill 是一个面向 Codex 和 Claude Code 的 skill，用来把对话里的零散需求、纠正、临时决策和代码变更，提炼成结构化的模块 PRD，并把必须长期遵守的硬约束沉淀为 `docs/prd/contracts/` 下的约束合同。

## 设计理念

和 AI 一起开发时，真正重要的产品规则经常不是一次性写进 PRD 的，而是在连续对话里一点点冒出来：

- “这个字段必须每次都传。”
- “之前解决过的问题不能再复现。”
- “这不是重试问题，要找根因。”
- “提交前要把文档和代码一起收尾。”

如果这些要求只留在聊天里，后面的 agent 很容易忘；如果直接把整段聊天塞进文档，PRD 又会变成流水账。

PRD Distill 的目标是做中间那层“蒸馏”：

1. 把当天的碎片需求提炼成模块级 PRD。
2. 把高风险、必须验证的规则整理成约束合同。
3. 在提交代码前提醒 agent 把文档和实现一起收尾。

它可以和 [`context-keeper`](https://github.com/vincent4j/context-keeper) 配合：`context-keeper` 负责保存每日 plans / worklog，PRD Distill 负责把这些材料继续提炼成长期有效的模块 PRD。

## 适合什么场景

- 你经常在和 AI 聊天时临时补充需求、纠正方向、指出边界。
- 一个项目会连续做很多天，不能只靠当前对话记忆。
- PRD 经常落后于实现，后续 agent 容易重复踩坑。
- 你希望提交代码前，产品文档、约束和实现能一起收尾。

## 功能

- **提炼 PRD**：读取聊天上下文、`docs/plans/`、`docs/worklog/`、已有 PRD 和 `git diff`，更新模块级 PRD。
- **整理约束合同**：把“必须 / 不能 / 每个 / 之前解决过又复现”这类强约束，沉淀到 `docs/prd/contracts/`。
- **检查实现与文档是否一致**：提交前检查 PRD、合同、测试和运行证据是否对齐。
- **Claude Code 自动化**：默认安装全局 hooks，支持聊天时自动收集强需求片段，以及提交前拦截未收尾的 PRD / 合同草稿。

这里的“约束合同”不是法律合同，而是一条可检查的长期规则。例如：某个字段必须来自哪个来源、缺失时必须失败而不是猜测、某个高风险流程必须有测试和运行证据。

## Codex 和 Claude Code 的区别

这个区别很关键：

| 能力 | Claude Code | Codex |
|---|---|---|
| 手动触发 | `/prd-distill` | `[$prd-distill]` |
| 聊天时自动收集强需求 | 支持。全局 `UserPromptSubmit` hook 会把强需求片段写入 `docs/prd/inbox/` | 不支持。Codex 目前没有等价的用户消息生命周期 hook |
| 提交前自动拦截 | 支持。全局 `PreToolUse` hook 会在 `git commit` 前检查 inbox 草稿 | 不支持内建拦截；依赖 agent 在提交前按 skill 规则先收尾 |
| 提交前收尾 | hook + skill 双保险 | skill 行为约定；你说“提交 / 保存并提交 / push”时，agent 应该先收尾再提交 |

所以：

- Claude Code 可以做到：**聊天时自动收集 + 提交前自动拦截**。
- Codex 可以做到：**手动触发 / 提交前 agent 触发**，但做不到“每条用户消息自动进 inbox”。

## Claude Code 全局 hooks 如何工作

Claude Code 的全局 hooks 是 PRD Distill 的关键自动化层。完整安装后，它会写入 `~/.claude/settings.json`，并把脚本放到 `~/.claude/hooks/prd-distill/`。之后所有 Claude Code 项目都会自动拥有两道机制：

1. **聊天时收集强需求**
   每次你发送消息后，`UserPromptSubmit` hook 会检查这条消息里是否出现“必须 / 不能 / 每个 / 之前解决过 / 为什么会没有”这类强约束信号。如果命中，它会把原文片段追加到当前项目的 `docs/prd/inbox/YYYY-MM-DD-requirement-fragments.md`。

2. **提交前拦截未收尾草稿**
   当 agent 准备执行 `git commit` 时，`PreToolUse` hook 会检查 `docs/prd/inbox/` 和 `docs/prd/contracts/inbox/` 是否还有待处理草稿。如果有，它会阻止这次提交，并要求 agent 在同一轮继续运行 `/prd-distill`，把 PRD / 合同收尾后再提交。

hooks 不会自动改写正式 PRD，也不会替你决定哪些草稿应该生效。它只负责“先收集”和“别漏提交前收尾”；真正的提炼、归并、提升为正式 PRD / 合同，仍由 `/prd-distill` 工作流完成。

## 安装

完整安装，包含 Codex / Claude Code skill 和 Claude Code 全局 hooks：

```bash
tmp="$(mktemp -d)" && git clone --depth=1 https://github.com/vincent4j/prd-distill "$tmp" && python3 "$tmp/scripts/install.py"
```

如果只想安装 skill 文件，不写入 Claude Code 全局 hooks：

```bash
npx skills add vincent4j/prd-distill
```

如果之后新安装了 Codex 或 Claude Code，重新运行完整安装命令即可补装。

## 手动安装

在仓库目录内运行：

```bash
python3 scripts/install.py
```

安装器会自动检测本机运行时：

- 只安装了 Codex：安装到 Codex。
- 只安装了 Claude Code：安装到 Claude Code，并默认安装全局 hooks。
- 两者都安装了：两边都安装。

常用参数：

```bash
python3 scripts/install.py --all
python3 scripts/install.py --codex
python3 scripts/install.py --claude
python3 scripts/install.py --codex --codex-dir ~/.agents/skills
python3 scripts/install.py --all --no-claude-hooks
```

Claude Code hooks 默认安装到：

```text
~/.claude/settings.json
~/.claude/hooks/prd-distill/
```

## 使用

Codex 中输入：

```text
[$prd-distill]
```

Claude Code 中输入：

```text
/prd-distill
```

然后选择：

```text
1. 提炼 PRD
2. 整理约束合同
3. 检查实现与文档是否一致
```

## 生成的文件

PRD Distill 会在项目中生成或更新：

```text
docs/
└── prd/
    ├── README.md                  # 模块索引：项目有哪些模块，每个模块对应哪份 PRD / 合同
    ├── inbox/                     # 待提炼的需求碎片
    ├── [module].md                # 模块级 PRD
    └── contracts/
        ├── README.md              # 合同索引
        ├── inbox/                 # 待确认的合同草稿
        └── [module].md            # 已生效的模块约束合同
```

## 和 context-keeper 的关系

`context-keeper` 和 `prd-distill` 不是替代关系，而是上下游关系。

- `context-keeper` 记录“今天发生了什么”：它按天保存对话上下文、plans、worklog 和经验摘要，保留当天的原始背景。
- `prd-distill` 提炼“长期应该遵守什么”：它把多天、多轮对话里的需求碎片，按功能模块归并成 PRD，并把必须验证的规则整理成约束合同。

推荐节奏是：

1. 工作结束时，用 `context-keeper` 保存当天上下文。
2. 当某个模块的需求逐渐稳定，或准备提交代码时，用 PRD Distill 把近期碎片提炼进 `docs/prd/`。
3. 后续 agent 不需要翻完整聊天记录，只看模块 PRD 和约束合同，就能知道当前有效规则。

你可以只安装 PRD Distill；如果项目里已经有 `context-keeper` 生成的 `docs/plans/` 和 `docs/worklog/`，PRD Distill 会把它们当作更稳定的输入材料。

## 提交前收尾

PRD Distill 的收尾应该发生在 `git commit` 之前，而不是提交之后。

推荐流程：

1. agent 准备提交代码前，先运行 PRD Distill。
2. 如果有新的需求、约束或实现变化，先更新 `docs/prd/**`。
3. 把代码和 PRD / 合同文件一起 `git add`。
4. 再执行 `git commit`。

这样代码和文档会进入同一个提交，不需要提交后再补一次 md。

## 文件结构

```text
prd-distill/
├── README.md
├── scripts/
│   └── install.py
└── skills/
    └── prd-distill/
        ├── SKILL.md
        ├── agents/
        ├── assets/
        ├── references/
        └── scripts/
```
