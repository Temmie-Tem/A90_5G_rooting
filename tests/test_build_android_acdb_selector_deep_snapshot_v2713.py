"""Tests for the V2713 ACDB selector deep-snapshot build gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2713 = load_revalidation("build_android_acdb_selector_deep_snapshot_v2713")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2713-test-"))
    defaults: dict[str, object] = {
        "build": False,
        "write_report": False,
        "build_root": root / "build",
        "manifest": root / "build/manifest.json",
        "report": root / "report.md",
        "clang": v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        "lld": v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class BuildAndroidAcdbSelectorDeepSnapshotV2713(unittest.TestCase):
    def test_source_state_requires_deep_snapshot_large_buffer_get_and_no_preinit_set(self) -> None:
        state = v2713.source_state()
        required = state["required"]
        prohibited = state["prohibited"]

        self.assertTrue(state["required_ok"], required)
        self.assertTrue(state["prohibited_ok"], prohibited)
        self.assertTrue(required["preinit_uses_large_get_constant"])
        self.assertTrue(required["preinit_declares_ownprocess_buffer"])
        self.assertTrue(required["preinit_zeros_large_buffer_before_get"])
        self.assertTrue(required["preinit_sets_word0_to_large_len"])
        self.assertTrue(required["preinit_sets_word1_to_ownprocess_buffer"])
        self.assertTrue(required["preinit_large_request_before_get"])
        self.assertTrue(required["preinit_logs_selector_deep_snapshot"])
        self.assertTrue(required["preinit_no_fake_set_call"])
        self.assertFalse(prohibited["preinit_calls_audio_set"])
        self.assertEqual(state["v2713_delta"]["word0"], "force lower custom topology GET input word0 to 65536")

    def test_tap_source_extends_known_indirect_capture_to_lower_custom_topologies(self) -> None:
        state = v2713.source_state()
        required = state["required"]

        self.assertTrue(required["tap_captures_lower_afe_custom_topology"])
        self.assertTrue(required["tap_captures_lower_adm_custom_topology"])
        self.assertTrue(required["tap_captures_lower_asm_custom_topology"])
        self.assertTrue(required["tap_captures_lower_supp_custom_topology"])
        self.assertTrue(required["tap_indirect_capture_after_real_get"])
        self.assertTrue(required["tap_retains_65536_capture_cap"])

    def test_dry_run_contract_is_host_only_and_targets_v2702_buffer_gap(self) -> None:
        payload = v2713.make_payload(args())
        contract = payload["capture_contract"]
        boundary = payload["measurement_boundary"]

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["host_only_build"])
        self.assertTrue(boundary["no_live_default"])
        self.assertTrue(boundary["no_native_replay"])
        self.assertTrue(boundary["preinit_no_audio_set_call"])
        self.assertEqual(contract["large_get_bytes"], 65536)
        self.assertEqual(contract["target_cal_types"], [24, 10, 14])
        self.assertEqual(contract["get_commands"][10], "0x00011394")
        self.assertEqual(contract["get_commands"][14], "0x00012e01")
        self.assertIn("V2702", contract["v2702_dependency"])
        self.assertIn("v2713_selector_deep_snapshot", contract["success_discriminator"])

    def test_patched_constants_restore_v2692(self) -> None:
        original_preinit = v2713.v2692.PREINIT_SOURCE_REL
        original_tap = v2713.v2692.ACDBTAP_SOURCE_REL
        original_preload = v2713.v2692.PRELOAD_ARTIFACT_NAME

        with v2713.patched_v2692_constants():
            self.assertEqual(v2713.v2692.PREINIT_SOURCE_REL, v2713.PREINIT_SOURCE_REL)
            self.assertEqual(v2713.v2692.ACDBTAP_SOURCE_REL, v2713.ACDBTAP_SOURCE_REL)
            self.assertEqual(v2713.v2692.PRELOAD_ARTIFACT_NAME, v2713.PRELOAD_ARTIFACT_NAME)

        self.assertEqual(v2713.v2692.PREINIT_SOURCE_REL, original_preinit)
        self.assertEqual(v2713.v2692.ACDBTAP_SOURCE_REL, original_tap)
        self.assertEqual(v2713.v2692.PRELOAD_ARTIFACT_NAME, original_preload)

    @unittest.skipUnless(
        (v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang").exists()
        and (v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld").exists(),
        "private Android clang/lld unavailable",
    )
    def test_build_outputs_arm32_selector_deep_snapshot_helper_and_preload(self) -> None:
        payload = v2713.make_payload(args(build=True))
        helper = payload["build"]["artifacts"]["helper"]
        preload = payload["build"]["artifacts"]["preload"]

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(helper["ok"], helper)
        self.assertTrue(preload["ok"], preload)
        self.assertIn("ELF 32-bit LSB", helper["file"]["stdout"])
        self.assertIn("ELF 32-bit LSB", preload["file"]["stdout"])
        self.assertTrue(preload["checks"]["soname_v2713"])
        self.assertTrue(preload["checks"]["exports_acdb_ioctl"])
        self.assertTrue(preload["checks"]["exports_ioctl"])
        self.assertTrue(preload["checks"]["exports_lower_runner"])
        self.assertTrue(preload["checks"]["exports_a90_arm_capture"])
        self.assertEqual(len(helper["sha256"]), 64)
        self.assertEqual(len(preload["sha256"]), 64)

    def test_cli_writes_manifest_and_report(self) -> None:
        local_args = args(write_report=True)
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/build_android_acdb_selector_deep_snapshot_v2713.py",
                "--build-root",
                str(local_args.build_root),
                "--manifest",
                str(local_args.manifest),
                "--write-report",
                "--report",
                str(local_args.report),
            ],
            cwd=v2713.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertTrue(local_args.manifest.exists())
        self.assertTrue(local_args.report.exists())
        self.assertIn("selector deep-snapshot", local_args.report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
