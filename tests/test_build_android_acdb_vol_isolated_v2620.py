"""Tests for the V2620 ACDB VOL-isolated build."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2620 = load_revalidation("build_android_acdb_vol_isolated_v2620")


class BuildAndroidAcdbVolIsolatedV2620(unittest.TestCase):
    def test_source_state_skips_tail_meta_and_keeps_vol(self) -> None:
        state = v2620.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        self.assertEqual(state["vol_isolated_matrix"]["skipped_v2618_crash_command"], "0x12eeb")
        self.assertEqual(state["vol_isolated_matrix"]["vol_sweep"]["commands"], ["0x1326d", "0x1326e"])

    def test_make_payload_host_only_is_ready_without_live(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2620-test-"))
        args = argparse.Namespace(
            build=False,
            build_root=root / "build",
            manifest=root / "manifest.json",
            report=root / "report.md",
            write_report=False,
            clang=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
            lld=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
            readelf="readelf",
            file="file",
        )

        payload = v2620.make_payload(args)

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["host_only_build"])
        self.assertIn("0x12eeb", payload["capture_contract"]["skips"])
        self.assertEqual(payload["measurement_boundary"]["fake_audio_cal_env"], "A90_ACDB_FAKE_ALLOCATE=1")

    def test_write_report_declares_live_deferred(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2620-report-"))
        args = argparse.Namespace(
            build=False,
            build_root=root / "build",
            manifest=root / "manifest.json",
            report=root / "report.md",
            write_report=False,
            clang=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
            lld=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
            readelf="readelf",
            file="file",
        )
        payload = v2620.make_payload(args)

        v2620.write_report(payload, args.report)
        text = args.report.read_text(encoding="utf-8")

        self.assertIn("VOL-isolated", text)
        self.assertIn("0x12eeb", text)
        self.assertIn("Live execution is deferred", text)


if __name__ == "__main__":
    unittest.main()
