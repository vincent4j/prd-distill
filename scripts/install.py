#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = REPO_ROOT / "skills" / "prd-distill"


_ARGPARSE_TRANSLATIONS = {
    "usage: ": "用法：",
    "options": "选项",
    "optional arguments": "选项",
    "show this help message and exit": "显示帮助并退出",
    "the following arguments are required: %s": "缺少必填参数：%s",
}

argparse._ = lambda text: _ARGPARSE_TRANSLATIONS.get(text, text)


def _home() -> Path:
    return Path(os.environ.get("HOME") or str(Path.home())).expanduser().resolve()


def _copy_skill(target_root: Path) -> Path:
    target_root = target_root.expanduser().resolve()
    target = target_root / "prd-distill"
    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SOURCE_SKILL, target)
    return target


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _detect_codex() -> bool:
    home = _home()
    return (
        _command_exists("codex")
        or (home / ".agents").exists()
        or (home / ".codex").exists()
    )


def _detect_claude() -> bool:
    home = _home()
    return _command_exists("claude") or (home / ".claude").exists()


def _default_codex_dir() -> Path:
    home = _home()
    for candidate in (
        home / ".agents" / "skills",
        home / ".codex" / "skills",
    ):
        if candidate.exists():
            return candidate
    return home / ".agents" / "skills"


def _default_claude_dir() -> Path:
    return _home() / ".claude" / "skills"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _remove_hook(items: list[dict], command_suffix: str) -> None:
    needle = command_suffix.replace("\\", "/")
    for group in items:
        kept = []
        for hook in group.get("hooks", []):
            command = str(hook.get("command") or "").replace("\\", "/")
            if needle not in command:
                kept.append(hook)
        group["hooks"] = kept
    items[:] = [
        group for group in items
        if group.get("hooks")
    ]


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _install_claude_hooks(claude_dir: Path) -> Path:
    claude_dir = claude_dir.expanduser().resolve()
    hooks_dir = claude_dir / "hooks" / "prd-distill"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("harvest_prd_prompt.py", "guard_prd_commit.py"):
        target = hooks_dir / name
        shutil.copy2(SOURCE_SKILL / "scripts" / "claude_hooks" / name, target)
        _make_executable(target)

    settings_path = claude_dir / "settings.json"
    settings = _load_json(settings_path)
    hooks = settings.setdefault("hooks", {})
    user_prompt = hooks.setdefault("UserPromptSubmit", [])
    pre_tool = hooks.setdefault("PreToolUse", [])

    harvest_command = f"python3 {shlex.quote(str(hooks_dir / 'harvest_prd_prompt.py'))}"
    guard_command = f"python3 {shlex.quote(str(hooks_dir / 'guard_prd_commit.py'))}"

    _remove_hook(user_prompt, "harvest_prd_prompt.py")
    _remove_hook(pre_tool, "guard_prd_commit.py")
    user_prompt.append({
        "hooks": [{"type": "command", "command": harvest_command}]
    })
    pre_tool.append({
        "matcher": "Bash",
        "hooks": [{
            "type": "command",
            "command": guard_command,
        }],
    })

    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return hooks_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为本机已安装的 Codex 和 Claude Code 安装 prd-distill"
    )
    parser.add_argument("--all", action="store_true", help="强制安装到 Codex 和 Claude Code 的全局 skills 目录")
    parser.add_argument("--codex", action="store_true", help="安装到 Codex skills 目录")
    parser.add_argument("--codex-dir", help="指定 Codex skills 目录")
    parser.add_argument("--claude", action="store_true", help="安装到 Claude Code 全局 skills 目录")
    parser.add_argument("--claude-dir", help="指定 Claude Code 全局 skills 目录")
    parser.add_argument("--no-claude-hooks", action="store_true", help="不安装 Claude Code hooks")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    explicit = any((
        args.all,
        args.codex,
        args.claude,
    ))
    detected = {
        "codex": _detect_codex(),
        "claude": _detect_claude(),
    }
    installed: list[str] = []

    if args.all:
        args.codex = True
        args.claude = True
    elif not explicit:
        args.codex = detected["codex"]
        args.claude = detected["claude"]
        if not args.codex and not args.claude:
            args.codex = True
            args.claude = True
    if args.codex:
        installed.append(str(_copy_skill(Path(args.codex_dir) if args.codex_dir else _default_codex_dir())))
    if args.claude:
        installed.append(str(_copy_skill(Path(args.claude_dir) if args.claude_dir else _default_claude_dir())))
        if not args.no_claude_hooks:
            installed.append(str(_install_claude_hooks(_home() / ".claude")))

    if not installed:
        raise SystemExit("没有可安装目标；请传入 --codex 或 --claude")

    print(json.dumps({
        "mode": "explicit" if explicit else "auto",
        "detected": detected,
        "installed": installed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
