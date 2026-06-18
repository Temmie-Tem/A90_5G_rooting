"""Tests for the V2717 route-first common-topology SET capture build gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2717 = load_revalidation("build_android_acdb_route_first_common_setcal_capture_v2717")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2717-test-"))
    defaults: dict[str, object] = {
        "build": False,
        "write_report": False,
        "build_root": root / "build",
        "manifest": root / "build/manifest.json",
        "report": root / "report.md",
        "clang": v2717.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        "lld": v2717.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class BuildAndroidAcdbRouteFirstCommonSetcalCaptureV2717(unittest.TestCase):
    def test_source_state_requires_phase_hook_and_fake_set_boundary(self) -> None:
        state = v2717.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        self.assertTrue(state["required"]["helper_calls_send_v5_before_common_topology"])
        self.assertTrue(state["required"]["helper_event_path_v2717"])
        self.assertTrue(state["required"]["phase_hook_init_short_success"])
        self.assertTrue(state["required"]["phase_hook_calls_real_common_postinit"])
        self.assertTrue(state["required"]["phase_hook_neutralizes_real_common_reentry"])
        self.assertTrue(state["required"]["phase_hook_no_compile_flag_dependency"])
        self.assertTrue(state["required"]["ioctl_always_fakes_audio_set"])
        self.assertTrue(state["required"]["ioctl_dumps_same_process_dmabuf"])
        self.assertIn("route-specific send_v5 before post-init common topology", state["v2717_delta"]["basis"])

    def test_dry_run_contract_targets_custom_topology_phase_capture(self) -> None:
        payload = v2717.make_payload(args())

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["host_only_build"])
        self.assertTrue(payload["measurement_boundary"]["no_live_default"])
        self.assertTrue(payload["measurement_boundary"]["raw_payload_private_only"])
        self.assertEqual(payload["capture_contract"]["target_cal_types"], [10, 14, 24])
        self.assertIn("nested real-common entries return 0", payload["capture_contract"]["phase_common_policy"])
        self.assertIn("send_audio_cal_v5 -> post-init real common topology", payload["capture_contract"]["call_order"])
        self.assertIn("byte-exact SET records for 10/14/24", payload["capture_contract"]["success_discriminator"])

    def test_patched_context_restores_nested_build_constants(self) -> None:
        original_v2630_helper = v2717.v2630.HELPER_SOURCE_REL
        original_v2630_preinit = v2717.v2630.PREINIT_SOURCE_REL
        original_v2613_helper = v2717.v2630.v2613.HELPER_SOURCE_REL
        original_v2613_preinit = v2717.v2630.v2613.PREINIT_SOURCE_REL
        original_v2608_helper = v2717.v2630.v2613.v2611.v2608.HELPER_SOURCE_REL
        original_v2608_preinit = v2717.v2630.v2613.v2611.v2608.PREINIT_SOURCE_REL
        original_artifact = v2717.v2630.HELPER_ARTIFACT_NAME

        with v2717.patched_v2630_constants():
            self.assertEqual(v2717.v2630.HELPER_SOURCE_REL, v2717.HELPER_SOURCE_REL)
            self.assertEqual(v2717.v2630.PREINIT_SOURCE_REL, v2717.PREINIT_SOURCE_REL)
            self.assertEqual(v2717.v2630.v2613.HELPER_SOURCE_REL, v2717.HELPER_SOURCE_REL)
            self.assertEqual(v2717.v2630.v2613.PREINIT_SOURCE_REL, v2717.PREINIT_SOURCE_REL)
            self.assertEqual(v2717.v2630.v2613.v2611.v2608.HELPER_SOURCE_REL, v2717.HELPER_SOURCE_REL)
            self.assertEqual(v2717.v2630.v2613.v2611.v2608.PREINIT_SOURCE_REL, v2717.PREINIT_SOURCE_REL)
            self.assertEqual(v2717.v2630.HELPER_ARTIFACT_NAME, v2717.HELPER_ARTIFACT_NAME)

        self.assertEqual(v2717.v2630.HELPER_SOURCE_REL, original_v2630_helper)
        self.assertEqual(v2717.v2630.PREINIT_SOURCE_REL, original_v2630_preinit)
        self.assertEqual(v2717.v2630.v2613.HELPER_SOURCE_REL, original_v2613_helper)
        self.assertEqual(v2717.v2630.v2613.PREINIT_SOURCE_REL, original_v2613_preinit)
        self.assertEqual(v2717.v2630.v2613.v2611.v2608.HELPER_SOURCE_REL, original_v2608_helper)
        self.assertEqual(v2717.v2630.v2613.v2611.v2608.PREINIT_SOURCE_REL, original_v2608_preinit)
        self.assertEqual(v2717.v2630.HELPER_ARTIFACT_NAME, original_artifact)

    def test_phase_source_has_no_v2656_compile_gate(self) -> None:
        source = (v2717.ROOT / v2717.PREINIT_SOURCE_REL).read_text(encoding="utf-8")

        self.assertIn("common_reentry_neutralized", source)
        self.assertIn("init_common_return_success", source)
        self.assertIn("postinit_real_common_return", source)
        self.assertIn("A90_PHASE_REAL_COMMON", source)
        self.assertNotIn("A90_V2608_CALL_REAL_COMMON_TOPOLOGY", source)

    @unittest.skipUnless(
        (v2717.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang").exists()
        and (v2717.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld").exists(),
        "private Android clang/lld unavailable",
    )
    def test_build_outputs_arm32_helper_and_route_first_common_setcal_preload(self) -> None:
        payload = v2717.make_payload(args(build=True))
        helper = payload["build"]["artifacts"]["helper"]
        preload = payload["build"]["artifacts"]["preload"]

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(helper["ok"], helper)
        self.assertTrue(preload["ok"], preload)
        self.assertIn("ELF 32-bit LSB", helper["file"]["stdout"])
        self.assertIn("ELF 32-bit LSB", preload["file"]["stdout"])
        self.assertTrue(helper["checks"]["undefined_common_topology"])
        self.assertTrue(helper["checks"]["undefined_send_audio_cal_v5"])
        self.assertTrue(preload["checks"]["soname_v2717"])
        self.assertTrue(preload["checks"]["exports_phase_common_hook"])
        self.assertTrue(preload["checks"]["exports_acdb_ioctl"])
        self.assertTrue(preload["checks"]["exports_ioctl"])
        self.assertTrue(preload["checks"]["exports_a90_arm_capture"])
        self.assertTrue(payload["build"]["compile"]["preinit_no_send"]["phase_common_hook_enabled"])

    def test_cli_writes_manifest_and_report(self) -> None:
        local_args = args(write_report=True)
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/build_android_acdb_route_first_common_setcal_capture_v2717.py",
                "--build-root",
                str(local_args.build_root),
                "--manifest",
                str(local_args.manifest),
                "--write-report",
                "--report",
                str(local_args.report),
            ],
            cwd=v2717.ROOT,
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
        report = local_args.report.read_text(encoding="utf-8")
        self.assertIn("route-first common-topology", report)
        self.assertIn("send_audio_cal_v5 -> common_topology", report)


if __name__ == "__main__":
    unittest.main()
