from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"


class NativeSoftapS4TransferServerSourceV3344Tests(unittest.TestCase):
    def test_transfer_commands_are_registered(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("static int wifi_softap_transfer_start", source)
        self.assertIn("static int wifi_softap_transfer_status_command", source)
        self.assertIn('strcmp(subcommand, "transfer-start") == 0', source)
        self.assertIn('strcmp(subcommand, "transfer-status") == 0', source)
        self.assertIn("transfer-start [channel]", source)
        self.assertIn("transfer-status", source)

    def test_transfer_server_is_private_ap_bound(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("wifi_start_softap_httpd", source)
        self.assertIn("wifi_start_softap_upload_receiver", source)
        self.assertIn("server_bind_private_ap_only=1", source)
        self.assertIn("address_value_logged=0", source)
        self.assertIn("client_identity_logged=0", source)
        self.assertIn("peer_address_logged=0", source)
        self.assertNotIn('"0.0.0.0"', source)
        self.assertNotIn("INADDR_ANY", source)

    def test_transfer_uses_http_download_and_bounded_raw_upload(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn('"httpd"', source)
        self.assertIn("A90_WIFI_SOFTAP_DOWNLOAD_BYTES", source)
        self.assertIn("A90_WIFI_SOFTAP_UPLOAD_MAX_BYTES", source)
        self.assertIn("download_payload_sha256=%s", source)
        self.assertIn("upload_result.sha256=%s", source)
        self.assertIn('wifi_softap_print_file_meta("download_file"', source)
        self.assertIn('wifi_softap_print_file_meta("upload_file"', source)
        self.assertIn("softap-transfer-start-pass", source)
        self.assertIn("softap-transfer-status-pass", source)

    def test_transfer_keeps_no_wan_nat_route_export(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("wan_nat_attempted=0", source)
        self.assertIn("ip_forward_write_attempted=0", source)
        self.assertIn("nat_attempted=0", source)
        self.assertIn("default_route_export_attempted=0", source)
        self.assertIn("dhcp_router_option_exported=0", source)
        self.assertNotIn("option router", source)

    def test_cleanup_stops_server_workers_and_removes_transfer_files(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("A90_WIFI_SOFTAP_HTTPD_PID", source)
        self.assertIn("A90_WIFI_SOFTAP_UPLOAD_PID", source)
        self.assertIn("transfer_runtime_removed=1", source)
        self.assertIn("final_httpd_count=%d", source)
        self.assertIn("A90_WIFI_SOFTAP_DOWNLOAD_FILE", source)
        self.assertIn("A90_WIFI_SOFTAP_UPLOAD_FILE", source)
        self.assertIn("A90_WIFI_SOFTAP_UPLOAD_RESULT", source)


if __name__ == "__main__":
    unittest.main()
