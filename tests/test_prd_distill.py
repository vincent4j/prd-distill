import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "prd-distill" / "scripts" / "prd_distill.py"


class CheckCommandTests(unittest.TestCase):
    def run_check(self, root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
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


if __name__ == "__main__":
    unittest.main()
