"""Tests for the V2820 audio selftest policy boot-image builder."""

from __future__ import annotations

import importlib
import unittest

v2820 = importlib.import_module("build_native_init_boot_v2820_audio_selftest_policy")


class BuildNativeInitBootV2820AudioSelftestPolicyTest(unittest.TestCase):
    def test_identity_and_paths_are_v2820(self) -> None:
        self.assertEqual(v2820.CYCLE, "V2820")
        self.assertEqual(v2820.INIT_VERSION, "0.10.2")
        self.assertEqual(v2820.INIT_BUILD, "v2820-audio-selftest-policy")
        self.assertIn("boot_linux_v2820_audio_selftest_policy.img", str(v2820.BOOT_IMAGE))
        self.assertIn("NATIVE_INIT_V2820_AUDIO_SELFTEST_POLICY_SOURCE_BUILD", str(v2820.REPORT_PATH))

    def test_report_names_policy_fix_and_no_device_action(self) -> None:
        manifest = {
            "decision": v2820.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2820_audio_selftest_policy.img",
            "boot_sha256": "6" * 64,
            "init_version": v2820.INIT_VERSION,
            "init_build": v2820.INIT_BUILD,
        }
        report = v2820.render_report(manifest, ("-DTEST=1",), ("-DINIT=1",))
        self.assertIn("V2820", report)
        self.assertIn("0.10.2", report)
        self.assertIn("boost controls as present-but-write-blocked", report)
        self.assertIn("Device flash: `no`", report)
        self.assertIn("Rollback target remains `v2321-usb-clean-identity-rodata`", report)

    def test_metadata_rewrite_mentions_pending_live_validation(self) -> None:
        text = v2820.__file__
        self.assertIn("build_native_init_boot_v2820_audio_selftest_policy.py", text)
        from pathlib import Path
        source = Path(text).read_text(encoding="utf-8")
        self.assertIn('"audio-observability-candidate"', source)
        self.assertIn('"pending-live-validation"', source)
        self.assertIn("selftest boost-policy predicate fix", source)


if __name__ == "__main__":
    unittest.main()
