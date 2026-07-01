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


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", text.strip()).strip("-")
    return cleaned.lower() or "general"


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

    print(json.dumps({"created_or_existing": created}, ensure_ascii=False, indent=2))
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
        print(f"exists: {path}", file=sys.stderr)
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
        warnings.append("missing docs/prd/README.md module index")
    if not (root / "docs" / "prd" / "contracts" / "README.md").exists():
        warnings.append("missing docs/prd/contracts/README.md contract index")

    pending = _pending_files(root)
    if pending:
        warnings.append(f"pending PRD/contract drafts: {len(pending)}")

    for path in _active_contract_files(root):
        text = path.read_text(encoding="utf-8")
        for required in ("## 关联 PRD", "## 合同列表"):
            if required not in text:
                errors.append(f"{path}: missing {required}")
        if "测试" not in text:
            errors.append(f"{path}: active contracts must mention tests")
        if "运行证据" not in text:
            errors.append(f"{path}: active contracts must mention runtime evidence")

    result = {"errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PRD Distill helper")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="initialize docs/prd structure")
    init.add_argument("--root", default=".")
    init.set_defaults(func=cmd_init)

    scan = sub.add_parser("scan", help="scan PRD-related docs")
    scan.add_argument("--root", default=".")
    scan.set_defaults(func=cmd_scan)

    new_contract = sub.add_parser("new-contract", help="create a draft contract")
    new_contract.add_argument("--root", default=".")
    new_contract.add_argument("--module", required=True)
    new_contract.add_argument("--title", required=True)
    new_contract.add_argument("--kind", default="decision")
    new_contract.add_argument("--source", default="user_feedback")
    new_contract.add_argument("--trigger", default="")
    new_contract.add_argument("--contract", default="TBD")
    new_contract.add_argument("--force", action="store_true")
    new_contract.set_defaults(func=cmd_new_contract)

    pending = sub.add_parser("pending", help="list pending PRD/contract drafts")
    pending.add_argument("--root", default=".")
    pending.add_argument("--fail", action="store_true")
    pending.set_defaults(func=cmd_pending)

    check = sub.add_parser("check", help="validate PRD/contract structure")
    check.add_argument("--root", default=".")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
