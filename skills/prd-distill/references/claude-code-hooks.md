# Claude Code Hooks

使用本仓库安装器安装到 Claude Code 时，hooks 默认安装为全局 hooks。核心 skill 流程仍然不能依赖 hooks；hooks 只是自动收集和提交前拦截的兜底层。

## 安装位置

全局 hooks：

```text
~/.claude/settings.json
~/.claude/hooks/prd-distill/
```

skill 提供的 hook 脚本：

```text
skills/prd-distill/scripts/claude_hooks/
```

安装器会把脚本复制到 `~/.claude/hooks/prd-distill/`，并更新 `~/.claude/settings.json`。如果不想安装全局 hooks，运行安装器时传 `--no-claude-hooks`。

## 推荐配置

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/prd-distill/harvest_prd_prompt.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/prd-distill/guard_prd_commit.py"
          }
        ]
      }
    ]
  }
}
```

## Hook 行为

`harvest_prd_prompt.py`：

- 从 stdin JSON 读取用户 prompt。
- 识别 `必须`、`不能`、`每个`、`为什么会没有` 等强需求触发词；不把"之前解决过""又复现"等纯历史信号当作强需求。
- 追加写入 `docs/prd/inbox/YYYY-MM-DD-requirement-fragments.md`。
- 不直接创建生效 PRD 或合同文件。

`guard_prd_commit.py`：

- 只在 Bash 命令是 `git commit` 时生效；其他 Bash 调用直接跳过。
- 当 `docs/prd/inbox/*.md` 或 `docs/prd/contracts/inbox/*.md` 里有待处理草稿时阻止提交。
- 这是最后兜底的提交前保护。Agent 应该在同一轮运行 `/prd-distill`、把生成的 PRD / 合同文档和代码一起 stage，然后重试提交。
- 可以设置 `PRD_DISTILL_ALLOW_PENDING=1` 有意识地绕过。

## 安全边界

Hooks 只负责收集和阻止，不自动重写生效 PRD 文件，也不在提交后生成文档。是否把 inbox 提升为生效 PRD / 合同，仍由 agent / 用户在最终提交前判断。
