"""Tests for V2583 ACDB pre-init store-get probe builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2583 = load_revalidation("build_android_acdb_preinit_store_get_probe_v2583")


class BuildAndroidAcdbPreinitStoreGetProbeV2583(unittest.TestCase):
    def test_source_state_requires_hook_and_store_get_cases(self) -> None:
        state = v2583.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        self.assertEqual(len(state["cases"]), 5)
        self.assertIn("store_selector_37", state["cases"])
        self.assertIn("store_selector_1_instance", state["cases"])

    def test_manifest_without_build_is_host_only_and_live_blocked(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2583-manifest-"))
        args = v2583.parse_args([
            "--build-root",
            str(root / "build"),
            "--manifest-path",
            str(root / "manifest.json"),
        ])
        payload = v2583.manifest(args)

        self.assertTrue(payload["host_only"])
        self.assertEqual(payload["device_action"], "none")
        self.assertTrue(payload["boundaries"]["live_execution_blocked_in_this_unit"])
        self.assertIn("common-topology hook", payload["capture_contract"]["store_get_policy"])
        self.assertTrue(payload["source_state"]["required_ok"])

    def test_report_records_preinit_boundary(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2583-report-"))
        args = v2583.parse_args([
            "--build-root",
            str(root / "build"),
            "--manifest-path",
            str(root / "manifest.json"),
        ])
        payload = v2583.manifest(args)
        payload["build"] = {
            "artifacts": {
                "helper": {
                    "path": "workspace/private/builds/audio/x/bin/helper",
                    "sha256": "a" * 64,
                    "file": "ELF 32-bit",
                    "checks": {"entry_start": True},
                },
                "preload": {
                    "path": "workspace/private/builds/audio/x/bin/preload.so",
                    "sha256": "b" * 64,
                    "file": "ELF 32-bit",
                    "checks": {"exports_common_topology": True},
                },
            }
        }
        report = root / "report.md"

        v2583.write_report(report, payload)
        text = report.read_text(encoding="utf-8")

        self.assertIn("Host-only build-only unit", text)
        self.assertIn("common-topology hook", text)
        self.assertIn("metadata only", text)
        self.assertIn("does not open `/dev/msm_audio_cal`", text)
        self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
