"""Tests for the V2630 ACDB SET-calibration capture build gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2630 = load_revalidation("build_android_acdb_setcal_capture_v2630")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2630-test-"))
    defaults: dict[str, object] = {
        "build": False,
        "write_report": False,
        "build_root": root / "build",
        "manifest": root / "build/manifest.json",
        "report": root / "report.md",
        "clang": v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        "lld": v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class BuildAndroidAcdbSetcalCaptureV2630(unittest.TestCase):
    def test_source_state_requires_setcal_arg_and_dmabuf_capture(self) -> None:
        state = v2630.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        required = state["required"]
        self.assertTrue(required["base_v2613_required_ok"])
        self.assertTrue(required["always_fakes_audio_set"])
        self.assertTrue(required["preserves_full_set_arg"])
        self.assertTrue(required["parses_set_header_words"])
        self.assertTrue(required["same_process_dmabuf_mmap_dump"])
        self.assertTrue(required["header_only_is_not_failure"])
        self.assertTrue(required["sha256_for_arg_and_dmabuf"])
        self.assertTrue(required["retains_v2531_trace_events"])

    def test_dry_run_contract_is_host_only_and_blocks_real_set(self) -> None:
        payload = v2630.make_payload(args())

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["host_only_build"])
        self.assertTrue(payload["measurement_boundary"]["no_live_default"])
        self.assertTrue(payload["measurement_boundary"]["raw_payload_private_only"])
        self.assertIn("always fake-successes AUDIO_SET_CALIBRATION", payload["measurement_boundary"]["no_real_audio_set"])
        self.assertIn("arg[0:data_size]", payload["capture_contract"]["set_capture"])
        self.assertIn("same-process", payload["capture_contract"]["dmabuf_capture"])
        self.assertEqual(
            payload["sources"]["v2630_delta"]["header_only_policy"],
            "cal_size==0 or mem_handle<0 is a valid header-only SET record, not a failed capture",
        )

    def test_patched_context_restores_v2613_and_ioctl_constants(self) -> None:
        original_artifact = v2630.v2613.PRELOAD_ARTIFACT_NAME
        original_ioctl = v2630.v2613.v2611.v2608.v2572.IOCTL_SOURCE_REL

        with v2630.patched_v2613_constants():
            self.assertEqual(v2630.v2613.PRELOAD_ARTIFACT_NAME, v2630.PRELOAD_ARTIFACT_NAME)
            self.assertEqual(v2630.v2613.v2611.v2608.v2572.IOCTL_SOURCE_REL, v2630.IOCTL_SOURCE_REL)

        self.assertEqual(v2630.v2613.PRELOAD_ARTIFACT_NAME, original_artifact)
        self.assertEqual(v2630.v2613.v2611.v2608.v2572.IOCTL_SOURCE_REL, original_ioctl)

    @unittest.skipUnless(
        (v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang").exists()
        and (v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld").exists(),
        "private Android clang/lld unavailable",
    )
    def test_build_outputs_arm32_helper_and_setcal_preload(self) -> None:
        payload = v2630.make_payload(args(build=True))
        helper = payload["build"]["artifacts"]["helper"]
        preload = payload["build"]["artifacts"]["preload"]

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(helper["ok"], helper)
        self.assertTrue(preload["ok"], preload)
        self.assertIn("ELF 32-bit LSB", helper["file"]["stdout"])
        self.assertIn("ELF 32-bit LSB", preload["file"]["stdout"])
        self.assertEqual(len(helper["sha256"]), 64)
        self.assertEqual(len(preload["sha256"]), 64)
        self.assertTrue(preload["checks"]["soname_v2630"])
        self.assertIn(" UND mmap", preload["symbols"]["stdout"])
        self.assertIn(" UND munmap", preload["symbols"]["stdout"])

    def test_cli_writes_manifest_and_report(self) -> None:
        local_args = args(write_report=True)
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/build_android_acdb_setcal_capture_v2630.py",
                "--build-root",
                str(local_args.build_root),
                "--manifest",
                str(local_args.manifest),
                "--write-report",
                "--report",
                str(local_args.report),
            ],
            cwd=v2630.ROOT,
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
