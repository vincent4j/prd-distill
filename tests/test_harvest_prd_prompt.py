import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).parents[1] / "skills" / "prd-distill" / "scripts" / "claude_hooks" / "harvest_prd_prompt.py"


def _run_hook(prompt: str, root: Path) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"prompt": prompt})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        env={"CLAUDE_PROJECT_DIR": str(root)},
    )


class HarvestPrdPromptTests(unittest.TestCase):
    def test_strong_constraint_writes_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            inbox = root / "docs" / "prd" / "inbox"
            self.assertTrue(inbox.exists())
            fragments = list(inbox.glob("*-requirement-fragments.md"))
            self.assertEqual(len(fragments), 1)
            self.assertIn("必须", fragments[0].read_text(encoding="utf-8"))

    def test_pure_history_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("这个以前解决过吗？", root)
            self.assertEqual(result.returncode, 0)
            inbox = root / "docs" / "prd" / "inbox"
            self.assertFalse(inbox.exists())

    def test_reproduce_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("为什么又复现了？", root)
            self.assertEqual(result.returncode, 0)
            inbox = root / "docs" / "prd" / "inbox"
            self.assertFalse(inbox.exists())

    def test_mixed_message_only_writes_when_current_requirement_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook(
                "这个又复现了，以后重试前必须检查幂等键", root
            )
            self.assertEqual(result.returncode, 0)
            inbox = root / "docs" / "prd" / "inbox"
            self.assertTrue(inbox.exists())
            fragments = list(inbox.glob("*-requirement-fragments.md"))
            self.assertEqual(len(fragments), 1)
            self.assertIn("必须", fragments[0].read_text(encoding="utf-8"))

    def test_no_trigger_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("我们继续做下一个模块", root)
            self.assertEqual(result.returncode, 0)
            inbox = root / "docs" / "prd" / "inbox"
            self.assertFalse(inbox.exists())


if __name__ == "__main__":
    unittest.main()
