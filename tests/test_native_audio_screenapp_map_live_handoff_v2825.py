"""Tests for the V2825 audio screenapp route-map live wrapper."""

from __future__ import annotations

import importlib
import json
import unittest

v2825 = importlib.import_module("native_audio_screenapp_map_live_handoff_v2825")


class NativeAudioScreenappMapLiveV2825Test(unittest.TestCase):
    def test_wrapper_pins_v2824_candidate_constants(self) -> None:
        self.assertEqual(v2825.CYCLE, "V2825")
        self.assertEqual(v2825.CANDIDATE_VERSION, "0.10.4")
        self.assertEqual(v2825.CANDIDATE_TAG, "v2824-audio-screenapp-map")
        self.assertIn("boot_linux_v2824_audio_screenapp_map.img", str(v2825.CANDIDATE_IMAGE))
        self.assertIn("NATIVE_INIT_V2825_AUDIO_SCREENAPP_MAP_LIVE", str(v2825.REPORT_PATH))

    def test_configure_runner_sets_screenapp_map_check(self) -> None:
        v2825.configure_runner()
        self.assertEqual(v2825.runner.CYCLE, "V2825")
        self.assertEqual(v2825.runner.CANDIDATE_VERSION, "0.10.4")
        self.assertEqual(v2825.runner.SCREENAPP_COMMAND, ["screenapp", "audio-map"])
        markers = "\n".join(v2825.runner.REQUIRED_SCREENAPP_MARKERS)
        self.assertIn("screenapp.app=audio-map", markers)
        self.assertIn("screenapp.title=AUDIO ROUTE MAP", markers)
        self.assertIn("screenapp.presented=1", markers)

        dry = v2825.runner.dry_run({"candidate": {"sha256": "2" * 64}})
        rendered = json.dumps(dry["commands"], sort_keys=True)
        self.assertIn('["hide"]', rendered)
        self.assertIn('["screenapp", "audio-map"]', rendered)

    def test_report_mentions_display_only_boundary(self) -> None:
        report = v2825.render_report({
            "decision": "v2825-test",
            "candidate_sha256": "b" * 64,
            "audio_status_markers": {"ok": True, "count": 16, "required": 16, "missing": []},
            "selftest_markers": {"ok": True, "count": 8, "required": 8, "missing": []},
            "screenapp_markers": {"ok": True, "count": 6, "required": 6, "missing": []},
        })
        self.assertIn("V2825", report)
        self.assertIn("screenapp audio-map", report)
        self.assertIn("display/KMS only", report)
        self.assertIn("No forbidden partitions", report)


if __name__ == "__main__":
    unittest.main()
