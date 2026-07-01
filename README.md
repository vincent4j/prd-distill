# prd-distill

`prd-distill` 用来把聊天里的片段需求、每日 plans、工作日志和代码变更，提炼成模块级 PRD，并把必须遵守的硬约束沉淀为 `docs/prd/contracts/` 下的合同文档。

它是一个同时支持 Codex 和 Claude Code 的 Skill。

## 安装

一键安装：

```bash
npx skills add vincent4j/prd-distill
```

如果希望一次安装到 Codex、Claude Code 等所有本地支持的 Agent：

```bash
npx skills add vincent4j/prd-distill --all
```

如果之后新安装了 Codex 或 Claude Code，重新运行上面的安装命令即可补装。

## 手动安装

如果不使用 `npx skills`，也可以手动安装：

```bash
python3 scripts/install.py
```

手动安装器会自动检测本机运行时：

- 只安装了 Codex：安装到 Codex。
- 只安装了 Claude Code：安装到 Claude Code。
- 两者都安装了：两边都安装。
- 后续新增其中一个运行时：重新运行同一条命令即可补装。

常用手动安装参数：

```bash
python3 scripts/install.py --all
python3 scripts/install.py --codex
python3 scripts/install.py --claude
python3 scripts/install.py --codex --codex-dir ~/.agents/skills
python3 scripts/install.py --all --claude-project /path/to/project --install-claude-hooks
```

Claude Code hooks 是可选增强；不安装 hooks 也能正常使用核心 Skill。hooks 只负责自动收集强约束片段和提交前提醒。

## 使用

Codex：

```text
[$prd-distill]
```

Claude Code：

```text
/prd-distill
```

主动触发后会进入菜单：

```text
PRD Distill - 需求蒸馏台

1. 提炼 PRD
2. 整理合同
3. 检查一致性

请选择操作（输入 1-3）：
```

## 输出目录

```text
docs/prd/README.md
docs/prd/inbox/
docs/prd/contracts/
docs/prd/contracts/inbox/
```

## 仓库结构

```text
skills/prd-distill/       # Codex 和 Claude Code 共用的 Skill 包
scripts/install.py        # 手动安装器
```
