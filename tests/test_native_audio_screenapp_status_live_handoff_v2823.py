"""Tests for the V2823 audio screenapp status live wrapper."""

from __future__ import annotations

import importlib
import unittest

v2823 = importlib.import_module("native_audio_screenapp_status_live_handoff_v2823")


class NativeAudioScreenappStatusLiveV2823Test(unittest.TestCase):
    def test_wrapper_pins_v2822_candidate_constants(self) -> None:
        self.assertEqual(v2823.CYCLE, "V2823")
        self.assertEqual(v2823.CANDIDATE_VERSION, "0.10.3")
        self.assertEqual(v2823.CANDIDATE_TAG, "v2822-audio-screenapp-status")
        self.assertIn("boot_linux_v2822_audio_screenapp_status.img", str(v2823.CANDIDATE_IMAGE))
        self.assertIn("NATIVE_INIT_V2823_AUDIO_SCREENAPP_STATUS_LIVE", str(v2823.REPORT_PATH))

    def test_configure_runner_sets_screenapp_check(self) -> None:
        v2823.configure_runner()
        self.assertEqual(v2823.runner.CYCLE, "V2823")
        self.assertEqual(v2823.runner.CANDIDATE_VERSION, "0.10.3")
        self.assertEqual(v2823.runner.SCREENAPP_COMMAND, ["screenapp", "audio-status"])
        markers = "\n".join(v2823.runner.REQUIRED_SCREENAPP_MARKERS)
        self.assertIn("screenapp.app=audio-status", markers)
        self.assertIn("screenapp.presented=1", markers)

    def test_report_mentions_display_only_boundary(self) -> None:
        report = v2823.render_report({
            "decision": "v2823-test",
            "candidate_sha256": "9" * 64,
            "audio_status_markers": {"ok": True, "count": 16, "required": 16, "missing": []},
            "selftest_markers": {"ok": True, "count": 8, "required": 8, "missing": []},
            "screenapp_markers": {"ok": True, "count": 6, "required": 6, "missing": []},
        })
        self.assertIn("V2823", report)
        self.assertIn("screenapp audio-status", report)
        self.assertIn("display/KMS only", report)
        self.assertIn("No forbidden partitions", report)


if __name__ == "__main__":
    unittest.main()
