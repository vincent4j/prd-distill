#!/usr/bin/env python3
"""安装 prd-distill 到本机 Claude Code 和/或 Codex。

策略:
- skill 文件 -> ~/.claude/skills/prd-distill/ 和/或 ~/.agents/skills/prd-distill/
- hook 脚本 -> ~/.claude/hooks/prd-distill/ (仅 Claude Code, Codex 无 hook 系统)
- **不动** 任何 settings.json: hook 配置是项目级, 由 prd_distill.py init
  时单独写到 <project>/.claude/settings.json。

Codex 下没有 Claude Code 那种 UserPromptSubmit / PreToolUse 事件机制,
harvest_prd_prompt.py 在 Codex 下装入也跑不起来, 所以 Codex 不装 hook
脚本。所有 PRD / 合同提炼在 Codex 下要靠用户在对话里显式告诉 AI。
"""
from __future__ import annotations

import argparse
import json
import shutil
import stat
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = REPO_ROOT / "skills" / "prd-distill"


def _home() -> Path:
    return Path.home().expanduser().resolve()


def _default_codex_dir(home: Path | None = None) -> Path:
    """Codex 优先 ~/.agents/skills/ (OpenAI agents 新约定), 否则 ~/.codex/skills/。"""
    base = home if home is not None else _home()
    for candidate in (
        base / ".agents" / "skills",
        base / ".codex" / "skills",
    ):
        if candidate.exists():
            return candidate
    return base / ".agents" / "skills"


def _copy_skill(target_root: Path) -> Path:
    target_root = target_root.expanduser().resolve()
    target = target_root / "prd-distill"
    target_root.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    shutil.copytree(SOURCE_SKILL, target)
    return target


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _install_hook_scripts(hooks_root: Path) -> Path:
    """把 hook 脚本装到 <root>/hooks/prd-distill/, 不写 settings.json。

    Claude Code 专属。Codex 没这套事件机制, 不调用本函数。
    """
    hooks_dir = hooks_root / "prd-distill"
    if hooks_dir.is_symlink():
        hooks_dir.unlink()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("harvest_prd_prompt.py", "guard_prd_commit.py"):
        target = hooks_dir / name
        shutil.copy2(SOURCE_SKILL / "scripts" / "claude_hooks" / name, target)
        _make_executable(target)
    return hooks_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把 prd-distill 装到本机 Claude Code 和/或 Codex; 不写 settings.json"
    )
    parser.add_argument(
        "--target",
        choices=("claude", "codex", "both"),
        default="claude",
        help="安装目标: claude=只装 Claude Code (默认), codex=只装 Codex, "
             "both=两个都装",
    )
    parser.add_argument(
        "--no-hooks",
        action="store_true",
        help="只装 skill, 不装 Claude Code hook 脚本",
    )
    parser.add_argument(
        "--home",
        default=None,
        help="覆盖 HOME 路径; 默认 ~/.claude/ 与 ~/.agents/",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    home = (
        Path(args.home).expanduser().resolve()
        if args.home
        else Path.home().expanduser().resolve()
    )
    installed: list[str] = []

    if args.target in ("claude", "both"):
        claude_root = home / ".claude"
        skill_dir = _copy_skill(claude_root / "skills")
        installed.append(str(skill_dir))
        if not args.no_hooks:
            hooks_dir = _install_hook_scripts(claude_root / "hooks")
            installed.append(str(hooks_dir))

    if args.target in ("codex", "both"):
        codex_dir = _default_codex_dir(home)
        skill_dir = _copy_skill(codex_dir)
        installed.append(str(skill_dir))

    summary: dict[str, object] = {
        "target": args.target,
        "installed": installed,
        "scope": "user-global (skill + hook scripts only, no settings.json change)",
        "rule": "hook 配置是项目级, 由 prd_distill.py init 写到 <project>/.claude/settings.json",
    }
    if args.target in ("codex", "both"):
        summary["codex_note"] = "Codex 没 hook 事件机制, harvest_prd_prompt.py 装入也跑不起来; PRD / 合同提炼要靠对话里显式告诉 AI"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
