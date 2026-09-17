#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
BRIDGE_START = "<!-- prd-distill:start -->"
BRIDGE_END = "<!-- prd-distill:end -->"
BRIDGE_CONTENT = f"""{BRIDGE_START}
## PRD / 合同约束

开发、修 bug、改行为或遇到陌生业务词时，先检索项目知识库，不全文加载文档。

1. 用模块名、业务词、文件名、接口名、字段名、错误现象或合同 ID 检索 `docs/prd/README.md`，只读命中上下文。
2. 继续在相关 PRD / 合同中关键词检索，只读命中条目；命中不清、跨模块或触碰核心流程 / 数据 / 安全边界时才扩大读取。
3. 历史经验由 context-keeper 提供；按需消费已定位的有限证据，不依赖 context-keeper 也能运行。硬约束以 `docs/prd/contracts/` 为准。
4. 编码前有命中则列最多 5 条 `受影响合同：<ID>：原因；证据：类型`；无命中只说 `未命中生效合同`。
5. 实现后只验受影响合同；UI / UX / 视觉 / 交互 / 响应式需截图、DOM 或页面证据；无匹配证据不能宣称完成。
6. 最终只报告命中合同状态 `通过 / 部分通过 / 未验证 / 不适用`；提交前若改了 PRD / 合同，先做 PRD Distill 收尾。
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


def _select_bridge_targets(root: Path, mode: str = "existing") -> list[Path]:
    """选择要写入受控块的入口桥接文件。

    mode 取值:
    - "claude"   只写 CLAUDE.md (默认, 多数用户用 Claude Code)
    - "agents"   只写 AGENTS.md (Codex / OpenAI agents)
    - "both"     两个都写
    - "existing" 项目根里有哪个就写哪个, 都没有时同时创建两个
    """
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if mode == "claude":
        return [claude]
    if mode == "agents":
        return [agents]
    if mode == "both":
        return [agents, claude]
    if mode == "existing":
        existing = [path for path in (agents, claude) if path.exists()]
        return existing or [agents, claude]
    raise ValueError(f"未知的 --bridge-target: {mode}")


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
    """完整启用 PRD Distill 于本项目:
    1. 创建 docs/prd/ 结构 (PRD / 合同目录)
    2. 写入入口桥接块 (CLAUDE.md / AGENTS.md)
    3. 写项目级 .claude/settings.json 的 hook 配置

    三步一起做才能让本项目真正"启用": 没 init 的项目压根不会创建
    docs/prd/ 目录, 也没项目级 hook 配置, hook 不被 Claude Code 调用。
    """
    root = Path(args.root).resolve()
    prd = root / "docs" / "prd"
    contracts = prd / "contracts"
    created: list[str] = []

    if _write_if_missing(prd / "README.md", _read_template("prd-index.md")):
        created.append("docs/prd/README.md")
    if _write_if_missing(contracts / "README.md", _read_template("contracts-readme.md")):
        created.append("docs/prd/contracts/README.md")

    bridge_targets = _select_bridge_targets(root, args.bridge_target)
    bridge_results = []
    for path in bridge_targets:
        action = _upsert_bridge(path)
        bridge_results.append({
            "file": str(path.relative_to(root)),
            "action": action,
        })

    # init 自动写项目级 hook 配置: 装好脚本路径引用, 让 Claude Code 在
    # 本项目里调用 harvest / guard hook。未 init 的项目无 settings.json,
    # hook 不被调用, docs/prd/ 也不会被创建。
    hook_result = _write_project_hooks(root)

    print(json.dumps({
        "created_or_existing": created,
        "bridge": bridge_results,
        "hook": hook_result,
        "enabled": True,
    }, ensure_ascii=False, indent=2))
    return 0


def _write_project_hooks(root: Path) -> dict[str, object]:
    """把 hook 配置写到 <root>/.claude/settings.json (项目级), 返回结果摘要。

    抽出来给 cmd_init 和 cmd_install_hooks 共用。
    """
    home = Path.home()
    hooks_dir = home / ".claude" / "hooks" / "prd-distill"
    harvest_script = hooks_dir / "harvest_prd_prompt.py"
    guard_script = hooks_dir / "guard_prd_commit.py"

    claude_dir = root / ".claude"
    settings_path = claude_dir / "settings.json"

    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    user_prompt = hooks.setdefault("UserPromptSubmit", [])
    pre_tool = hooks.setdefault("PreToolUse", [])

    _remove_hook_entry(user_prompt, "harvest_prd_prompt.py")
    _remove_hook_entry(pre_tool, "guard_prd_commit.py")

    user_prompt.append({
        "hooks": [{"type": "command", "command": f"python3 {shlex.quote(str(harvest_script))}"}]
    })
    pre_tool.append({
        "matcher": "Bash",
        "hooks": [{
            "type": "command",
            "command": f"python3 {shlex.quote(str(guard_script))}",
        }],
    })

    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "settings_file": str(settings_path.relative_to(root)),
        "hook_scripts_dir": str(hooks_dir),
        "scope": "project",
        "rule": "未启用的项目没有 settings.json, hook 不被 Claude Code 调用, docs/prd/ 也不会被创建",
    }


def cmd_install_bridge(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    targets = _select_bridge_targets(root, args.bridge_target)
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


def _list_md(path: Path, base: Path | None = None) -> list[str]:
    if not path.exists():
        return []
    if base is None:
        return sorted(str(item) for item in path.glob("*.md"))
    return sorted(str(item.relative_to(base)) for item in path.glob("*.md"))


def _find_memory_keeper_files(root: Path) -> list[str]:
    """全项目扫描 memory-keeper.md, 返回相对路径列表(已排序)。

    context-keeper 的存储目录是用户可配置的(--store-dir / 配置文件 /
    _discovery_candidates 发现), 任何固定路径枚举都会漏掉自定义位置。
    但 memory-keeper.md 作为 context-keeper 的统一入口文件名, 不管
    目录在哪, 全项目 rglob 都能可靠发现。
    """
    return sorted(
        str(p.relative_to(root))
        for p in root.rglob("memory-keeper.md")
        if p.is_file()
    )


def cmd_scan(args: argparse.Namespace) -> int:
    """列出 PRD / 合同目录、旧版历史目录(根 docs/ 下 plans / worklog)与
    全项目找到的 memory-keeper.md。

    memory-keeper.md 全项目扫描不假设 context-keeper 存储目录的位置;
    plans / worklogs / evolution 等子目录内容由 --evidence 显式提供。
    """
    root = Path(args.root).resolve()
    legacy = root / "docs"
    data = {
        "context_keeper": {
            "memory_keeper_files": _find_memory_keeper_files(root),
        },
        "legacy_history": {
            "plans": _list_md(legacy / "plans", root),
            "worklogs": _list_md(legacy / "worklog", root),
        },
        "prd": _list_md(root / "docs" / "prd", root),
        "prd_inbox": _list_md(root / "docs" / "prd" / "inbox", root),
        "contracts": _list_md(root / "docs" / "prd" / "contracts", root),
        "contracts_inbox": _list_md(root / "docs" / "prd" / "contracts" / "inbox", root),
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


def _compile_query(query: str) -> re.Pattern[str]:
    try:
        return re.compile(query, re.IGNORECASE)
    except re.error:
        return re.compile(re.escape(query), re.IGNORECASE)


def _clip(text: str, limit: int = 240) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _validate_evidence(evidence_files: list[str], root: Path) -> list[Path]:
    """校验 --evidence 显式传入的文件:
    必须是项目根下的现有文件。返回绝对路径列表。

    校验失败时给出明确错误, 不自动扩大搜索范围。
    """
    validated: list[Path] = []
    for raw in evidence_files:
        path = Path(raw).expanduser().resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise SystemExit(
                f"error: evidence {raw} 超出项目根 {root}"
            )
        if not path.exists():
            raise SystemExit(f"error: evidence {raw} 不存在")
        if not path.is_file():
            raise SystemExit(f"error: evidence {raw} 不是文件")
        validated.append(path)
    return validated


def _collect_lookup_candidates(
    root: Path, evidence_paths: list[Path]
) -> list[Path]:
    """默认且始终只搜索 docs/prd/ 与生效合同。
    evidence_paths 由 --evidence 显式传入, 必须已通过 _validate_evidence 验证。
    不在候选列表中默认包含 context-keeper/ 或旧版历史目录。
    """
    candidates: list[Path] = []
    prd = root / "docs" / "prd"
    contracts = prd / "contracts"

    for path in (
        prd / "README.md",
        *sorted(item for item in prd.glob("*.md") if item.name != "README.md"),
        contracts / "README.md",
        *sorted(item for item in contracts.glob("*.md") if item.name != "README.md"),
    ):
        if path.exists():
            candidates.append(path)
    candidates.extend(evidence_paths)
    return candidates


def _line_hits(path: Path, pattern: re.Pattern[str], limit: int) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if pattern.search(line):
            hits.append({"line": lineno, "text": _clip(line)})
            if len(hits) >= limit:
                break
    return hits


def cmd_lookup(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    evidence_paths = _validate_evidence(args.evidence or [], root)
    evidence_set = {str(path.relative_to(root)) for path in evidence_paths}
    pattern = _compile_query(args.query)
    searched: list[str] = []
    records: list[dict[str, object]] = []

    for path in _collect_lookup_candidates(root, evidence_paths):
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        searched.append(rel)
        hits = _line_hits(path, pattern, args.max_matches_per_file)
        if not hits:
            continue
        score = len(hits)
        if rel == "docs/prd/README.md":
            score += 100
        if pattern.search(rel):
            score += 20
        record_type = "evidence" if rel in evidence_set else "prd_or_contract"
        records.append(
            {"file": rel, "type": record_type, "hits": hits, "_score": score}
        )

    records.sort(key=lambda item: (-int(item["_score"]), str(item["file"])))
    matches = [
        {"file": item["file"], "type": item["type"], "hits": item["hits"]}
        for item in records[: args.max_files]
    ]

    print(json.dumps({
        "root": str(root),
        "query": args.query,
        "searched_files": len(searched),
        "max_files": args.max_files,
        "max_matches_per_file": args.max_matches_per_file,
        "evidence_files": sorted(evidence_set),
        "truncated": len(records) > args.max_files,
        "matches": matches,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_pending(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    pending = _pending_files(root)
    for path in pending:
        print(path)
    return 1 if pending and args.fail else 0


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    prd = root / "docs" / "prd"
    errors: list[str] = []
    warnings: list[str] = []

    if not prd.exists():
        print(json.dumps({
            "status": "not_initialized",
            "errors": errors,
            "warnings": warnings,
        }, ensure_ascii=False, indent=2))
        return 0

    if not (prd / "README.md").exists():
        warnings.append("缺少 docs/prd/README.md 模块索引")
    if not (prd / "contracts" / "README.md").exists():
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

    result = {"status": "initialized", "errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    """把 hook 配置写到 <project>/.claude/settings.json (项目级)。

    hook 脚本本身来自 ~/.claude/hooks/prd-distill/ (由 install.py 装一次,
    所有项目共用), 项目级 settings.json 只引用其路径。未启用的项目
    没有这个文件, hook 不会被触发。
    """
    root = Path(args.root).resolve()
    result = _write_project_hooks(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _remove_hook_entry(items: list[dict], script_name: str) -> None:
    """从 settings.json 的 hook 列表里移除引用指定脚本的条目。"""
    needle = script_name.replace("\\", "/")
    kept_items: list[dict] = []
    for group in items:
        kept_group_hooks: list[dict] = []
        for hook in group.get("hooks", []):
            command = str(hook.get("command") or "").replace("\\", "/")
            if needle not in command:
                kept_group_hooks.append(hook)
        if kept_group_hooks:
            new_group = dict(group)
            new_group["hooks"] = kept_group_hooks
            kept_items.append(new_group)
    items[:] = kept_items


def cmd_status(args: argparse.Namespace) -> int:
    """报告项目级 PRD Distill 启用状态。

    PRD Distill 是项目级 skill: 默认对所有项目都不启用。Agent 在对话中
    识别触发词且项目未启用时, 调用 status 确认状态, 然后询问用户
    是否启用 (运行 init --root <repo>)。
    """
    root = Path(args.root).resolve()
    enabled = (root / "docs" / "prd" / "README.md").exists()
    print(json.dumps({
        "root": str(root),
        "prd_distill_enabled": enabled,
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PRD Distill 辅助工具")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="初始化 docs/prd 结构")
    init.add_argument("--root", default=".")
    init.add_argument(
        "--bridge-target",
        choices=("claude", "agents", "both", "existing"),
        default="claude",
        help="入口桥接文件选择: claude=只写 CLAUDE.md, agents=只写 AGENTS.md, "
             "both=两个都写, existing=按现状逻辑 (默认 claude)",
    )
    init.set_defaults(func=cmd_init)

    bridge = sub.add_parser("install-bridge", help="安装 AGENTS.md / CLAUDE.md 桥接规则")
    bridge.add_argument("--root", default=".")
    bridge.add_argument(
        "--bridge-target",
        choices=("claude", "agents", "both", "existing"),
        default="existing",
        help="入口桥接文件选择, 同 init --bridge-target",
    )
    bridge.set_defaults(func=cmd_install_bridge)

    install_hooks = sub.add_parser(
        "install-hooks",
        help="把 hook 配置写到项目级 .claude/settings.json, 不动 ~/.claude/",
    )
    install_hooks.add_argument("--root", default=".")
    install_hooks.set_defaults(func=cmd_install_hooks)

    scan = sub.add_parser("scan", help="扫描 PRD 相关文档")
    scan.add_argument("--root", default=".")
    scan.set_defaults(func=cmd_scan)

    lookup = sub.add_parser("lookup", help="窄搜索 PRD / 合同索引与目标文档")
    lookup.add_argument("--root", default=".")
    lookup.add_argument("--query", required=True)
    lookup.add_argument("--max-files", type=int, default=3)
    lookup.add_argument("--max-matches-per-file", type=int, default=8)
    lookup.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="显式传入 context-keeper 已定位的具体文件路径, 可重复; 仅读取这些文件的命中片段",
    )
    lookup.set_defaults(func=cmd_lookup)

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

    status = sub.add_parser(
        "status",
        help="报告项目级 PRD Distill 启用状态, 用于 Agent 判断是否需要询问用户启用",
    )
    status.add_argument("--root", default=".")
    status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
