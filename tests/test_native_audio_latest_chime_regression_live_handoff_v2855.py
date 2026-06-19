"""Tests for V2855 latest-candidate audio chime regression wrapper."""

from __future__ import annotations

import importlib
import unittest

v2855 = importlib.import_module("native_audio_latest_chime_regression_live_handoff_v2855")


class NativeAudioLatestChimeRegressionLiveHandoffV2855Test(unittest.TestCase):
    def test_wrapper_targets_latest_productization_candidate(self) -> None:
        self.assertEqual(v2855.CYCLE, "V2855")
        self.assertEqual(v2855.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2855.CANDIDATE_TAG, "v2853-audio-productization-marker-refresh")
        self.assertIn("v2853-audio-productization-marker-refresh", str(v2855.BUILD_MANIFEST))
        self.assertIn("boot_linux_v2853_audio_productization_marker_refresh.img", str(v2855.CANDIDATE_IMAGE))

    def test_configure_retargets_shared_runner(self) -> None:
        v2855.configure_runner_for_v2855()

        self.assertEqual(v2855.runner.CYCLE, "V2855")
        self.assertEqual(v2855.runner.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2855.runner.CANDIDATE_TAG, "v2853-audio-productization-marker-refresh")
        self.assertEqual(v2855.runner.base.CANDIDATE_IMAGE, v2855.CANDIDATE_IMAGE)
        self.assertEqual(v2855.runner.base.CANDIDATE_VERSION, "0.10.17")
        self.assertEqual(v2855.runner.DEFAULT_REMOTE_MANIFEST, v2855.v2844.BUNDLED_REMOTE_MANIFEST)

    def test_reuses_bounded_chime_command(self) -> None:
        args = v2855.runner.parse_args(["--dry-run"])
        command = v2855.runner.play_command(args)

        self.assertEqual(command[:2], ["audio", "chime"])
        self.assertIn("--execute", command)
        self.assertIn("--amplitude-milli", command)
        self.assertIn("80", command)
        self.assertIn("--duration-ms", command)
        self.assertIn("1200", command)

    def test_dry_run_scope_stays_no_host_deploy(self) -> None:
        args = v2855.runner.parse_args(["--dry-run"])
        state = v2855.runner.preflight_state()
        payload = v2855.runner.dry_run_payload(args, state)

        self.assertEqual(payload["commands"]["audio_chime"][:2], ["audio", "chime"])
        self.assertEqual(payload["commands"]["host_artifact_deploy_count"], 0)
        self.assertIn("no-host-deploy", state["discriminator"])
        self.assertFalse(state["host_artifact_deploy_required"])
        self.assertTrue(state["host_artifact_deploy_forbidden_in_this_unit"])


if __name__ == "__main__":
    unittest.main()
