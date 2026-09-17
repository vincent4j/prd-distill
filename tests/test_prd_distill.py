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
    def test_scan_reports_context_keeper_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["scan"], Path(tmp))
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["context_keeper"]["installed"])
        self.assertEqual(payload["context_keeper"]["layout"], "missing")
        self.assertEqual(payload["context_keeper"]["files"], {})

    def test_scan_reports_new_context_keeper_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ck = root / "context-keeper"
            (ck / "plans").mkdir(parents=True)
            (ck / "worklogs").mkdir(parents=True)
            (ck / "memory-keeper.md").write_text("# memory\n", encoding="utf-8")
            (ck / "plans" / "2026-09-17-示例.md").write_text("# plan\n", encoding="utf-8")
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["context_keeper"]["installed"])
        self.assertEqual(payload["context_keeper"]["layout"], "new")
        self.assertIn("context-keeper/memory-keeper.md", payload["context_keeper"]["files"]["memory_keeper"])
        self.assertEqual(
            payload["context_keeper"]["files"]["plans"],
            ["context-keeper/plans/2026-09-17-示例.md"],
        )
        self.assertEqual(payload["context_keeper"]["files"]["worklogs"], [])
        self.assertEqual(payload["legacy_history"]["plans"], [])

    def test_scan_reports_legacy_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "plans").mkdir(parents=True)
            (root / "docs" / "memory-keeper.md").write_text("# old memory\n", encoding="utf-8")
            (root / "docs" / "plans" / "2026-09-17-旧碎片.md").write_text("# plan\n", encoding="utf-8")
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["context_keeper"]["layout"], "missing")
        self.assertEqual(
            payload["legacy_history"]["plans"],
            ["docs/plans/2026-09-17-旧碎片.md"],
        )
        self.assertIn("docs/memory-keeper.md", payload["legacy_history"]["memory_keeper"])

    def test_scan_reports_mixed_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ck = root / "context-keeper"
            (ck / "plans").mkdir(parents=True)
            (root / "docs" / "plans").mkdir(parents=True)
            (root / "docs" / "plans" / "2026-09-17-旧.md").write_text(
                "# legacy\n", encoding="utf-8"
            )
            result = _run(["scan"], root)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["context_keeper"]["installed"])
        self.assertEqual(payload["context_keeper"]["layout"], "mixed")
        self.assertNotEqual(payload["legacy_history"]["plans"], [])


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


if __name__ == "__main__":
    unittest.main()
