from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"
WIFI_DOC = ROOT / "docs/operations/NATIVE_INIT_WIFI_LIFECYCLE_COMMANDS.md"


class NativeSoftapS3IftypeProbeSourceV3341Tests(unittest.TestCase):
    def test_softap_iftype_probe_command_is_registered(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("static int wifi_softap_iftype_probe", source)
        self.assertIn('strcmp(subcommand, "iftype-probe") == 0', source)
        self.assertIn("A90_WIFI_SOFTAP_PROBE_IFACE", source)
        self.assertIn("A90_WIFI_SOFTAP_WLAN0_WAIT_MS", source)
        self.assertIn("wifi softap iftype-probe [timeout_ms]", source)

    def test_probe_uses_nl80211_ap_new_and_delete_interface(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("NL80211_CMD_NEW_INTERFACE", source)
        self.assertIn("NL80211_CMD_DEL_INTERFACE", source)
        self.assertIn("NL80211_ATTR_IFTYPE", source)
        self.assertIn("NL80211_IFTYPE_AP", source)
        self.assertIn("ap_iftype_add_attempted=1", source)
        self.assertIn("ap_iftype_cleanup_ok=", source)
        self.assertIn("softap-iftype-probe-pass", source)

    def test_probe_keeps_ap_server_start_blocked(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("config_write_attempted=0", source)
        self.assertIn("wpa_supplicant_mode2_start_attempted=0", source)
        self.assertIn("dhcp_server_start_attempted=0", source)
        self.assertIn("listener_start_attempted=0", source)
        self.assertIn("address_assign_attempted=0", source)
        self.assertIn("server_exposure_attempted=0", source)

    def test_probe_covers_sta_supplicant_stoppable_gate(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("wifi_softap_stop_sta_supplicant_if_needed", source)
        self.assertIn("sta_supplicant.stop_attempted=", source)
        self.assertIn("sta_supplicant.stoppable=", source)
        self.assertIn("softap-iftype-probe-sta-supplicant-busy", source)

    def test_wifi_lifecycle_doc_mentions_iftype_probe_contract(self) -> None:
        doc = WIFI_DOC.read_text(encoding="utf-8")

        self.assertIn("wifi softap iftype-probe [timeout_ms]", doc)
        self.assertIn("NL80211_CMD_NEW_INTERFACE", doc)
        self.assertIn("NL80211_CMD_DEL_INTERFACE", doc)
        self.assertIn("decision=softap-iftype-probe-pass", doc)
        self.assertIn("wpa_supplicant mode=2", doc)


if __name__ == "__main__":
    unittest.main()
