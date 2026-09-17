#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


TRIGGERS = [
    "必须",
    "不能",
    "每个",
    "一定",
    "不要",
    "不对",
    "逻辑有问题",
    "为什么会没有",
    "真正想要",
    "以后",
    "contract",
    "invariant",
    "must",
    "must not",
    "always",
    "never",
]


HISTORY_HINTS = (
    "之前解决过",
    "以前解决过",
    "又复现",
    "我记得之前",
    "查一下上次",
    "上次怎么",
    "上次为什么",
    "上次遗漏",
    "上次出现",
    "上次遇到",
    "上回怎么",
    "上回为什么",
    "上回遗漏",
    "上回出现",
    "上回遇到",
)


def _is_history_question(text: str) -> bool:
    return any(hint in text for hint in HISTORY_HINTS)


def _extract_prompt(payload: object) -> str:
    if isinstance(payload, dict):
        for key in ("prompt", "message", "user_prompt", "text", "content"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in payload.values():
            nested = _extract_prompt(value)
            if nested:
                return nested
    if isinstance(payload, list):
        for item in payload:
            nested = _extract_prompt(item)
            if nested:
                return nested
    return ""


def _hits(text: str) -> list[str]:
    lowered = text.lower()
    return [trigger for trigger in TRIGGERS if trigger.lower() in lowered]


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def _is_prd_distill_source_root(root: Path) -> bool:
    """当前项目根是 prd-distill 自身源码仓库时跳过 hook。

    判定: 项目根同时存在 skills/prd-distill/scripts/prd_distill.py 与
    tests/test_prd_distill.py, 表明这是 prd-distill 的开发/维护仓库,
    不应在仓库自身维护 PRD 需求碎片。
    """
    return (
        (root / "skills" / "prd-distill" / "scripts" / "prd_distill.py").exists()
        and (root / "tests" / "test_prd_distill.py").exists()
    )


def _is_prd_distill_enabled(root: Path) -> bool:
    """PRD Distill 在该项目已启用 = docs/prd/README.md 存在(init 创建)。

    PRD Distill 是项目级 skill: 默认对所有项目都不生效, hook 不会自动
    写 inbox。用户通过对话显式确认启用后, `init` 命令创建
    docs/prd/README.md 等产物, hook 才对该项目开始记录需求碎片。
    """
    return (root / "docs" / "prd" / "README.md").exists()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    root = _project_root()
    # 源码根跳过: 避免开发仓库被自己的 hook 污染
    if _is_prd_distill_source_root(root):
        return 0
    # 项目未启用跳过: 默认不污染任何项目, 由 Agent 在对话中识别
    # 触发词并询问用户是否启用, 见 SKILL.md "项目级启用与对话式初始化"。
    if not _is_prd_distill_enabled(root):
        return 0

    prompt = _extract_prompt(payload)
    hits = _hits(prompt)
    if not prompt or not hits:
        return 0
    # 出现历史叙述词时整体不写, 避免把"上次怎么处理的""又复现了"等纯历史
    # 追问误当成需求收进 inbox; 含新增要求的混合消息由 Agent 显式提炼。
    if _is_history_question(prompt):
        return 0

    inbox = root / "docs" / "prd" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    now = dt.datetime.now().strftime("%H:%M:%S")
    path = inbox / f"{today}-requirement-fragments.md"
    snippet = prompt.strip()
    if len(snippet) > 1200:
        snippet = snippet[:1200].rstrip() + "..."

    with path.open("a", encoding="utf-8") as fh:
        if path.stat().st_size == 0:
            fh.write(f"# PRD 需求碎片 - {today}\n\n")
        fh.write(f"## {now}\n\n")
        fh.write(f"- **触发词：** {', '.join(hits)}\n")
        fh.write("- **状态：** 待处理\n")
        fh.write("- **原文：**\n\n")
        fh.write("```text\n")
        fh.write(snippet)
        fh.write("\n```\n\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
