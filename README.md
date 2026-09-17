# prd-distill

PRD Distill 用来解决一个很常见的问题：你和 AI 明明已经把需求、规则、坑点都说清楚了，但过几天换个会话、换个 agent，它又忘了。

它是一个面向 Codex 和 Claude Code 的 skill，会把对话里的零散需求、纠正、临时决策和代码变更，提炼成模块 PRD，并把必须长期遵守的规则沉淀为约束合同。

## 为什么我会做这个 Skill

用 AI 写一个稍微大一点的应用，最烦的不是让它写代码，而是让它一直记得“以前到底说好了什么”。

我自己反复遇到的是这三个问题：

- 改一个旧模块时，已经想不起当时的详细需求、功能边界和设计原因，只能让 AI 重新读代码、重新研究现状。
- 之前已经修过、验证过的 bug，因为只留在聊天记录里，后续改功能时又被改回来了。
- 过去已经纠正过 AI、明确过的规则，比如固定路径、字段来源、失败处理，一段时间后新的 agent 又不遵守了。

PRD Distill 想解决的就是这些问题：不要让重要规则只活在聊天里，也不要让每次开发都重新读代码、重新猜历史。后面的 agent 再改同一个模块时，应该先查模块 PRD 和约束合同，再动代码。

## 它做什么

- **提炼模块 PRD**：把当天或近期的碎片需求整理成“这个模块现在应该怎么工作”。
- **整理约束合同**：把不能回归、必须验证、以后不能再改坏的规则沉淀下来。
- **写入项目入口规则**：让后续 agent 知道开发前应该先查 PRD / 合同。
- **提交前收尾**：提醒 agent 把代码、PRD、合同和验证证据一起对齐。
- **按需消费 `context-keeper` 证据**：通过 `--evidence <file>` 把 `context-keeper/` 下已定位的具体文件作为有限历史证据交给 PRD Distill；命中用 `type: "evidence"` 单独标识，不主动宽扫历史目录。

`context-keeper` 更像”当天工作记录”，PRD Distill 更像”长期规则整理”。两者互相独立：没有 `context-keeper` 时 PRD Distill 仍能根据当前对话、当前代码和已有产品文档工作；没有 PRD Distill 时 `context-keeper` 仍能保存进度。两者同时存在时，PRD Distill 只在显式提供 `context-keeper/` 下的具体文件时消费其内容，不主动宽扫历史目录。

## 怎么开始用

在 Codex 中输入 `[$prd-distill]`，或在 Claude Code 中输入 `/prd-distill`，然后选择要做的事：提炼 PRD、整理约束合同，或检查实现与文档是否一致。

你也可以直接把任务交给 agent：

```text
请使用 PRD Distill 初始化这个项目的 PRD / 合同结构，并写入 AGENTS.md / CLAUDE.md 桥接规则。
```

或者在提交前说：

```text
请使用 PRD Distill 检查当前实现和模块 PRD / 合同是否一致，提交前把需要收尾的文档一起处理掉。
```

## 安装

推荐让 agent 帮你安装。把下面这段复制给你正在使用的 Codex / Claude Code / 其他本地 agent，它会拉取仓库、运行安装器并完成校验。

```text
请帮我在本机安装 PRD Distill。

要求：
1. 从 https://github.com/vincent4j/prd-distill 拉取最新代码。
2. 运行仓库里的 scripts/install.py，安装到本机可用的 Codex / Claude Code skills。
3. 如果本机有 Claude Code，请同时安装 Claude Code 全局 hooks。
4. 安装后校验 skill 可用，并告诉我安装到哪些路径。
```

如果只想安装 skill，不想安装 Claude Code hooks，把第 3 条改成：

```text
不要安装 Claude Code 全局 hooks，只安装 skill 文件。
```

手动安装备用：在仓库目录运行 `python3 scripts/install.py`；如果不装 hooks，运行 `python3 scripts/install.py --all --no-claude-hooks`。

## 它会生成什么

在项目里，PRD Distill 主要维护这些内容：

- `docs/prd/README.md`：模块索引，告诉后续 agent 去哪里找规则。
- `docs/prd/<module>.md`：模块 PRD，记录当前有效需求和行为。
- `docs/prd/contracts/<module>.md`：约束合同，记录不能回归的规则、验证方式和证据要求。
- `AGENTS.md` / `CLAUDE.md`：很短的桥接规则，让新会话知道开发前要先查 PRD / 合同。

重复运行时，它只更新受控块和 PRD / 合同相关文件，不会改写项目里的其他说明。

## 后续 agent 会怎么用它

当你提出一个新需求，比如“改一下采集逻辑”或“优化某个模块”时，agent 应该先做四件事：

1. 用模块名、业务词、文件名、接口名或错误现象，在 `docs/prd/README.md` 里定位相关模块。
2. 只读取相关模块 PRD 和约束合同，不全文翻旧聊天、不宽扫整个项目。
3. 如果新需求和已有规则冲突，先列出冲突点，请你确认。
4. 改完代码后，按受影响合同跑测试或补充运行证据。

这就是 PRD Distill 真正想提供的价值：让后续 agent 不靠猜、不靠临时记忆，而是按项目里已经沉淀下来的规则继续开发。

## 与 `context-keeper` 配合

PRD Distill 与 `context-keeper` 互相独立。`context-keeper/` 下的 plan、worklog、memory、evolution 不会被 PRD Distill 默认读取；只有显式传入 `--evidence` 时才会消费对应文件。

典型用法：

```bash
# 默认: 只搜当前 PRD 和合同
python3 skills/prd-distill/scripts/prd_distill.py lookup \
  --root <repo> --query '<关键词>'

# 需要把 context-keeper 已定位的历史文件作为有限证据
python3 skills/prd-distill/scripts/prd_distill.py lookup \
  --root <repo> --query '<关键词>' \
  --evidence context-keeper/plans/2026-09-17-主题.md \
  --evidence context-keeper/memory-keeper.md
```

`--evidence` 文件不存在、不是文件或不在项目根下时立即报错，不会偷偷扩大搜索范围；evidence 命中用 `type: "evidence"` 单独标识，与当前 PRD/合同命中分开。零命中不报错也不回退。

## Codex 和 Claude Code 的区别

- **Codex**：可以手动触发 `[$prd-distill]`，也可以在提交前让 agent 主动收尾。
- **Claude Code**：除了手动触发 `/prd-distill`，还可以通过全局 hooks 自动收集强需求片段，并在 `git commit` 前拦截未收尾的 PRD / 合同草稿。

所以，如果你主要用 Claude Code，建议完整安装 hooks；如果你主要用 Codex，只安装 skill 也能覆盖主要工作流。
