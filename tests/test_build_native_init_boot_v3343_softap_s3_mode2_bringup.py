from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3343_softap_s3_mode2_bringup.py"
)


class BuildNativeInitBootV3343SoftapS3Mode2BringupTests(unittest.TestCase):
    def test_v3343_identity(self) -> None:
        self.assertEqual(runner.CYCLE, "V3343")
        self.assertEqual(runner.INIT_VERSION, "0.11.107")
        self.assertEqual(runner.INIT_BUILD, "v3343-softap-s3-mode2-bringup")
        self.assertEqual(
            runner.EXPECTED_HELPER_SHA256,
            "fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef",
        )
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3343_softap_s3_mode2_bringup.img",
        )
        self.assertEqual(runner.BASE_BOOT.name, "boot_linux_v3335_gpu_z3_primary_setcrtc.img")

    def test_required_strings_cover_mode2_start_and_cleanup(self) -> None:
        required = b"\n".join(runner.REQUIRED_STRINGS)

        self.assertIn(b"0.11.107", required)
        self.assertIn(b"v3343-softap-s3-mode2-bringup", required)
        self.assertIn(b"wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|cleanup]", required)
        self.assertIn(b"softap-start-pass", required)
        self.assertIn(b"softap-cleanup-pass", required)
        self.assertIn(b"wpa_supplicant_mode2_start_attempted=1", required)
        self.assertIn(b"dhcp_server_start_attempted=1", required)
        self.assertIn(b"default_route_export_attempted=0", required)
        self.assertIn(b"nat_attempted=0", required)

    def test_softap_manifest_names_mode2_bringup_contract(self) -> None:
        manifest = runner._softap_manifest()

        self.assertEqual(manifest["rung"], "S3-ap-bringup")
        self.assertEqual(manifest["scope"], "softap-mode2-ap-dhcp-start-cleanup")
        self.assertIn("wifi softap start 6", manifest["commands"])
        self.assertIn("wifi softap cleanup", manifest["commands"])
        self.assertEqual(manifest["start_contract"]["ap_daemon"], "wpa_supplicant-mode-2")
        self.assertEqual(manifest["start_contract"]["hostapd"], "not-used")
        self.assertEqual(manifest["start_contract"]["dhcp"], "busybox-udhcpd")
        self.assertEqual(manifest["start_contract"]["allowed_channels"], [1, 6, 11])
        self.assertIn("version-0.11.107", manifest["pass_requirements"])
        self.assertIn("dhcp-server-alive-1", manifest["pass_requirements"])
        self.assertIn("softap-cleanup-rc-0", manifest["pass_requirements"])

    def test_report_describes_no_hostapd_no_wan_nat_default_route(self) -> None:
        report = runner.render_report(
            {
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
                "helper_sha256": "1" * 64,
            },
            (runner.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,),
            (),
        )

        self.assertIn("V3343", report)
        self.assertIn("0.11.107", report)
        self.assertIn("wpa_supplicant mode=2", report)
        self.assertIn("`udhcpd`", report)
        self.assertIn("without WAN/NAT/default-route export", report)
        self.assertIn("without a server listener", report)

    def test_current_wifi_source_contains_mode2_bringup(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("softap-start-pass", source)
        self.assertIn("wpa_supplicant_mode2_start_attempted=1", source)
        self.assertIn("dhcp_server_start_attempted=1", source)
        self.assertIn("softap-cleanup-pass", source)


if __name__ == "__main__":
    unittest.main()
