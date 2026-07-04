"""Regression tests for V3386 Wi-Fi uplink-service boundary source build."""

from __future__ import annotations

import unittest

from _loader import load_revalidation


builder = load_revalidation("build_native_init_boot_v3386_wifi_uplink_service_boundary")


class BuildNativeInitBootV3386WifiUplinkServiceBoundaryTests(unittest.TestCase):
    def test_builder_identity_and_required_markers(self) -> None:
        self.assertEqual(builder.CYCLE, "V3386")
        self.assertEqual(builder.INIT_VERSION, "0.11.142")
        self.assertEqual(builder.INIT_BUILD, "v3386-wifi-uplink-service-boundary")

        required = b"\n".join(builder.REQUIRED_STRINGS)
        for marker in (
            b"v3386-wifi-uplink-service-boundary",
            b"0.11.142",
            b"a90-native-wifi-uplink-service-v1",
            b"wifi uplink-service [status|start|stop|once]",
            b"A90_NATIVE_UPLINK_AUTOCONNECT_V1",
            b"wifi-uplink-service-start-pass",
            b"wifi-uplink-service-confirm-required",
            b"wifi-uplink-service-autoconnect-pass",
            b"credentials=private-config-gated",
            b"connect=confirm-gated",
            b"external_ping_execution=0",
            b"public_tunnel=0",
        ):
            self.assertIn(marker, required)

    def test_rewrite_updates_v3385_identity(self) -> None:
        text = builder._rewrite_v3386_text(
            "V3385 0.11.141 v3385-wifi-service-boundary "
            "wifi-service-boundary a90-doomgeneric-v3385"
        )
        self.assertIn("V3386", text)
        self.assertIn("0.11.142", text)
        self.assertIn("v3386-wifi-uplink-service-boundary", text)
        self.assertIn("wifi-uplink-service-boundary", text)
        self.assertIn("a90-doomgeneric-v3386", text)
        self.assertNotIn("v3385", text)
        self.assertNotIn("wifi-service-boundary", text)

    def test_manifest_names_separate_uplink_contract(self) -> None:
        manifest = builder._boot_audit_manifest()
        service = manifest["wifi_uplink_service_boundary"]

        self.assertEqual(service["version"], "a90-native-wifi-uplink-service-v1")
        self.assertEqual(service["request_file"], "request")
        self.assertEqual(service["response_file"], "response")
        self.assertEqual(service["supported_ops"], ["status", "autoconnect"])
        self.assertEqual(service["execution_gate"], "confirm=A90_NATIVE_UPLINK_AUTOCONNECT_V1")
        self.assertEqual(service["public_exposure"], "denied")
        self.assertEqual(service["external_ping"], "denied")
        self.assertTrue(service["separate_from_status_scan_service"])
        self.assertIn(
            "bin/a90_doomgeneric_private_engine_v3385",
            service["obsolete_ramdisk_engines"],
        )


if __name__ == "__main__":
    unittest.main()
