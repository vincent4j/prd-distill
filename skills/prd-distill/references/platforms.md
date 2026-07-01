# 平台支持

`prd-distill` 必须同时支持 Codex 和 Claude Code。

## 共享核心

两个运行时共用同一个 skill 目录：

```text
prd-distill/
  SKILL.md
  scripts/
  references/
  assets/
```

核心工作流必须写在 `SKILL.md` 和 references 中。不要依赖 Claude Code hooks 才能正确工作。

## 推荐安装

一键安装：

```bash
npx skills add vincent4j/prd-distill
```

一次安装到所有本地支持的 Agent：

```bash
npx skills add vincent4j/prd-distill --all
```

## 手动安装

不使用 `npx skills` 时，可以运行：

```bash
python3 scripts/install.py
```

手动安装器会自动检测本机运行时：

- 只检测到 Codex：安装 Codex skill。
- 只检测到 Claude Code：安装 Claude Code skill。
- 两者都检测到：两边都安装。
- 都未检测到：预创建默认用户级 skill 目录。
- 用户之后安装另一个运行时：重新运行同一条命令即可补装。

强制同时安装到 Codex 和 Claude Code：

```bash
python3 scripts/install.py --all
```

只安装到 Codex：

```bash
python3 scripts/install.py --codex
```

安装到自定义 Codex skills 目录：

```bash
python3 scripts/install.py --codex --codex-dir ~/.agents/skills
```

只安装到 Claude Code：

```bash
python3 scripts/install.py --claude
```

安装到指定 Claude Code 项目：

```bash
python3 scripts/install.py --claude-project /path/to/project
```

安装 Claude Code 项目 hooks：

```bash
python3 scripts/install.py --claude-project /path/to/project --install-claude-hooks
```

## 使用方式

Codex：

```text
[$prd-distill]
```

Codex 没有 Claude Code hook 生命周期。使用 skill 工作流，并在提交前运行确定性检查：

```bash
python3 ~/.codex/skills/prd-distill/scripts/prd_distill.py check --root <repo>
```

Claude Code：

```text
/prd-distill
```

安装 hooks 后：

- `UserPromptSubmit` 会把强需求片段收集到 `docs/prd/inbox/`。
- `PreToolUse` 会观察 Bash 调用，并在 PRD / 合同 inbox 草稿未处理时阻止 `git commit`。

## 兼容规则

- hook 脚本必须是可选的，并且只服务于 Claude Code。
- `agents/openai.yaml` 对 Claude Code 必须无害。
- 核心脚本只使用 Python 标准库。
- 不要把平台特定假设写进文档模型。
- 不要在 `SKILL.md` 里写只有 Claude 能理解、Codex 无法安全忽略的 frontmatter。
