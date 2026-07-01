#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def _pending(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in (
        root / "docs" / "prd" / "inbox",
        root / "docs" / "prd" / "contracts" / "inbox",
    ):
        if directory.exists():
            files.extend(sorted(directory.glob("*.md")))
    return files


def _command(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        value = tool_input.get("command")
        if isinstance(value, str):
            return value
    return ""


def _is_git_commit(command: str) -> bool:
    return bool(re.search(
        r"(?:^|[;&|]{1,2}\s*)git(?:\s+(?:-[^\s]+|--[^\s]+)(?:\s+\S+)*)*\s+commit(?:\s|$)",
        command,
    ))


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))


def main() -> int:
    if os.environ.get("PRD_DISTILL_ALLOW_PENDING") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    command = _command(payload)
    if not _is_git_commit(command):
        return 0
    root = _project_root()
    pending = _pending(root)
    if not pending:
        return 0
    sample = "\n".join(f"- {path.relative_to(root)}" for path in pending[:8])
    more = "" if len(pending) <= 8 else f"\n... and {len(pending) - 8} more"
    _deny(
        "PRD Distill found pending PRD/contract inbox drafts before commit. "
        "Run /prd-distill, finish PRD/constraint-contract closeout, stage the "
        "generated docs with the code, then retry git commit. This keeps docs "
        "and implementation in the same commit. Set PRD_DISTILL_ALLOW_PENDING=1 "
        "to bypass intentionally.\n"
        f"{sample}{more}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
