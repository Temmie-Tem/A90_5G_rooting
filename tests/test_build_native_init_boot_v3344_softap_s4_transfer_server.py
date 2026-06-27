from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3344_softap_s4_transfer_server.py"
)


class BuildNativeInitBootV3344SoftapS4TransferServerTests(unittest.TestCase):
    def test_v3344_identity(self) -> None:
        self.assertEqual(runner.CYCLE, "V3344")
        self.assertEqual(runner.INIT_VERSION, "0.11.108")
        self.assertEqual(runner.INIT_BUILD, "v3344-softap-s4-transfer-server")
        self.assertEqual(
            runner.EXPECTED_HELPER_SHA256,
            "fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef",
        )
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3344_softap_s4_transfer_server.img",
        )
        self.assertEqual(runner.BASE_BOOT.name, "boot_linux_v3335_gpu_z3_primary_setcrtc.img")

    def test_required_strings_cover_s4_transfer_server(self) -> None:
        required = b"\n".join(runner.REQUIRED_STRINGS)

        self.assertIn(b"0.11.108", required)
        self.assertIn(b"v3344-softap-s4-transfer-server", required)
        self.assertIn(b"transfer-start [channel]", required)
        self.assertIn(b"transfer-status", required)
        self.assertIn(b"scope=s4-local-transfer-server-private-ap", required)
        self.assertIn(b"server_bind_private_ap_only=1", required)
        self.assertIn(b"softap-transfer-start-pass", required)
        self.assertIn(b"softap-transfer-status-pass", required)
        self.assertIn(b"download_payload_sha256=%s", required)
        self.assertIn(b"upload_result.sha256=%s", required)
        self.assertIn(b"transfer_runtime_removed=1", required)

    def test_softap_manifest_names_s4_transfer_contract(self) -> None:
        manifest = runner._softap_manifest()

        self.assertEqual(manifest["rung"], "S4-transfer-server")
        self.assertEqual(
            manifest["scope"],
            "softap-private-ap-http-download-raw-upload-sha-cleanup",
        )
        self.assertIn("wifi softap transfer-start 6", manifest["commands"])
        self.assertIn("wifi softap transfer-status", manifest["commands"])
        self.assertEqual(
            manifest["transfer_contract"]["http_download"],
            "busybox-httpd-private-ap-bind",
        )
        self.assertEqual(
            manifest["transfer_contract"]["raw_upload"],
            "native-bounded-single-connection-private-ap-bind",
        )
        self.assertIn("http-download-sha256-match", manifest["pass_requirements"])
        self.assertIn("raw-upload-sha256-match", manifest["pass_requirements"])
        self.assertIn("post-cleanup-selftest-fail-0", manifest["pass_requirements"])

    def test_report_describes_redacted_private_transfer_proof(self) -> None:
        report = runner.render_report(
            {
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
                "helper_sha256": "1" * 64,
            },
            (runner.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,),
            (),
        )

        self.assertIn("V3344", report)
        self.assertIn("0.11.108", report)
        self.assertIn("BusyBox `httpd`", report)
        self.assertIn("raw upload receiver", report)
        self.assertIn("HTTP download SHA match", report)
        self.assertIn("raw upload SHA match", report)
        self.assertIn("must not contain SSID, PSK", report)

    def test_current_wifi_source_contains_s4_transfer_surface(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("softap-transfer-start-pass", source)
        self.assertIn("softap-transfer-status-pass", source)
        self.assertIn("server_bind_private_ap_only=1", source)
        self.assertIn("download_payload_sha256=%s", source)
        self.assertIn("upload_result.sha256=%s", source)


if __name__ == "__main__":
    unittest.main()
