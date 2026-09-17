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


def _inbox_files(root: Path) -> list[Path]:
    inbox = root / "docs" / "prd" / "inbox"
    if not inbox.exists():
        return []
    return list(inbox.glob("*-requirement-fragments.md"))


class HarvestPrdPromptTests(unittest.TestCase):
    def test_strong_constraint_writes_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            fragments = _inbox_files(root)
            self.assertEqual(len(fragments), 1)
            self.assertIn("必须", fragments[0].read_text(encoding="utf-8"))

    def test_pure_history_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("这个以前解决过吗？", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_reproduce_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("为什么又复现了？", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_history_query_last_time_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("查一下上次怎么处理的。", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_history_remember_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("我记得之前成功过，你先找原文。", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_mixed_message_with_history_hint_is_suppressed(self) -> None:
        # follow-up 4.2 例子: "这个又复现了，以后重试前必须检查幂等键"
        # 含"又复现"历史词, 按"见到历史词完全不写"策略抑制, 由 Agent 显式提炼。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook(
                "这个又复现了，以后重试前必须检查幂等键", root
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_mixed_message_with_history_omission_is_suppressed(self) -> None:
        # follow-up 4.2 例子: "上次遗漏了整体复盘, 从现在开始整组验收后必须..."
        # 含"上次遗漏"历史词, 抑制。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook(
                "上次遗漏了整体复盘，从现在开始整组验收后必须检查是否已经交付",
                root,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_no_trigger_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("我们继续做下一个模块", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])


if __name__ == "__main__":
    unittest.main()
