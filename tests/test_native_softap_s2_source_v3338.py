from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"
WIFI_DOC = ROOT / "docs/operations/NATIVE_INIT_WIFI_LIFECYCLE_COMMANDS.md"


class NativeSoftapS2SourceV3338Tests(unittest.TestCase):
    def test_softap_command_surface_is_registered(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn('#define A90_WIFI_SOFTAP_VERSION "a90-native-wifi-softap-v2"', source)
        self.assertIn('#define A90_WIFI_SOFTAP_ROOT "/cache/a90-softap"', source)
        self.assertIn("static int wifi_softap_cmd", source)
        self.assertIn('strcmp(argv[1], "softap") == 0', source)
        self.assertIn(
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|transfer-start [channel]|transfer-status|cleanup]",
            source,
        )

    def test_softap_surface_uses_readonly_feasibility_gate(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn('#include "a90_wififeas.h"', source)
        self.assertIn("a90_wififeas_evaluate(&feasibility)", source)
        self.assertIn("wififeas.decision=", source)
        self.assertIn("gates.wlan=", source)
        self.assertIn("softap-status-blocked-wlan-gate", source)
        self.assertIn("softap-prepare-blocked-wlan-gate", source)

    def test_softap_s2_does_not_start_or_expose_services(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("config_write_attempted=0", source)
        self.assertIn("hostapd_start_attempted=0", source)
        self.assertIn("wpa_supplicant_mode2_start_attempted=0", source)
        self.assertIn("dhcp_server_start_attempted=0", source)
        self.assertIn("listener_start_attempted=0", source)
        self.assertIn("interface_mode_change_attempted=0", source)
        self.assertIn("address_assign_attempted=0", source)
        self.assertIn("server_exposure_attempted=0", source)
        self.assertIn("prepare_dry_run=%d", source)
        self.assertIn("start_allowed=%d", source)

    def test_softap_plan_keeps_later_rungs_blocked(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("plan.s2=status-plan-prepare-no-start", source)
        self.assertIn("plan.s3=mode2-ap-start-and-dhcp-done", source)
        self.assertIn("plan.s4=transfer-start-status-cleanup-next", source)

    def test_wifi_lifecycle_doc_mentions_softap_surface(self) -> None:
        doc = WIFI_DOC.read_text(encoding="utf-8")

        self.assertIn("wifi softap status", doc)
        self.assertIn("wifi softap plan", doc)
        self.assertIn("wifi softap prepare [profile]", doc)
        self.assertIn("wifi softap iftype-probe [timeout_ms]", doc)
        self.assertIn("no AP daemon start", doc)


if __name__ == "__main__":
    unittest.main()
