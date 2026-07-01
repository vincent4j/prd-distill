#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


def _hook_exists(items: list[dict], command_suffix: str) -> bool:
    needle = command_suffix.replace("\\", "/")
    for group in items:
        for hook in group.get("hooks", []):
            command = str(hook.get("command") or "").replace("\\", "/")
            if needle in command:
                return True
    return False


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _install_claude_hooks(project: Path) -> None:
    project = project.expanduser().resolve()
    hooks_dir = project / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("harvest_prd_prompt.py", "guard_prd_commit.py"):
        target = hooks_dir / name
        shutil.copy2(SOURCE_SKILL / "scripts" / "claude_hooks" / name, target)
        _make_executable(target)

    settings_path = project / ".claude" / "settings.json"
    settings = _load_json(settings_path)
    hooks = settings.setdefault("hooks", {})
    user_prompt = hooks.setdefault("UserPromptSubmit", [])
    pre_tool = hooks.setdefault("PreToolUse", [])

    harvest_command = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/harvest_prd_prompt.py"'
    guard_command = 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_prd_commit.py"'

    if not _hook_exists(user_prompt, "harvest_prd_prompt.py"):
        user_prompt.append({
            "hooks": [{"type": "command", "command": harvest_command}]
        })
    if not _hook_exists(pre_tool, "guard_prd_commit.py"):
        pre_tool.append({
            "matcher": "Bash",
            "hooks": [{
                "type": "command",
                "command": guard_command,
            }],
        })

    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为本机已安装的 Codex 和 Claude Code 安装 prd-distill"
    )
    parser.add_argument("--all", action="store_true", help="强制安装到 Codex 和 Claude Code 的全局 skills 目录")
    parser.add_argument("--codex", action="store_true", help="安装到 Codex skills 目录")
    parser.add_argument("--codex-dir", help="指定 Codex skills 目录")
    parser.add_argument("--claude", action="store_true", help="安装到 Claude Code 全局 skills 目录")
    parser.add_argument("--claude-dir", help="指定 Claude Code 全局 skills 目录")
    parser.add_argument("--claude-project", help="安装到 <project>/.claude/skills")
    parser.add_argument("--install-claude-hooks", action="store_true", help="把 Claude Code hooks 安装到 --claude-project")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    explicit = any((
        args.all,
        args.codex,
        args.claude,
        args.claude_project,
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
    if args.install_claude_hooks and not args.claude_project:
        raise SystemExit("--install-claude-hooks 需要同时指定 --claude-project")

    if args.codex:
        installed.append(str(_copy_skill(Path(args.codex_dir) if args.codex_dir else _default_codex_dir())))
    if args.claude:
        installed.append(str(_copy_skill(Path(args.claude_dir) if args.claude_dir else _default_claude_dir())))
    if args.claude_project:
        project = Path(args.claude_project).expanduser().resolve()
        installed.append(str(_copy_skill(project / ".claude" / "skills")))
        if args.install_claude_hooks:
            _install_claude_hooks(project)
            installed.append(str(project / ".claude" / "hooks"))

    if not installed:
        raise SystemExit("没有可安装目标；请传入 --codex、--claude 或 --claude-project")

    print(json.dumps({
        "mode": "explicit" if explicit else "auto",
        "detected": detected,
        "installed": installed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
