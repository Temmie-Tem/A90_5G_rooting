"""Tests for the V2828 audio route-map safety-label boot-image builder."""

from __future__ import annotations

import importlib
import unittest

v2828 = importlib.import_module("build_native_init_boot_v2828_audio_route_map_safety")


class BuildNativeInitBootV2828AudioRouteMapSafetyTest(unittest.TestCase):
    def test_identity_and_paths_are_v2828(self) -> None:
        self.assertEqual(v2828.CYCLE, "V2828")
        self.assertEqual(v2828.INIT_VERSION, "0.10.6")
        self.assertEqual(v2828.INIT_BUILD, "v2828-audio-route-map-safety")
        self.assertIn("boot_linux_v2828_audio_route_map_safety.img", str(v2828.BOOT_IMAGE))
        self.assertIn("NATIVE_INIT_V2828_AUDIO_ROUTE_MAP_SAFETY_SOURCE_BUILD", str(v2828.REPORT_PATH))

    def test_report_names_safety_label_delta_and_no_device_action(self) -> None:
        manifest = {
            "decision": v2828.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2828_audio_route_map_safety.img",
            "boot_sha256": "a" * 64,
            "init_version": v2828.INIT_VERSION,
            "init_build": v2828.INIT_BUILD,
        }
        report = v2828.render_report(manifest, ("-DTEST=1",), ("-DINIT=1",))
        self.assertIn("V2828", report)
        self.assertIn("0.10.6", report)
        self.assertIn("route-map safety-label", report)
        self.assertIn("SP UNVERIFIED", report)
        self.assertIn("Device flash: `no`", report)
        self.assertIn("Rollback target remains `v2321-usb-clean-identity-rodata`", report)

    def test_metadata_rewrite_marks_pending_live_validation(self) -> None:
        source = v2828.__loader__.get_source(v2828.__name__)
        self.assertIsNotNone(source)
        assert source is not None

        self.assertIn('"audio-route-map-safety-labels"', source)
        self.assertIn('"pending-live-validation"', source)
        self.assertIn("explicit route-map safety labels", source)


if __name__ == "__main__":
    unittest.main()
