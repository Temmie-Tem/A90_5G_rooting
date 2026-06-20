"""Static checks for V2984 inputcaps touch diagnostics live runner."""

from __future__ import annotations

from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "workspace/public/src/scripts/revalidation/native_inputcaps_touch_diag_live_handoff_v2984.py"


class TestNativeInputcapsTouchDiagLiveV2984(unittest.TestCase):
    def test_runner_targets_v2983_candidate(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V2984"', text)
        self.assertIn('CANDIDATE_VERSION = "0.10.62"', text)
        self.assertIn('CANDIDATE_TAG = "v2983-inputcaps-touch-diag"', text)
        self.assertIn('boot_linux_v2983_inputcaps_touch_diag.img', text)
        self.assertIn('3edb059b7887cd0577a98bc28b41f1ce8c643b4234b7d3100896bb27aa86d226', text)

    def test_runner_collects_read_only_inputcaps(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('["inputscan"]', text)
        self.assertIn('["inputcaps", event_name]', text)
        self.assertIn('DEFAULT_EVENTS = ("event6", "event8")', text)
        self.assertIn('parse_inputcaps', text)
        self.assertIn('runtime_status values', text)
        self.assertIn('not explained by missing capabilities', text)
        self.assertNotIn('["readinput"', text)
        self.assertNotIn('sendevent', text)
        self.assertNotIn('EVIOCGRAB', text)

    def test_runner_preserves_flash_and_rollback_boundaries(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('native_init_flash.py', text)
        self.assertIn('rollback to v2321 and verify selftest fail=0', text)
        self.assertIn('no readinput event stream, no input injection, no keymap changes', text)
        self.assertIn('base.rollback_v2321', text)


if __name__ == "__main__":
    unittest.main()
