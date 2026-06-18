"""Tests for the V2725 corrected ACDB deploy plan with V2724 helper."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2725 = load_revalidation("native_audio_acdb_corrected_core39_replay_deploy_plan_v2725")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2725-test-"))
    defaults: dict[str, object] = {
        "v2636_manifest": v2725.v2721.DEFAULT_V2636_MANIFEST,
        "v2669_run": v2725.v2721.DEFAULT_V2669_RUN,
        "helper": v2725.DEFAULT_HELPER,
        "expected_helper_sha256": v2725.EXPECTED_HELPER_SHA256,
        "real_hal_run": v2725.v2721.DEFAULT_REAL_HAL_RUN,
        "build_root": root / "build",
        "manifest_path": root / "deploy-plan.json",
        "report_path": root / "report.md",
        "remote_dir": "/cache/a90-acdb-setcal-replay-v2725-test",
        "hold_sec": 10,
        "write_report": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class NativeAudioAcdbCorrectedCore39ReplayDeployPlanV2725(unittest.TestCase):
    def test_manifest_uses_v2724_helper_and_corrected_order(self) -> None:
        manifest = v2725.build_manifest(args())

        self.assertTrue(manifest["ok"], manifest.get("replay_blockers"))
        self.assertEqual(manifest["run_id"], "V2725")
        self.assertEqual(manifest["helper_contract"]["helper_sha256"], v2725.EXPECTED_HELPER_SHA256)
        self.assertEqual(manifest["helper_contract"]["expected_helper_sha256"], v2725.EXPECTED_HELPER_SHA256)
        self.assertTrue(manifest["v2725_delta"]["uses_v2724_ioctl_result_helper"])
        self.assertTrue(manifest["v2725_delta"]["future_live_has_uniform_ioctl_markers"])
        self.assertEqual(manifest["corrected_manifest_contract"]["replay_order"], v2725.v2721.EXPECTED_REPLAY_ORDER)
        self.assertEqual(manifest["corrected_manifest_contract"]["stale_cal_types_present"], [])
        self.assertNotIn("--basic-payload", manifest["remote_argv"])

    def test_write_report_is_public_metadata_only(self) -> None:
        ns = args()
        manifest = v2725.build_manifest(ns)
        v2725.write_report(ns.report_path, manifest, ns.manifest_path)
        text = ns.report_path.read_text(encoding="utf-8")

        self.assertIn("V2725", text)
        self.assertIn("helper_sha256", text)
        self.assertIn("stale_cal_types_present: `[]`", text)
        self.assertNotIn("workspace/private/runs/audio", text)
        self.assertNotIn("device-artifacts", text)
        self.assertNotIn(".jsonl", text)


if __name__ == "__main__":
    unittest.main()
