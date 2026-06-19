"""Tests for V2856 latest-candidate audio stop-execute regression wrapper."""

from __future__ import annotations

import importlib
import unittest

v2856 = importlib.import_module("native_audio_latest_stop_execute_regression_live_handoff_v2856")


class NativeAudioLatestStopExecuteRegressionLiveHandoffV2856Test(unittest.TestCase):
    def test_wrapper_targets_latest_productization_candidate(self) -> None:
        self.assertEqual(v2856.CYCLE, "V2856")
        self.assertEqual(v2856.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2856.CANDIDATE_TAG, "v2853-audio-productization-marker-refresh")
        self.assertIn("v2853-audio-productization-marker-refresh", str(v2856.BUILD_MANIFEST))
        self.assertIn("boot_linux_v2853_audio_productization_marker_refresh.img", str(v2856.CANDIDATE_IMAGE))

    def test_configure_retargets_shared_runner(self) -> None:
        v2856.configure_runner_for_v2856()

        self.assertEqual(v2856.runner.CYCLE, "V2856")
        self.assertEqual(v2856.runner.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2856.runner.CANDIDATE_TAG, "v2853-audio-productization-marker-refresh")
        self.assertEqual(v2856.runner.base.CANDIDATE_IMAGE, v2856.CANDIDATE_IMAGE)
        self.assertEqual(v2856.runner.base.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2856.runner.DEFAULT_REMOTE_MANIFEST, v2856.v2848.BUNDLED_REMOTE_MANIFEST)

    def test_dry_run_scope_stays_single_stop_no_deploy(self) -> None:
        args = v2856.runner.parse_args(["--dry-run"])
        state = v2856.runner.preflight_state()
        payload = v2856.runner.dry_run_payload(args, state)

        self.assertEqual(
            payload["commands"]["audio_stop_execute"],
            ["audio", "stop", "internal-speaker-safe", "--execute"],
        )
        self.assertEqual(payload["commands"]["host_artifact_deploy_count"], 0)
        self.assertIn("audio-stop-execute-bounded-core-route-reset", state["discriminator"])
        self.assertFalse(state["host_artifact_deploy_required"])
        self.assertTrue(state["host_artifact_deploy_forbidden_in_this_unit"])

    def test_reuses_v2848_stop_classifier(self) -> None:
        good = "\n".join([
            "audio.stop.execute_supported=1",
            "audio.stop.execute_requested=1",
            "audio.stop.playback_stop_reason=no-active-pcm-handle",
            "audio.stop.setcal_deallocate_reason=no-active-setcal-session",
            "audio.stop.route_write_attempted=1",
            "audio.stop.ioctl_attempted=1",
            "audio.route.mode=reset",
            "audio.route.layer=core",
            "audio.route.write_attempted=1",
            "audio.route.write_done count=8 layer=core mode=reset",
            "audio.stop.route_reset_rc=0",
            "audio.stop.done=1 rc=0",
        ])

        self.assertTrue(v2856.v2848.classify_stop_output(good, 0)["pass"])
        self.assertFalse(v2856.v2848.classify_stop_output(good + "\naudio.route.write_failed control=x", 0)["pass"])


if __name__ == "__main__":
    unittest.main()
