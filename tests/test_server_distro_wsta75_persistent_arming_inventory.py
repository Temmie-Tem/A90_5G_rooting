from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


wsta72 = load_script("workspace/public/src/scripts/server-distro/run_wsta72_persistent_prepare_to_arm.py")
wsta73 = load_script("workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py")
wsta74 = load_script("workspace/public/src/scripts/server-distro/run_wsta74_persistent_arming_status.py")
runner = load_script("workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py")


class ServerDistroWsta75PersistentArmingInventoryTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def prepare_packet(self, root: Path, label: str, ttl_sec: int = 300) -> dict[str, Path]:
        base = root / label
        prepare_args = wsta72.build_arg_parser().parse_args([
            "--run-dir",
            str(base / "prepare"),
            "--prepare-to-arm",
            "--ttl-sec",
            str(ttl_sec),
            "--ack-credentialed-wifi",
            "--ack-public-exposure",
            "--native-confirm-token-source",
            "private",
            "--public-confirm-token-source",
            "private",
        ])
        self.assertEqual(wsta72.run(prepare_args)["decision"], wsta72.PASS_DECISION)
        packet_args = wsta73.build_arg_parser().parse_args([
            "--run-dir",
            str(base / "packet"),
            "--wsta72-prepare-to-arm-json",
            str(base / "prepare" / "wsta72_prepare_to_arm.json"),
        ])
        self.assertEqual(wsta73.run(packet_args)["decision"], wsta73.PASS_DECISION)
        return {
            "prepare": base / "prepare" / "wsta72_prepare_to_arm.json",
            "packet": base / "packet" / "wsta73_arming_packet.json",
            "initial": base / "prepare" / "wsta63" / "initial-wsta54" / "wsta54_private_lease.json",
        }

    def test_default_inventory_scan_is_host_only_and_private(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            with mock.patch.object(runner.wsta74.wsta73.wsta71.wsta65.wsta64.wsta58.wsta55, "run", side_effect=AssertionError("unexpected live WSTA55")):
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "inventory"),
                    "--scan-root",
                    str(root),
                ]))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(result["arming_inventory"]["packet_count"], 0)
        self.assertEqual(result["arming_inventory"]["overall_state"], "NO_ARMING_PACKETS_FOUND")
        for key in (
            "device_action",
            "boot_flash",
            "native_reboot",
            "wifi_connect",
            "dhcp",
            "public_tunnel",
            "public_smoke",
            "userdata_touch",
            "switch_root",
        ):
            self.assertFalse(result["safety"][key])

    def test_inventory_rechecks_ready_and_stale_packets(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            ready = self.prepare_packet(root, "ready", ttl_sec=300)
            stale = self.prepare_packet(root, "stale", ttl_sec=60)
            stale_artifact = json.loads(stale["initial"].read_text(encoding="utf-8"))
            expires = runner.wsta74.wsta73.wsta72.wsta67.wsta65.wsta64.parse_utc_stamp(stale_artifact["expires_utc"])
            self.assertIsNotNone(expires)
            now = expires - runner._dt.timedelta(seconds=10)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "inventory"),
                "--scan-root",
                str(root),
                "--min-initial-seconds-remaining",
                "30",
                "--now-utc",
                runner.utc_stamp(now),
            ]))
            saved = json.loads((root / "inventory" / "wsta75_arming_inventory.json").read_text(encoding="utf-8"))
            markdown = (root / "inventory" / "wsta75_arming_inventory.md").read_text(encoding="utf-8")

        inventory = result["arming_inventory"]
        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        self.assertEqual(inventory["packet_count"], 2)
        self.assertEqual(inventory["ready_count"], 1)
        self.assertEqual(inventory["stale_count"], 1)
        self.assertEqual(inventory["overall_state"], "READY_PACKET_PRESENT_DEFAULT_OFF")
        self.assertEqual(inventory["selected_ready_packet"]["state"], "READY_TO_EXECUTE_DEFAULT_OFF")
        self.assertEqual(inventory["selected_ready_packet"]["wsta73_arming_packet"], runner.rel(ready["packet"]))
        states = {entry["wsta73_arming_packet"]: entry["state"] for entry in inventory["entries"]}
        self.assertEqual(states[runner.rel(ready["packet"])], "READY_TO_EXECUTE_DEFAULT_OFF")
        self.assertEqual(states[runner.rel(stale["packet"])], "STALE_OR_NOT_READY")
        self.assertIn("WSTA Persistent Arming Packet Inventory", markdown)
        self.assertFalse(result["checks"]["live_execution_requested"])

    def test_inventory_excludes_nested_wsta74_recheck_packets(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            artifacts = self.prepare_packet(root, "ready")
            status_result = wsta74.run(wsta74.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "status"),
                "--wsta73-arming-packet-json",
                str(artifacts["packet"]),
            ]))
            self.assertEqual(status_result["decision"], wsta74.PASS_DECISION)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "inventory"),
                "--scan-root",
                str(root),
            ]))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(result["arming_inventory"]["packet_count"], 1)
        self.assertEqual(result["arming_inventory"]["entries"][0]["wsta73_arming_packet"], runner.rel(artifacts["packet"]))

    def test_nonprivate_scan_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(runner.DEFAULT_RUN_BASE / "wsta75-nonprivate-test"),
                "--scan-root",
                tmp,
            ]))

        self.assertEqual(result["decision"], "wsta75-blocked-nonprivate-scan-root")

    def test_public_summary_markdown_and_template_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            self.prepare_packet(root, "ready")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "inventory"),
                "--scan-root",
                str(root),
            ]))
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            template_text = json.dumps(runner.template(), sort_keys=True)
            markdown = (root / "inventory" / "wsta75_arming_inventory.md").read_text(encoding="utf-8")
        tunnel_domain = "try" + "cloudflare.com"
        http_scheme = "http" + "://"
        https_scheme = "https" + "://"

        for text in (summary_text, template_text, markdown):
            self.assertNotIn(tunnel_domain, text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn(http_scheme, text.lower())
            self.assertNotIn(https_scheme, text.lower())
            self.assertNotIn(runner.wsta74.wsta73.wsta72.wsta63.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN, text)
            self.assertNotIn(runner.wsta74.wsta73.wsta72.wsta63.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN, text)

    def test_print_template_exits_without_inventory(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA75 host-only", payload)
        self.assertIn("--scan-root", payload)

    def test_source_keeps_live_and_raw_public_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("READY_PACKET_PRESENT_DEFAULT_OFF", source)
        self.assertIn("wsta75-persistent-arming-inventory-pass", source)
        self.assertIn("wsta74_rechecked", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"public_url_value_logged": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("a90ctl.py", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
