# Claude Code Hooks for PRD Distill

Use hooks only when the user wants automation beyond skill invocation. Hooks are optional; the skill still works without them.

## Install Locations

Project-level hooks:

```text
.claude/settings.json
.claude/hooks/
```

Skill-provided hook scripts:

```text
skills/prd-distill/scripts/claude_hooks/
```

Copy or reference the scripts from project `.claude/settings.json`.

## Suggested Settings

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/harvest_prd_prompt.py\""
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
                "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_prd_commit.py\""
              }
            ]
          }
    ]
  }
}
```

## Hook Behavior

`harvest_prd_prompt.py`:

- Reads the user prompt from stdin JSON.
- Detects strong requirement phrases such as `必须`, `不能`, `每个`, `之前解决过`, `为什么会没有`.
- Appends a timestamped fragment to `docs/prd/inbox/YYYY-MM-DD-requirement-fragments.md`.
- Does not create active PRD or contract files.

`guard_prd_commit.py`:

- Runs on Bash tool calls and exits without action unless the command is a `git commit`.
- Blocks commits when `docs/prd/inbox/*.md` or `docs/prd/contracts/inbox/*.md` contains pending drafts.
- The block is intentionally pre-commit. Run `/prd-distill`, stage generated PRD/contract docs with code, then retry the commit.
- Set `PRD_DISTILL_ALLOW_PENDING=1` to bypass intentionally.

## Safety

Hooks should capture and block only. They should not rewrite active PRD files automatically and should not generate docs after a commit. Promotion from inbox to active PRD/contracts remains an agent/user decision before the final commit.
