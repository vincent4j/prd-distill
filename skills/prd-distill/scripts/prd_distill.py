#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
BRIDGE_START = "<!-- prd-distill:start -->"
BRIDGE_END = "<!-- prd-distill:end -->"
BRIDGE_CONTENT = f"""{BRIDGE_START}
## PRD / 合同约束

开发已有模块、修 bug、改模块行为，或遇到陌生业务名词时，先用检索方式查询项目知识库，不默认全文加载文档。

执行规则：

1. 用模块名、业务词、文件名、接口名、字段名、错误现象或合同 ID 先检索 `docs/prd/README.md`，只读命中上下文来定位模块、主 PRD 和合同。
2. 在相关 PRD / 合同中继续关键词检索，只读命中章节和相邻上下文；命中不清、跨模块或触碰核心流程 / 数据 / 安全边界时才扩大读取。
3. 若有 `docs/memory-keeper.md`，只在 bug / 回归 / 相似问题 / 高风险模块或 PRD 命中不足时检索；命中内容只作历史经验和合同候选，硬约束以 `docs/prd/contracts/` 为准。
4. 实现前列出本次可能影响的 PRD 规则或生效合同；若需求冲突，先停下请用户确认。
5. 实现后按受影响合同跑绑定测试或检查运行证据；无法验证时说明风险。
6. 提交前若本轮改了 `docs/plans/`、`docs/worklog/`、`docs/memory-keeper.md` 或 PRD / 合同，先做 PRD Distill 收尾再提交。
{BRIDGE_END}
"""


_ARGPARSE_TRANSLATIONS = {
    "usage: ": "用法：",
    "positional arguments": "位置参数",
    "options": "选项",
    "optional arguments": "选项",
    "show this help message and exit": "显示帮助并退出",
    "the following arguments are required: %s": "缺少必填参数：%s",
    "invalid choice: %(value)r (choose from %(choices)s)": "无效选择：%(value)r（可选：%(choices)s）",
}

argparse._ = lambda text: _ARGPARSE_TRANSLATIONS.get(text, text)


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", text.strip()).strip("-")
    return cleaned.lower() or "通用"


def _today() -> str:
    return dt.date.today().isoformat()


def _read_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _select_bridge_targets(root: Path) -> list[Path]:
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    existing = [path for path in (agents, claude) if path.exists()]
    return existing or [agents, claude]


def _upsert_bridge(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(BRIDGE_CONTENT + "\n", encoding="utf-8")
        return "created"

    text = path.read_text(encoding="utf-8")
    has_start = BRIDGE_START in text
    has_end = BRIDGE_END in text
    if has_start != has_end:
        raise ValueError(f"{path}: PRD Distill 受控块不完整，请先手动修复")

    if has_start:
        pattern = re.compile(
            re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END),
            re.DOTALL,
        )
        updated = pattern.sub(BRIDGE_CONTENT.rstrip(), text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            return "updated"
        return "unchanged"

    separator = "" if text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
    path.write_text(text + separator + BRIDGE_CONTENT + "\n", encoding="utf-8")
    return "appended"


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    prd = root / "docs" / "prd"
    contracts = prd / "contracts"
    created: list[str] = []

    for directory in (prd / "inbox", contracts / "inbox"):
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory.relative_to(root)))

    if _write_if_missing(prd / "README.md", _read_template("prd-index.md")):
        created.append("docs/prd/README.md")
    if _write_if_missing(contracts / "README.md", _read_template("contracts-readme.md")):
        created.append("docs/prd/contracts/README.md")

    bridge_results = []
    for path in _select_bridge_targets(root):
        action = _upsert_bridge(path)
        bridge_results.append({
            "file": str(path.relative_to(root)),
            "action": action,
        })

    print(json.dumps({
        "created_or_existing": created,
        "bridge": bridge_results,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_install_bridge(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    targets = _select_bridge_targets(root)
    results = []
    for path in targets:
        action = _upsert_bridge(path)
        results.append({
            "file": str(path.relative_to(root)),
            "action": action,
        })

    print(json.dumps({
        "root": str(root),
        "targets": results,
        "rule": "AGENTS.md 和 CLAUDE.md 都存在时同时写入；都不存在时默认创建两个；只存在一个时只写入已有文件。",
    }, ensure_ascii=False, indent=2))
    return 0


def _list_md(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(str(item) for item in path.glob("*.md"))


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    data = {
        "plans": _list_md(root / "docs" / "plans"),
        "worklogs": _list_md(root / "docs" / "worklog"),
        "memory_keeper": str(root / "docs" / "memory-keeper.md")
        if (root / "docs" / "memory-keeper.md").exists()
        else None,
        "prd": _list_md(root / "docs" / "prd"),
        "prd_inbox": _list_md(root / "docs" / "prd" / "inbox"),
        "contracts": _list_md(root / "docs" / "prd" / "contracts"),
        "contracts_inbox": _list_md(root / "docs" / "prd" / "contracts" / "inbox"),
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_new_contract(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    inbox = root / "docs" / "prd" / "contracts" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    date = _today()
    module_slug = _slug(args.module)
    title_slug = _slug(args.title)
    path = inbox / f"{date}-{module_slug}-{title_slug}.md"

    content = _read_template("contract-draft.md")
    replacements = {
        "{{title}}": args.title,
        "{{module}}": args.module,
        "{{kind}}": args.kind,
        "{{source}}": args.source,
        "{{trigger}}": args.trigger,
        "{{date}}": date,
        "{{contract}}": args.contract,
    }
    for old, new in replacements.items():
        content = content.replace(old, new)

    if path.exists() and not args.force:
        print(f"文件已存在：{path}", file=sys.stderr)
        return 1
    path.write_text(content, encoding="utf-8")
    print(path)
    return 0


def _pending_files(root: Path) -> list[Path]:
    pending: list[Path] = []
    for directory in (
        root / "docs" / "prd" / "inbox",
        root / "docs" / "prd" / "contracts" / "inbox",
    ):
        if directory.exists():
            pending.extend(sorted(directory.glob("*.md")))
    return pending


def _active_contract_files(root: Path) -> list[Path]:
    contracts = root / "docs" / "prd" / "contracts"
    if not contracts.exists():
        return []
    return [
        item
        for item in sorted(contracts.glob("*.md"))
        if item.name != "README.md"
    ]


def cmd_pending(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    pending = _pending_files(root)
    for path in pending:
        print(path)
    return 1 if pending and args.fail else 0


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not (root / "docs" / "prd" / "README.md").exists():
        warnings.append("缺少 docs/prd/README.md 模块索引")
    if not (root / "docs" / "prd" / "contracts" / "README.md").exists():
        warnings.append("缺少 docs/prd/contracts/README.md 合同索引")

    pending = _pending_files(root)
    if pending:
        warnings.append(f"待处理 PRD / 合同草稿：{len(pending)}")

    for path in _active_contract_files(root):
        text = path.read_text(encoding="utf-8")
        for required in ("## 关联 PRD", "## 合同列表"):
            if required not in text:
                errors.append(f"{path}: 缺少 {required}")
        if "测试" not in text:
            errors.append(f"{path}: 生效合同必须说明测试")
        if "运行证据" not in text:
            errors.append(f"{path}: 生效合同必须说明运行证据")

    result = {"errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PRD Distill 辅助工具")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="初始化 docs/prd 结构")
    init.add_argument("--root", default=".")
    init.set_defaults(func=cmd_init)

    bridge = sub.add_parser("install-bridge", help="安装 AGENTS.md / CLAUDE.md 桥接规则")
    bridge.add_argument("--root", default=".")
    bridge.set_defaults(func=cmd_install_bridge)

    scan = sub.add_parser("scan", help="扫描 PRD 相关文档")
    scan.add_argument("--root", default=".")
    scan.set_defaults(func=cmd_scan)

    new_contract = sub.add_parser("new-contract", help="创建合同草稿")
    new_contract.add_argument("--root", default=".")
    new_contract.add_argument("--module", required=True)
    new_contract.add_argument("--title", required=True)
    new_contract.add_argument("--kind", default="decision")
    new_contract.add_argument("--source", default="用户反馈")
    new_contract.add_argument("--trigger", default="")
    new_contract.add_argument("--contract", default="待补充")
    new_contract.add_argument("--force", action="store_true")
    new_contract.set_defaults(func=cmd_new_contract)

    pending = sub.add_parser("pending", help="列出待处理 PRD / 合同草稿")
    pending.add_argument("--root", default=".")
    pending.add_argument("--fail", action="store_true")
    pending.set_defaults(func=cmd_pending)

    check = sub.add_parser("check", help="校验 PRD / 合同结构")
    check.add_argument("--root", default=".")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
