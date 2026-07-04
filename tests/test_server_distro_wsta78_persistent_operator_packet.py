from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


wsta72 = load_script("workspace/public/src/scripts/server-distro/run_wsta72_persistent_prepare_to_arm.py")
wsta73 = load_script("workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py")
wsta75 = load_script("workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py")
wsta76 = load_script("workspace/public/src/scripts/server-distro/run_wsta76_persistent_launch_brief.py")
wsta77 = load_script("workspace/public/src/scripts/server-distro/run_wsta77_persistent_launch_brief_summary.py")
runner = load_script("workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py")


class ServerDistroWsta78PersistentOperatorPacketTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def prepare_summary(self, root: Path, ttl_sec: int = 300) -> dict[str, Path]:
        prepare_args = wsta72.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "prepare"),
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
            str(root / "packet"),
            "--wsta72-prepare-to-arm-json",
            str(root / "prepare" / "wsta72_prepare_to_arm.json"),
        ])
        self.assertEqual(wsta73.run(packet_args)["decision"], wsta73.PASS_DECISION)
        inventory_args = wsta75.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "inventory"),
            "--scan-root",
            str(root),
        ])
        self.assertEqual(wsta75.run(inventory_args)["decision"], wsta75.PASS_DECISION)
        brief_args = wsta76.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "brief"),
            "--wsta75-arming-inventory-json",
            str(root / "inventory" / "wsta75_arming_inventory.json"),
        ])
        self.assertEqual(wsta76.run(brief_args)["decision"], wsta76.PASS_DECISION)
        summary_args = wsta77.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "summary"),
            "--scan-root",
            str(root),
        ])
        self.assertEqual(wsta77.run(summary_args)["decision"], wsta77.PASS_DECISION)
        return {
            "summary": root / "summary" / "wsta77_launch_brief_summary.json",
            "brief": root / "brief" / "wsta76_launch_brief.json",
            "packet": root / "packet" / "wsta73_arming_packet.json",
            "initial": root / "prepare" / "wsta63" / "initial-wsta54" / "wsta54_private_lease.json",
        }

    def test_default_run_is_fail_closed_and_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            with mock.patch.object(runner.wsta77.wsta76.wsta75.wsta74.wsta73.wsta71.wsta65.wsta64.wsta58.wsta55, "run", side_effect=AssertionError("unexpected live WSTA55")):
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "packet"),
                ]))

        self.assertEqual(result["decision"], "wsta78-blocked-summary-required")
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

    def test_ready_summary_rechecks_and_writes_operator_packet(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            artifacts = self.prepare_summary(root)
            with mock.patch.object(runner.wsta77.wsta76.wsta75.wsta74.wsta73.wsta71.wsta65.wsta64.wsta58.wsta55, "run", side_effect=AssertionError("unexpected live WSTA55")):
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "operator"),
                    "--wsta77-launch-summary-json",
                    str(artifacts["summary"]),
                ]))
            saved = json.loads((root / "operator" / "wsta78_operator_packet.json").read_text(encoding="utf-8"))
            markdown = (root / "operator" / "wsta78_operator_packet.md").read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        packet = result["operator_packet"]
        self.assertEqual(packet["state"], "READY_OPERATOR_PACKET_DEFAULT_OFF")
        self.assertEqual(packet["selected_wsta73_arming_packet"], runner.rel(artifacts["packet"]))
        self.assertEqual(packet["selected_wsta76_launch_brief"], runner.rel(artifacts["brief"]))
        self.assertTrue(packet["fresh_wsta76_launch_brief"].endswith("wsta76_launch_brief.json"))
        self.assertTrue(packet["ready_for_live"])
        self.assertIn("<native-confirm-token>", packet["operator_required_replacements"])
        self.assertIn("<public-confirm-token>", packet["operator_required_replacements"])
        self.assertIn("--allow-public-live", packet["operator_acknowledgements_required"])
        self.assertIn("wsta78-does-not-execute-live", packet["execution_guardrails"])
        self.assertTrue(packet["wsta58_live_command_template"])
        self.assertFalse(result["checks"]["live_execution_requested"])
        self.assertIn("WSTA Persistent Operator Packet", markdown)

    def test_summary_that_ages_stale_blocks_on_fresh_recheck(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            artifacts = self.prepare_summary(root, ttl_sec=60)
            initial = json.loads(artifacts["initial"].read_text(encoding="utf-8"))
            expires = runner.wsta77.wsta76.wsta75.wsta74.wsta73.wsta72.wsta67.wsta65.wsta64.parse_utc_stamp(initial["expires_utc"])
            self.assertIsNotNone(expires)
            later = runner.utc_stamp(expires - runner._dt.timedelta(seconds=10))
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "operator"),
                "--wsta77-launch-summary-json",
                str(artifacts["summary"]),
                "--min-initial-seconds-remaining",
                "30",
                "--now-utc",
                later,
            ]))

        self.assertEqual(result["decision"], "wsta78-blocked-no-ready-brief")
        self.assertEqual(result["gate_detail"]["overall_state"], "NO_READY_BRIEF")
        self.assertIn("STALE_OR_NOT_READY", result["gate_detail"]["state_counts"])

    def test_nonpass_summary_is_rejected(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            summary = root / "bad" / "wsta77_launch_brief_summary.json"
            summary.parent.mkdir(parents=True)
            summary.write_text(json.dumps({
                "decision": "wsta77-blocked-redaction-finding",
                "launch_summary": {},
            }), encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "operator"),
                "--wsta77-launch-summary-json",
                str(summary),
            ]))

        self.assertEqual(result["decision"], "wsta78-blocked-summary-not-pass")

    def test_ready_index_out_of_range_blocks(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            artifacts = self.prepare_summary(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "operator"),
                "--wsta77-launch-summary-json",
                str(artifacts["summary"]),
                "--ready-index",
                "3",
            ]))

        self.assertEqual(result["decision"], "wsta78-blocked-ready-index-out-of-range")

    def test_public_summary_markdown_and_template_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            artifacts = self.prepare_summary(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "operator"),
                "--wsta77-launch-summary-json",
                str(artifacts["summary"]),
            ]))
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            template_text = json.dumps(runner.template(), sort_keys=True)
            markdown = (root / "operator" / "wsta78_operator_packet.md").read_text(encoding="utf-8")
        tunnel_domain = "try" + "cloudflare.com"
        http_scheme = "http" + "://"
        https_scheme = "https" + "://"

        for text in (summary_text, template_text, markdown):
            self.assertNotIn(tunnel_domain, text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn(http_scheme, text.lower())
            self.assertNotIn(https_scheme, text.lower())
            self.assertNotIn(runner.wsta77.wsta76.wsta75.wsta74.wsta73.wsta72.wsta63.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN, text)
            self.assertNotIn(runner.wsta77.wsta76.wsta75.wsta74.wsta73.wsta72.wsta63.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN, text)

    def test_print_template_exits_without_packet(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA78 host-only", payload)
        self.assertIn("--wsta77-launch-summary-json", payload)

    def test_source_keeps_live_and_raw_public_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("READY_OPERATOR_PACKET_DEFAULT_OFF", source)
        self.assertIn("wsta78-persistent-operator-packet-pass", source)
        self.assertIn("wsta77_rechecked", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"public_url_value_logged": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("a90ctl.py", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
