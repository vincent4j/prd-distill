import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "prd-distill" / "scripts" / "prd_distill.py"


def _run(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


class CheckCommandTests(unittest.TestCase):
    def run_check(self, root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = _run(["check"], root)
        return result, json.loads(result.stdout)

    def test_uninitialized_project_is_explicit_and_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, payload = self.run_check(Path(tmp))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "not_initialized")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["warnings"], [])

    def test_partial_prd_structure_still_warns_about_missing_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "prd").mkdir(parents=True)
            result, payload = self.run_check(root)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "initialized")
        self.assertIn("缺少 docs/prd/README.md 模块索引", payload["warnings"])
        self.assertIn("缺少 docs/prd/contracts/README.md 合同索引", payload["warnings"])

    def test_complete_empty_prd_structure_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contracts = root / "docs" / "prd" / "contracts"
            contracts.mkdir(parents=True)
            (root / "docs" / "prd" / "README.md").write_text("# PRD\n", encoding="utf-8")
            (contracts / "README.md").write_text("# Contracts\n", encoding="utf-8")
            result, payload = self.run_check(root)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "initialized")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["warnings"], [])


class ScanCommandTests(unittest.TestCase):
    def test_scan_finds_memory_keeper_regardless_of_store_path(self) -> None:
        """scan 全项目扫描 memory-keeper.md, 不假设 context-keeper 存储目录。

        用户在 init 时可指定任意目录; 不管默认路径还是用户自定义路径,
        只要叫 memory-keeper.md 就应该被发现。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 三个不同位置的 memory-keeper.md:
            # 1. 老版默认 context-keeper/
            (root / "context-keeper").mkdir(parents=True)
            (root / "context-keeper" / "memory-keeper.md").write_text(
                "# default\n", encoding="utf-8"
            )
            # 2. 新版默认 docs/context-keeper/
            (root / "docs" / "context-keeper" / "plans").mkdir(parents=True)
            (root / "docs" / "context-keeper" / "memory-keeper.md").write_text(
                "# new\n", encoding="utf-8"
            )
            # 3. 用户自定义 notes/ck/
            (root / "notes" / "ck").mkdir(parents=True)
            (root / "notes" / "ck" / "memory-keeper.md").write_text(
                "# custom\n", encoding="utf-8"
            )
            # 4. 老版 v0.x 路径 docs/memory-keeper.md
            (root / "docs" / "memory-keeper.md").write_text(
                "# legacy\n", encoding="utf-8"
            )
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        files = payload["context_keeper"]["memory_keeper_files"]
        self.assertEqual(
            files,
            [
                "context-keeper/memory-keeper.md",
                "docs/context-keeper/memory-keeper.md",
                "docs/memory-keeper.md",
                "notes/ck/memory-keeper.md",
            ],
        )

    def test_scan_reports_empty_when_no_memory_keeper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["scan"], Path(tmp))
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["context_keeper"]["memory_keeper_files"], [])

    def test_scan_reports_legacy_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "plans").mkdir(parents=True)
            (root / "docs" / "plans" / "2026-09-17-旧碎片.md").write_text("# plan\n", encoding="utf-8")
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["legacy_history"]["plans"],
            ["docs/plans/2026-09-17-旧碎片.md"],
        )


class LookupCommandTests(unittest.TestCase):
    def test_lookup_default_ignores_context_keeper_and_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prd_dir = root / "docs" / "prd" / "contracts"
            prd_dir.mkdir(parents=True)
            (root / "docs" / "prd" / "README.md").write_text(
                "# PRD\n\n## 模块列表\n\n| MOD | | [mod.md](mod.md) |\n",
                encoding="utf-8",
            )
            (prd_dir / "README.md").write_text("# Contracts\n", encoding="utf-8")
            (prd_dir / "mod.md").write_text(
                "## 关联 PRD\n\n## 合同列表\n\n### MOD-CHECK-001：命中关键词\n",
                encoding="utf-8",
            )
            ck = root / "context-keeper"
            (ck / "plans").mkdir(parents=True)
            (ck / "plans" / "context-keeper-命中关键词.md").write_text(
                "## 用户需求\n\n命中关键词\n", encoding="utf-8"
            )
            (root / "docs" / "plans").mkdir(parents=True)
            (root / "docs" / "plans" / "legacy-命中关键词.md").write_text(
                "# legacy\n命中关键词\n", encoding="utf-8"
            )
            result = _run(["lookup", "--query", "命中关键词"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        searched = {record["file"] for record in payload["matches"]}
        self.assertNotIn("context-keeper/plans/context-keeper-命中关键词.md", searched)
        self.assertNotIn("docs/plans/legacy-命中关键词.md", searched)
        self.assertIn("docs/prd/contracts/mod.md", searched)
        self.assertNotIn("include_history", payload)

    def test_lookup_rejects_include_history_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(
                ["lookup", "--query", "x", "--include-history"], Path(tmp)
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_lookup_evidence_marks_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ck = root / "context-keeper" / "plans"
            ck.mkdir(parents=True)
            evidence = ck / "context-keeper-命中关键词.md"
            evidence.write_text("## 用户需求\n\n命中关键词\n", encoding="utf-8")
            result = _run(
                ["lookup", "--query", "命中关键词",
                 "--evidence", str(evidence)],
                root,
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        types = {m["file"]: m["type"] for m in payload["matches"]}
        self.assertEqual(
            types.get("context-keeper/plans/context-keeper-命中关键词.md"),
            "evidence",
        )
        self.assertEqual(
            payload["evidence_files"],
            ["context-keeper/plans/context-keeper-命中关键词.md"],
        )

    def test_lookup_evidence_accepts_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans = root / "context-keeper" / "plans"
            plans.mkdir(parents=True)
            a = plans / "a.md"
            b = plans / "b.md"
            a.write_text("# a 命中关键词\n", encoding="utf-8")
            b.write_text("# b 命中关键词\n", encoding="utf-8")
            result = _run(
                ["lookup", "--query", "命中关键词",
                 "--evidence", str(a), "--evidence", str(b)],
                root,
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(
            sorted(payload["evidence_files"]),
            ["context-keeper/plans/a.md", "context-keeper/plans/b.md"],
        )
        types = {m["file"]: m["type"] for m in payload["matches"]}
        for name in ("context-keeper/plans/a.md", "context-keeper/plans/b.md"):
            self.assertEqual(types.get(name), "evidence")

    def test_lookup_evidence_missing_file_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "no-such.md"
            result = _run(
                ["lookup", "--query", "x", "--evidence", str(missing)], root
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("不存在", result.stderr)

    def test_lookup_evidence_outside_project_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, \
                tempfile.TemporaryDirectory() as outside_dir:
            outside = Path(outside_dir) / "outside.md"
            outside.write_text("x", encoding="utf-8")
            result = _run(
                ["lookup", "--query", "x", "--evidence", str(outside)],
                Path(project_root),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("超出项目根", result.stderr)

    def test_lookup_evidence_zero_hits_returns_no_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans = root / "context-keeper" / "plans"
            plans.mkdir(parents=True)
            empty = plans / "empty.md"
            empty.write_text("# no relevant terms here\n", encoding="utf-8")
            result = _run(
                ["lookup", "--query", "不存在的关键词",
                 "--evidence", str(empty)],
                root,
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["matches"], [])


class StatusCommandTests(unittest.TestCase):
    def test_status_reports_disabled_for_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["status"], Path(tmp))
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["prd_distill_enabled"])

    def test_status_reports_enabled_when_init_ran(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "prd").mkdir(parents=True)
            (root / "docs" / "prd" / "README.md").write_text("# PRD\n", encoding="utf-8")
            result = _run(["status"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["prd_distill_enabled"])


class InitCommandTests(unittest.TestCase):
    def test_init_default_only_creates_claude_md(self) -> None:
        """默认 --bridge-target=claude: 只创建 CLAUDE.md, 不创建 AGENTS.md,
        避免只用 Claude Code 的项目根多一个冗余文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init"], root)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertFalse((root / "AGENTS.md").exists())

    def test_init_with_bridge_target_agents_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init", "--bridge-target", "agents"], root)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertFalse((root / "CLAUDE.md").exists())

    def test_init_with_bridge_target_both(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init", "--bridge-target", "both"], root)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "CLAUDE.md").exists())

    def test_init_with_bridge_target_existing_follows_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# pre\n", encoding="utf-8")
            result = _run(["init", "--bridge-target", "existing"], root)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertIn("prd-distill:start", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertFalse((root / "CLAUDE.md").exists())

    def test_init_does_not_create_inbox_directories(self) -> None:
        """inbox 按需创建: init 不预创建空目录, 由 new-contract /
        harvest hook 在首次写入时调用 mkdir 创建。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init"], root)
            self.assertEqual(result.returncode, 0)
            self.assertFalse((root / "docs" / "prd" / "inbox").exists())
            self.assertFalse((root / "docs" / "prd" / "contracts" / "inbox").exists())

    def test_init_rejects_unknown_bridge_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init", "--bridge-target", "bogus"], root)
            self.assertNotEqual(result.returncode, 0)

    def test_init_creates_project_level_hook_settings(self) -> None:
        """init 启用本项目: 写 <project>/.claude/settings.json 的 hook 配置。
        未启用的项目没有这个文件, Claude Code 不调用 hook, docs/prd/
        也不会被任何路径创建。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["init"], root)
            self.assertEqual(result.returncode, 0)
            settings = root / ".claude" / "settings.json"
            self.assertTrue(settings.exists())
            payload = json.loads(settings.read_text(encoding="utf-8"))
            self.assertIn("hooks", payload)
            user_prompt = payload["hooks"]["UserPromptSubmit"]
            self.assertTrue(
                any(
                    "harvest_prd_prompt.py" in hook.get("command", "")
                    for group in user_prompt
                    for hook in group.get("hooks", [])
                )
            )
            pre_tool = payload["hooks"]["PreToolUse"]
            self.assertTrue(
                any(
                    "guard_prd_commit.py" in hook.get("command", "")
                    for group in pre_tool
                    for hook in group.get("hooks", [])
                )
            )

    def test_install_hooks_writes_only_project_settings(self) -> None:
        """install-hooks 命令单独跑也只写项目级 settings.json, 不动 ~/.claude/。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["install-hooks"], root)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / ".claude" / "settings.json").exists())

    def test_install_hooks_is_idempotent(self) -> None:
        """重复跑 install-hooks 不重复追加: 用 _remove_hook_entry 去重。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run(["install-hooks"], root)
            _run(["install-hooks"], root)
            payload = json.loads(
                (root / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            user_prompt = payload["hooks"]["UserPromptSubmit"]
            harvest_count = sum(
                1
                for group in user_prompt
                for hook in group.get("hooks", [])
                if "harvest_prd_prompt.py" in hook.get("command", "")
            )
            self.assertEqual(harvest_count, 1)


class UninitializedProjectTests(unittest.TestCase):
    """未启用项目压根不应该有任何 PRD Distill 产物。

    init 之前:
    - 没有 docs/prd/ 目录
    - 没有 .claude/settings.json 文件
    - Claude Code 因此不调用 hook, 不会创建 PRD 目录
    """

    def test_uninit_project_has_no_prd_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse((root / "docs" / "prd").exists())
            self.assertFalse((root / ".claude" / "settings.json").exists())

    def test_scan_on_uninit_project_reports_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["prd"], [])
        self.assertEqual(payload["contracts"], [])


class ContextKeeperWriteProtectionTests(unittest.TestCase):
    """follow-up 4.5 / 5.5: PRD Distill 任何命令和 hook 不得修改 context-keeper/。

    不假设 context-keeper 的具体路径(用户可自定义存储目录), 改为扫描
    项目根下所有 .md 文件指纹, 跑遍 PRD Distill 命令和 hook 后断言
    docs/prd/ 和 docs/prd/contracts/ 之外的任何 .md 文件指纹不变。
    """

    HOOK = SCRIPT.parent / "claude_hooks" / "harvest_prd_prompt.py"

    PRD_OWNED = ("docs/prd/", "AGENTS.md", "CLAUDE.md")

    def _fingerprint(self, root: Path) -> dict[str, str]:
        """扫描 root 下所有 .md 文件, 排除 PRD Distill 自己应当写入的目录。"""
        result: dict[str, str] = {}
        for path in sorted(root.rglob("*.md")):
            rel = str(path.relative_to(root))
            if any(rel.startswith(prefix) for prefix in self.PRD_OWNED):
                continue
            result[rel] = path.read_bytes().decode("utf-8", errors="replace")
        return result

    def test_all_commands_and_hooks_leave_non_prd_markdown_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 用户自定义的 context-keeper 路径(非默认位置)
            ck = root / "notes" / "ck"
            (ck / "plans").mkdir(parents=True)
            (ck / "worklogs").mkdir(parents=True)
            (ck / "memory-keeper.md").write_text(
                "# memory\n\n历史经验: 必须检查幂等键\n", encoding="utf-8"
            )
            (ck / "plans" / "2026-09-17-示例.md").write_text(
                "# plan\n用户要求: 字段必须来自权威数据源\n", encoding="utf-8"
            )
            # 默认位置的 context-keeper 也放一份
            ck_default = root / "context-keeper" / "plans"
            ck_default.mkdir(parents=True)
            (ck_default / "2026-09-17-default.md").write_text(
                "# default\n", encoding="utf-8"
            )
            # 用户自定义的另一个目录
            user_dir = root / "memory"
            user_dir.mkdir()
            (user_dir / "notes.md").write_text("# user notes\n", encoding="utf-8")

            before = self._fingerprint(root)
            self.assertNotEqual(before, {})

            commands: list[list[str]] = [
                ["init", "--root", str(root)],
                ["install-bridge", "--root", str(root)],
                ["scan", "--root", str(root)],
                ["lookup", "--root", str(root), "--query", "必须",
                 "--evidence", str(ck / "memory-keeper.md")],
                ["check", "--root", str(root)],
                ["new-contract", "--root", str(root),
                 "--module", "test", "--title", "示例合同",
                 "--contract", "必须"],
                ["pending", "--root", str(root)],
            ]
            for cmd in commands:
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), *cmd],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(
                    result.returncode, 0,
                    f"command {cmd[0]} failed: {result.stderr}",
                )

            hook_payload = json.dumps({"prompt": "这个字段必须来自权威数据源"})
            hook_result = subprocess.run(
                [sys.executable, str(self.HOOK)],
                input=hook_payload,
                capture_output=True, text=True, check=False,
                env={"CLAUDE_PROJECT_DIR": str(root)},
            )
            self.assertEqual(hook_result.returncode, 0, hook_result.stderr)

            after = self._fingerprint(root)
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
