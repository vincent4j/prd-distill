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


def _enable_prd_distill(root: Path) -> None:
    """模拟 init 已运行: 创建 docs/prd/README.md 作为启用标记。"""
    (root / "docs" / "prd" / "inbox").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "prd" / "README.md").write_text("# PRD\n", encoding="utf-8")


class HarvestPrdPromptTests(unittest.TestCase):
    def test_strong_constraint_writes_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            fragments = _inbox_files(root)
            self.assertEqual(len(fragments), 1)
            self.assertIn("必须", fragments[0].read_text(encoding="utf-8"))

    def test_pure_history_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("这个以前解决过吗？", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_reproduce_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("为什么又复现了？", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_history_query_last_time_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("查一下上次怎么处理的。", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_history_remember_signal_does_not_write_to_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("我记得之前成功过，你先找原文。", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_mixed_message_with_history_hint_is_suppressed(self) -> None:
        # follow-up 4.2 例子: "这个又复现了，以后重试前必须检查幂等键"
        # 含"又复现"历史词, 按"见到历史词完全不写"策略抑制, 由 Agent 显式提炼。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
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
            _enable_prd_distill(root)
            result = _run_hook(
                "上次遗漏了整体复盘，从现在开始整组验收后必须检查是否已经交付",
                root,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_no_trigger_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _enable_prd_distill(root)
            result = _run_hook("我们继续做下一个模块", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_prd_distill_source_root_skips_hook(self) -> None:
        """在 prd-distill 自身源码根下不写 inbox, 避免开发仓库被自己的
        hook 污染。判定: 项目根同时存在 skills/prd-distill/scripts/prd_distill.py
        与 tests/test_prd_distill.py。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "prd-distill" / "scripts").mkdir(parents=True)
            (root / "skills" / "prd-distill" / "scripts" / "prd_distill.py").write_text(
                "# placeholder\n", encoding="utf-8"
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_prd_distill.py").write_text(
                "# placeholder\n", encoding="utf-8"
            )
            _enable_prd_distill(root)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])

    def test_prd_distill_source_root_requires_both_markers(self) -> None:
        """只有 prd_distill.py 但缺 test_prd_distill.py 时, 不应误判为
        源码根: 避免用户把 skill 装到项目内 skills/ 时被错误跳过。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "prd-distill" / "scripts").mkdir(parents=True)
            (root / "skills" / "prd-distill" / "scripts" / "prd_distill.py").write_text(
                "# placeholder\n", encoding="utf-8"
            )
            _enable_prd_distill(root)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            fragments = _inbox_files(root)
            self.assertEqual(len(fragments), 1)

    def test_disabled_project_skips_hook(self) -> None:
        """未启用项目跳过 hook: docs/prd/README.md 不存在时, 即使消息含
        触发词也不写 inbox, 不创建 docs/。Agent 应通过 status 询问用户
        是否启用。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_inbox_files(root), [])
            self.assertFalse((root / "docs").exists())

    def test_disabled_then_enabled_writes_to_inbox(self) -> None:
        """未启用时跳过; 用户显式启用(init 创建 README.md)后,
        后续消息按规则写入 inbox。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_hook("这个字段必须来自权威数据源", root)
            self.assertEqual(_inbox_files(root), [])
            _enable_prd_distill(root)
            _run_hook("另一个字段必须来自权威数据源", root)
            fragments = _inbox_files(root)
            self.assertEqual(len(fragments), 1)
            self.assertNotIn("这个字段必须", fragments[0].read_text(encoding="utf-8"))
            self.assertIn("另一个字段必须", fragments[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
