"""Tests for the V2821 audio selftest policy live wrapper."""

from __future__ import annotations

import importlib
import unittest

v2821 = importlib.import_module("native_audio_selftest_policy_live_handoff_v2821")


class NativeAudioSelftestPolicyLiveV2821Test(unittest.TestCase):
    def test_wrapper_pins_v2820_candidate_constants(self) -> None:
        self.assertEqual(v2821.CYCLE, "V2821")
        self.assertEqual(v2821.CANDIDATE_VERSION, "0.10.2")
        self.assertEqual(v2821.CANDIDATE_TAG, "v2820-audio-selftest-policy")
        self.assertIn("boot_linux_v2820_audio_selftest_policy.img", str(v2821.CANDIDATE_IMAGE))
        self.assertIn("NATIVE_INIT_V2821_AUDIO_SELFTEST_POLICY_LIVE", str(v2821.REPORT_PATH))

    def test_configure_runner_sets_v2821_globals(self) -> None:
        v2821.configure_runner()
        self.assertEqual(v2821.runner.CYCLE, "V2821")
        self.assertEqual(v2821.runner.CANDIDATE_VERSION, "0.10.2")
        self.assertIn("boot_linux_v2820_audio_selftest_policy.img", str(v2821.runner.CANDIDATE_IMAGE))
        self.assertIn("PASS      audio", "\n".join(v2821.runner.REQUIRED_SELFTEST_MARKERS))

    def test_selftest_markers_match_actual_verbose_row_shape(self) -> None:
        markers = "\n".join(v2821.REQUIRED_SELFTEST_MARKERS)
        self.assertIn("PASS      audio", markers)
        self.assertIn("boost=blocked", markers)
        self.assertNotIn("selftest audio:", markers)

    def test_report_mentions_no_runtime_audio_writes(self) -> None:
        report = v2821.render_report({
            "decision": "v2821-test",
            "candidate_sha256": "7" * 64,
            "audio_status_markers": {"ok": True, "count": 16, "required": 16, "missing": []},
            "selftest_markers": {"ok": True, "count": 8, "required": 8, "missing": []},
        })
        self.assertIn("V2821", report)
        self.assertIn("0.10.2", report)
        self.assertIn("no ADSP boot", report)
        self.assertIn("No forbidden partitions", report)


if __name__ == "__main__":
    unittest.main()
