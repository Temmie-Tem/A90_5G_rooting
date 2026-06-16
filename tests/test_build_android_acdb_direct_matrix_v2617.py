"""Tests for the V2617 ACDB direct matrix build gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2617 = load_revalidation("build_android_acdb_direct_matrix_v2617")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2617-test-"))
    defaults: dict[str, object] = {
        "build": False,
        "write_report": False,
        "build_root": root / "build",
        "manifest": root / "build/manifest.json",
        "report": root / "report.md",
        "clang": v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        "lld": v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class BuildAndroidAcdbDirectMatrixV2617(unittest.TestCase):
    def test_source_state_requires_manual_postinit_arm_and_direct_matrix(self) -> None:
        state = v2617.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        required = state["required"]
        self.assertTrue(required["helper_calls_init_v3_with_meta_head"])
        self.assertTrue(required["helper_arms_after_init_before_matrix"])
        self.assertTrue(required["helper_does_not_call_send_audio_cal_v5"])
        self.assertTrue(required["tap_manual_arm_exported"])
        self.assertTrue(required["tap_unarmed_real_only_path"])
        self.assertTrue(required["tap_auto_arm_disabled_by_build_flags"])
        self.assertTrue(required["tap_exit_on_target_disabled_by_build_flags"])
        self.assertTrue(required["helper_has_v2614_base_commands"])
        self.assertTrue(required["helper_has_bounded_vol_sweep"])

    def test_dry_run_contract_is_capture_only_and_exit_disabled(self) -> None:
        payload = v2617.make_payload(args())

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["host_only_build"])
        self.assertTrue(payload["measurement_boundary"]["no_live_default"])
        self.assertTrue(payload["measurement_boundary"]["no_native_replay"])
        self.assertEqual(payload["measurement_boundary"]["fake_audio_cal_env"], "A90_ACDB_FAKE_ALLOCATE=1")
        self.assertIn("post-init", payload["capture_contract"]["armed_dump_policy"])
        self.assertFalse(payload["sources"]["armed_capture_contract"]["auto_arm_on_initialize"])
        self.assertFalse(payload["sources"]["armed_capture_contract"]["exit_on_first_4916"])

    def test_matrix_shape_matches_v2616_geometry(self) -> None:
        matrix = v2617.source_state()["direct_matrix"]

        self.assertEqual(matrix["base_commands"][0], "0x1122e")
        self.assertIn("0x13265", matrix["base_commands"])
        self.assertIn("0x1326f", matrix["base_commands"])
        self.assertEqual(matrix["vol_sweep"]["commands"], ["0x1326d", "0x1326e"])
        self.assertEqual(matrix["vol_sweep"]["gain_steps"], list(range(16)))
        self.assertEqual(matrix["max_direct_calls"], 42)

    def test_patched_context_restores_v2613_constants(self) -> None:
        original_helper = v2617.v2613.HELPER_SOURCE_REL
        original_artifact = v2617.v2613.HELPER_ARTIFACT_NAME

        with v2617.patched_v2613_constants():
            self.assertEqual(v2617.v2613.HELPER_SOURCE_REL, v2617.HELPER_SOURCE_REL)
            self.assertEqual(v2617.v2613.HELPER_ARTIFACT_NAME, v2617.HELPER_ARTIFACT_NAME)

        self.assertEqual(v2617.v2613.HELPER_SOURCE_REL, original_helper)
        self.assertEqual(v2617.v2613.HELPER_ARTIFACT_NAME, original_artifact)

    @unittest.skipUnless(
        (v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang").exists()
        and (v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld").exists(),
        "private Android clang/lld unavailable",
    )
    def test_build_outputs_arm32_helper_and_combined_preload(self) -> None:
        payload = v2617.make_payload(args(build=True))
        helper = payload["build"]["artifacts"]["helper"]
        preload = payload["build"]["artifacts"]["preload"]

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(helper["ok"], helper)
        self.assertTrue(preload["ok"], preload)
        self.assertIn("ELF 32-bit LSB", helper["file"]["stdout"])
        self.assertIn("ELF 32-bit LSB", preload["file"]["stdout"])
        self.assertEqual(len(helper["sha256"]), 64)
        self.assertEqual(len(preload["sha256"]), 64)
        self.assertTrue(preload["checks"]["soname_v2617"])
        self.assertTrue(helper["checks"]["does_not_reference_send_audio_cal_v5"])

    def test_cli_writes_manifest_and_report(self) -> None:
        local_args = args(write_report=True)
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/build_android_acdb_direct_matrix_v2617.py",
                "--build-root",
                str(local_args.build_root),
                "--manifest",
                str(local_args.manifest),
                "--write-report",
                "--report",
                str(local_args.report),
            ],
            cwd=v2617.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(local_args.manifest.exists())
        self.assertTrue(local_args.report.exists())


if __name__ == "__main__":
    unittest.main()
