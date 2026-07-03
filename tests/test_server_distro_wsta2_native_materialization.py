from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py")


class ServerDistroWsta2NativeMaterializationTests(unittest.TestCase):
    def test_runner_pins_v3384_candidate_and_rollback_images(self) -> None:
        self.assertEqual(runner.V3384_VERSION, "0.11.140")
        self.assertEqual(runner.V3384_BUILD, "v3384-server-distro-hardware-contract")
        self.assertEqual(
            runner.V3384_SHA256,
            "47890d04219837af3acb96ad8e281ad4eab0ea3a73ae2641e05633d014979178",
        )
        self.assertIn("v2321", runner.ROLLBACK_IMAGES)
        self.assertIn("v2237", runner.ROLLBACK_IMAGES)
        self.assertIn("v48", runner.ROLLBACK_IMAGES)

    def test_runner_checks_required_contract_lines(self) -> None:
        text = "\n".join(runner.CONTRACT_REQUIRED)

        self.assertTrue(runner.contract_passed(text))
        self.assertFalse(runner.contract_passed(text.replace("A90DHW end=1", "")))
        self.assertIn("A90DHW next.required=wifi-sta-upstream", runner.CONTRACT_REQUIRED)
        self.assertIn(
            "A90DHW public_tunnel.owner=debian native=off inbound_public_ports=0",
            runner.CONTRACT_REQUIRED,
        )

    def test_runner_classifies_wlan0_and_forbidden_workers(self) -> None:
        self.assertTrue(
            runner.native_is_v3384(
                "version: 0.11.140\nbuild: v3384-server-distro-hardware-contract\n"
            )
        )
        self.assertFalse(runner.native_is_v3384("version: 0.11.139\nbuild: v3383\n"))
        self.assertTrue(runner.wlan0_present("[wifi status]\nwlan0_present=1\n"))
        self.assertFalse(runner.wlan0_present("[wifi status]\nwlan0_present=0\n"))
        self.assertTrue(runner.wlan0_admin_up("[wifi status]\nflags=0x1003\n"))
        self.assertFalse(runner.wlan0_admin_up("[wifi status]\nflags=0x1002\n"))
        self.assertFalse(runner.wlan0_admin_up("[wifi status]\nflags=-\n"))
        self.assertEqual(runner.forbidden_workers("PID CMD\n1 init\n"), [])
        self.assertIn("wpa_supplicant", runner.forbidden_workers("123 wpa_supplicant -i wlan0\n"))
        self.assertIn("dhclient", runner.forbidden_workers("124 dhclient -4 wlan0\n"))

    def test_runner_classifies_auto_menu_busy_for_single_hide_retry(self) -> None:
        self.assertTrue(
            runner.is_auto_menu_busy({
                "rc": -16,
                "status": "busy",
                "text": "[busy] auto menu active; send hide/q before command",
            })
        )
        self.assertFalse(runner.is_auto_menu_busy({"rc": -16, "status": "busy", "text": "other busy"}))
        self.assertFalse(runner.is_auto_menu_busy({"rc": 0, "status": "ok", "text": "auto menu active"}))

    def test_runner_live_surface_stays_below_association(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('["server-distro", "hardware-contract"]', source)
        self.assertIn('["wifi", "status"]', source)
        self.assertIn('["wifi", "softap", "iftype-probe"', source)
        self.assertIn("native_init_flash.py", source)
        self.assertIn("--flash-v3384", source)
        self.assertIn("wsta2-blocked-no-native-cmdv1-or-recovery-adb", source)
        self.assertIn("wsta2-blocked-v3384-not-resident", source)
        self.assertIn("needs_iftype_probe", source)
        self.assertIn("wlan0_admin_up", source)
        self.assertIn("auto_menu_retry", source)
        self.assertIn('send_bridge_line(args, "hide"', source)

        for forbidden_command in (
            '["wifi", "connect"',
            '["wifi", "dhcp"',
            '["wifi", "ping"',
            "cloudflared tunnel",
            "ssid=",
            "psk=",
        ):
            self.assertNotIn(forbidden_command, source)


if __name__ == "__main__":
    unittest.main()
