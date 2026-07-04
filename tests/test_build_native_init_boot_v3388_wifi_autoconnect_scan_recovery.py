"""Regression tests for V3388 Wi-Fi autoconnect scan recovery source build."""

from __future__ import annotations

import unittest

from _loader import load_revalidation


builder = load_revalidation("build_native_init_boot_v3388_wifi_autoconnect_scan_recovery")


class BuildNativeInitBootV3388WifiAutoconnectScanRecoveryTests(unittest.TestCase):
    def test_builder_identity_and_required_markers(self) -> None:
        self.assertEqual(builder.CYCLE, "V3388")
        self.assertEqual(builder.INIT_VERSION, "0.11.144")
        self.assertEqual(builder.INIT_BUILD, "v3388-wifi-autoconnect-scan-recovery")

        required = b"\n".join(builder.REQUIRED_STRINGS)
        for marker in (
            b"v3388-wifi-autoconnect-scan-recovery",
            b"0.11.144",
            b"a90-native-wifi-uplink-service-v1",
            b"autoconnect_profile_present=",
            b"config_profile_present=",
            b"requested_profile_present=",
            b"scan_recovery_attempted=",
            b"scan_recovery_first_scan_rc=",
            b"scan_recovery_rc=",
            b"scan_recovery_rescan_rc=",
            b"scan_recovery_success=",
            b"scan_recovery_decision=",
            b"wifi-autoconnect-scan-recovery-pass",
            b"wifi-autoconnect-scan-recovery-probe-failed",
            b"wifi-autoconnect-scan-recovery-rescan-failed",
            b"wifi-uplink-service-confirm-required",
            b"credentials=private-config-gated",
            b"secret_values_logged=0",
        ):
            self.assertIn(marker, required)

    def test_rewrite_updates_v3387_identity(self) -> None:
        text = builder._rewrite_v3388_text(
            "V3387 0.11.143 v3387-wifi-uplink-service-redacted "
            "wifi-uplink-service-redacted a90-doomgeneric-v3387"
        )
        self.assertIn("V3388", text)
        self.assertIn("0.11.144", text)
        self.assertIn("v3388-wifi-autoconnect-scan-recovery", text)
        self.assertIn("wifi-autoconnect-scan-recovery", text)
        self.assertIn("a90-doomgeneric-v3388", text)
        self.assertNotIn("v3387", text)
        self.assertNotIn("wifi-uplink-service-redacted", text)

    def test_manifest_records_scan_recovery_contract(self) -> None:
        manifest = builder._boot_audit_manifest()
        service = manifest["wifi_uplink_service_boundary"]

        self.assertEqual(service["version"], "a90-native-wifi-uplink-service-v1")
        self.assertEqual(service["scan_recovery"]["strategy"], "cleanup-iftype-probe-rescan-once")
        self.assertEqual(
            service["scan_recovery"]["redacted_result_fields"],
            [
                "scan_recovery_attempted",
                "scan_recovery_first_scan_rc",
                "scan_recovery_rc",
                "scan_recovery_rescan_rc",
                "scan_recovery_success",
                "scan_recovery_decision",
            ],
        )
        self.assertIn(
            "bin/a90_doomgeneric_private_engine_v3387",
            service["obsolete_ramdisk_engines"],
        )


if __name__ == "__main__":
    unittest.main()
