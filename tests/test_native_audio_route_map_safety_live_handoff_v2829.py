"""Tests for the V2829 audio route-map safety-label live wrapper."""

from __future__ import annotations

import importlib
import json
import unittest

v2829 = importlib.import_module("native_audio_route_map_safety_live_handoff_v2829")


class NativeAudioRouteMapSafetyLiveV2829Test(unittest.TestCase):
    def test_wrapper_pins_v2828_candidate_constants(self) -> None:
        self.assertEqual(v2829.CYCLE, "V2829")
        self.assertEqual(v2829.CANDIDATE_VERSION, "0.10.6")
        self.assertEqual(v2829.CANDIDATE_TAG, "v2828-audio-route-map-safety")
        self.assertIn("boot_linux_v2828_audio_route_map_safety.img", str(v2829.CANDIDATE_IMAGE))
        self.assertIn("NATIVE_INIT_V2829_AUDIO_ROUTE_MAP_SAFETY_LIVE", str(v2829.REPORT_PATH))

    def test_configure_runner_sets_screenapp_map_check(self) -> None:
        v2829.configure_runner()
        self.assertEqual(v2829.runner.CYCLE, "V2829")
        self.assertEqual(v2829.runner.CANDIDATE_VERSION, "0.10.6")
        self.assertEqual(v2829.runner.CANDIDATE_TAG, "v2828-audio-route-map-safety")
        self.assertEqual(v2829.runner.SCREENAPP_COMMAND, ["screenapp", "audio-map"])
        markers = "\n".join(v2829.runner.REQUIRED_SCREENAPP_MARKERS)
        self.assertIn("screenapp.app=audio-map", markers)
        self.assertIn("screenapp.title=AUDIO ROUTE MAP", markers)
        self.assertIn("screenapp.presented=1", markers)

        dry = v2829.runner.dry_run({"candidate": {"sha256": "2" * 64}})
        rendered = json.dumps(dry["commands"], sort_keys=True)
        self.assertIn('["hide"]', rendered)
        self.assertIn('["screenapp", "audio-map"]', rendered)

    def test_report_mentions_safety_labels_and_display_only_boundary(self) -> None:
        report = v2829.render_report({
            "decision": "v2829-test",
            "candidate_sha256": "b" * 64,
            "audio_status_markers": {"ok": True, "count": 16, "required": 16, "missing": []},
            "selftest_markers": {"ok": True, "count": 8, "required": 8, "missing": []},
            "screenapp_markers": {"ok": True, "count": 6, "required": 6, "missing": []},
        })
        self.assertIn("V2829", report)
        self.assertIn("BOOST WRITE BLOCKED", report)
        self.assertIn("SP UNVERIFIED", report)
        self.assertIn("screenapp audio-map", report)
        self.assertIn("display/KMS only", report)
        self.assertIn("No forbidden partitions", report)


if __name__ == "__main__":
    unittest.main()
