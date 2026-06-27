from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"


class NativeSoftapS3Mode2BringupSourceV3343Tests(unittest.TestCase):
    def test_softap_start_command_is_registered(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("static int wifi_softap_start", source)
        self.assertIn('strcmp(subcommand, "start") == 0', source)
        self.assertIn("start [channel]", source)
        self.assertIn("usage: wifi softap start [1|6|11]", source)

    def test_start_uses_wpa_supplicant_mode2_not_hostapd(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("A90_WIFI_SOFTAP_SUPPLICANT_CONF", source)
        self.assertIn('"\\tmode=2\\n"', source)
        self.assertIn("wpa_supplicant_mode2_start_attempted=1", source)
        self.assertIn("hostapd_start_attempted=0", source)
        self.assertNotIn("hostapd_start_attempted=1", source)

    def test_start_is_pinned_to_non_dfs_24ghz_channels(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("wifi_softap_channel_to_freq", source)
        self.assertIn("return 2412", source)
        self.assertIn("return 2437", source)
        self.assertIn("return 2462", source)
        self.assertIn("wifi_softap_parse_channel", source)

    def test_start_adds_udhcpd_without_route_or_nat_export(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn('"udhcpd"', source)
        self.assertIn("dhcp_server_start_attempted=1", source)
        self.assertIn("dhcp_server_alive=%d", source)
        self.assertIn("default_route_export_attempted=0", source)
        self.assertIn("nat_attempted=0", source)
        self.assertIn("dhcp_router_option_exported=0", source)
        self.assertNotIn("option router", source)

    def test_cleanup_is_real_and_removes_private_runtime_config(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("static int wifi_softap_cleanup_command", source)
        self.assertIn("wifi_softap_cleanup_internal", source)
        self.assertIn("A90_WIFI_SOFTAP_PRIVATE_CREDENTIALS", source)
        self.assertIn("private_config_removed=1", source)
        self.assertIn("softap-cleanup-pass", source)

    def test_public_output_keeps_credentials_redacted(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("credentials=private-generated", source)
        self.assertIn("credential_file_private=1", source)
        self.assertIn("ssid_psk_logged=0", source)
        self.assertIn("address_value_logged=0", source)


if __name__ == "__main__":
    unittest.main()
