"""Static checks for V2982 native-bounded readinput live handoff."""

from __future__ import annotations

from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "workspace/public/src/scripts/revalidation/native_readinput_timeout_live_handoff_v2982.py"


class TestNativeReadinputTimeoutLiveV2982(unittest.TestCase):
    def test_runner_targets_v2981_timeout_image(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V2982"', text)
        self.assertIn('CANDIDATE_VERSION = "0.10.61"', text)
        self.assertIn('CANDIDATE_TAG = "v2981-readinput-timeout"', text)
        self.assertIn('boot_linux_v2981_readinput_timeout.img', text)
        self.assertIn('c5ca7f973823f1f4ca5fc63a9c4d6c19582f4af632531f2954459e2f8a827d98', text)

    def test_runner_uses_native_timeout_not_host_cancel(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('command = ["readinput", event, str(count), str(timeout_ms)]', text)
        self.assertIn('and state.get("timeout_ms", 0) > 0', text)
        self.assertIn('native readinput timeout returns ETIMEDOUT', text)
        self.assertIn('"candidate-hide-before-inputscan"', text)
        self.assertIn('"candidate-hide-before-readinput"', text)
        self.assertNotIn('cancel_sent', text)
        self.assertNotIn('sock.sendall(b"q', text)
        self.assertNotIn('sample_timeout', text)
        self.assertNotIn('cancel_timeout', text)

    def test_runner_keeps_safety_boundaries(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('rollback to v2321 and verify selftest fail=0', text)
        self.assertIn('no input injection, no keymap changes', text)
        self.assertIn('no Wi-Fi/audio/video playback/PMIC/backlight/GPIO/regulator/GDSC', text)
        self.assertNotIn('sendevent', text)
        self.assertNotIn('EVIOCGRAB', text)


if __name__ == "__main__":
    unittest.main()
