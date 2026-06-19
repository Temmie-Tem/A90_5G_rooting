"""Tests for V2854 audio productization marker refresh live handoff wrapper."""

from __future__ import annotations

import importlib
import unittest

v2854 = importlib.import_module("native_audio_productization_marker_refresh_live_handoff_v2854")


class NativeAudioProductizationMarkerRefreshLiveHandoffV2854Test(unittest.TestCase):
    def test_wrapper_targets_v2853_candidate(self) -> None:
        self.assertEqual(v2854.CYCLE, "V2854")
        self.assertEqual(v2854.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2854.CANDIDATE_TAG, "v2853-audio-productization-marker-refresh")
        self.assertIn("v2853-audio-productization-marker-refresh", str(v2854.BUILD_MANIFEST))
        self.assertIn("boot_linux_v2853_audio_productization_marker_refresh.img", str(v2854.CANDIDATE_IMAGE))

    def test_refreshed_productization_markers_are_required(self) -> None:
        markers = "\n".join(v2854.REQUIRED_AUDIO_STATUS_MARKERS)
        for required in [
            "audio.status.productization.latest_run=V2852",
            "audio.status.productization.latest_version=0.10.16",
            "audio.status.productization.latest_tag=v2851-audio-changelog-productization",
            "audio.status.feature.changelog=1",
            "audio.status.feature.changelog.validation_run=V2852",
            "audio.status.feature.changelog.screenapp_count=2",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, markers)

    def test_configure_runner_sets_audio_status_and_about_changelog_checks(self) -> None:
        v2854.configure_runner()
        self.assertEqual(v2854.runner.CYCLE, "V2854")
        self.assertEqual(v2854.runner.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2854.runner.SCREENAPP_COMMAND, ["screenapp", "audio-status"])
        self.assertEqual(v2854.runner.EXTRA_MARKER_STEPS[0]["command"], ["screenapp", "about-changelog"])
        self.assertIn("audio.status.feature.changelog.validation_run=V2852", "\n".join(v2854.runner.REQUIRED_AUDIO_STATUS_MARKERS))

    def test_report_mentions_marker_refresh_validation(self) -> None:
        report = v2854.render_report({
            "decision": "v2854-test",
            "candidate_sha256": "9" * 64,
            "candidate_version_ok": True,
            "rollback_attempted": True,
            "rollback_recovery_fallback_used": False,
            "rollback_version_ok": True,
            "rollback_selftest_fail0": True,
            "audio_status_markers": {"ok": True, "count": 33, "required": 33, "missing": []},
            "selftest_markers": {"ok": True, "count": 8, "required": 8, "missing": []},
            "screenapp_markers": {"ok": True, "count": 6, "required": 6, "missing": []},
            "extra_markers": {"candidate-screenapp-about-changelog": {"ok": True, "count": 6, "required": 6, "missing": []}},
        })
        self.assertIn("V2854", report)
        self.assertIn("V2852 live-validated changelog/about evidence", report)
        self.assertIn("screenapp about-changelog", report)
        self.assertIn("no ADSP boot", report)
        self.assertIn("No forbidden partitions", report)


if __name__ == "__main__":
    unittest.main()
