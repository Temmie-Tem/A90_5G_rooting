from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta15_handoff_scan_boundary.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta15_handoff_scan_boundary.py")


class ServerDistroWsta15HandoffScanBoundaryTests(unittest.TestCase):
    def test_scan_summary_parses_native_scan_markers(self) -> None:
        record = {
            "transport_ok": True,
            "status": "ok",
            "rc": 0,
            "text": "\n".join((
                "[wifi scan]",
                "link_up_rc=0",
                "link_up_errno=0",
                "ifindex=7",
                "netlink_open=1",
                "family_id=23",
                "trigger_rc=0",
                "trigger_errno=0",
                "scan_result_count=3",
                "decision=wifi-scan-pass",
            )),
        }

        summary = runner.scan_summary(record)

        self.assertTrue(summary["scan_engine_ok"])
        self.assertTrue(summary["scan_has_bss"])
        self.assertEqual(summary["scan_result_count"], 3)
        self.assertEqual(summary["link_up_rc"], 0)
        self.assertEqual(summary["ifindex"], 7)

    def test_scan_summary_treats_zero_bss_as_engine_ok_without_visibility(self) -> None:
        summary = runner.scan_summary({
            "transport_ok": True,
            "status": "error",
            "rc": -61,
            "text": "scan_result_count=0\ndecision=wifi-scan-zero-bss\n",
        })

        self.assertTrue(summary["scan_engine_ok"])
        self.assertFalse(summary["scan_has_bss"])

    def test_best_scan_prefers_visible_bss_over_zero_bss(self) -> None:
        zero = {"scan_summary": runner.scan_summary({"text": "scan_result_count=0\ndecision=wifi-scan-zero-bss\n"})}
        pass_scan = {"scan_summary": runner.scan_summary({"text": "scan_result_count=2\ndecision=wifi-scan-pass\n"})}

        self.assertEqual(runner.best_scan([zero, pass_scan])["scan_result_count"], 2)

    def test_boundary_classification_splits_iftype_poison_cases(self) -> None:
        base = {
            "iftype_probe_requested": True,
            "checks": {
                "native_v3384": True,
                "selftest_fail_zero": True,
                "hardware_contract_ok": True,
                "process_table_ok": True,
                "forbidden_native_workers": [],
            },
        }

        survives = {
            **base,
            "pre_sta_only_scan_window": {"best": {"scan_engine_ok": True}},
            "post_iftype_scan_window": {"best": {"scan_engine_ok": True}},
        }
        regressed = {
            **base,
            "pre_sta_only_scan_window": {"best": {"scan_engine_ok": True}},
            "post_iftype_scan_window": {"best": {"scan_engine_ok": False}},
        }
        recovered = {
            **base,
            "pre_sta_only_scan_window": {"best": {"scan_engine_ok": False}},
            "post_iftype_scan_window": {"best": {"scan_engine_ok": True}},
        }

        self.assertEqual(runner.classify_boundary(survives), "wsta15-native-scan-engine-survives-iftype")
        self.assertEqual(runner.classify_boundary(regressed), "wsta15-native-post-iftype-scan-regressed")
        self.assertEqual(runner.classify_boundary(recovered), "wsta15-native-sta-only-scan-blocked-iftype-recovers")

    def test_runner_live_surface_stays_below_association_and_flash(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('["version"]', source)
        self.assertIn('["server-distro", "hardware-contract"]', source)
        self.assertIn('["wifi", "scan", str(args.scan_delay_ms)]', source)
        self.assertIn('["wifi", "softap", "iftype-probe"', source)
        self.assertIn('"flash_requested": False', source)
        self.assertIn('"no_wifi_association": True', source)
        self.assertNotIn("--flash-v3384", source)
        self.assertNotIn("native_init_flash.py", source)

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
