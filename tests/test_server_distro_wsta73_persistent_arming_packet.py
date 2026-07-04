from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


wsta72 = load_script("workspace/public/src/scripts/server-distro/run_wsta72_persistent_prepare_to_arm.py")
runner = load_script("workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py")


class ServerDistroWsta73PersistentArmingPacketTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def prepare_to_arm(self, root: Path, ttl_sec: int = 300) -> Path:
        args = wsta72.build_arg_parser().parse_args([
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
        self.assertEqual(wsta72.run(args)["decision"], wsta72.PASS_DECISION)
        return root / "prepare" / "wsta72_prepare_to_arm.json"

    def test_default_run_is_fail_closed_and_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(Path(tmp) / "run"),
            ]))

        self.assertEqual(result["decision"], "wsta73-blocked-prepare-to-arm-required")
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

    def test_valid_prepare_to_arm_renders_arming_packet(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            prepare = self.prepare_to_arm(root)
            with mock.patch.object(runner.wsta71.wsta65.wsta64.wsta58.wsta55, "run", side_effect=AssertionError("unexpected live WSTA55")):
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "arming"),
                    "--wsta72-prepare-to-arm-json",
                    str(prepare),
                ]))
            saved = json.loads((root / "arming" / "wsta73_arming_packet.json").read_text(encoding="utf-8"))
            markdown = (root / "arming" / "wsta73_arming_packet.md").read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        packet = result["arming_packet"]
        self.assertEqual(packet["state"], "ARMING_PACKET_READY_DEFAULT_OFF")
        self.assertEqual(packet["wsta65_session_state"], "READY")
        self.assertTrue(packet["ready_for_live"])
        self.assertIn("--execute-renewal-manual-stop", packet["wsta58_live_command_template"])
        self.assertIn("<native-confirm-token>", packet["wsta58_live_command_template"])
        self.assertIn("<public-confirm-token>", packet["wsta58_live_command_template"])
        self.assertIn("--force-manual-stop-proof", packet["operator_acknowledgements_required"])
        self.assertIn("wsta71_recheck_not_pass", packet["abort_conditions"])
        self.assertIn("PUBLIC_OFF", " ".join(packet["cleanup_expectations"]))
        self.assertIn("WSTA Persistent Arming Packet", markdown)
        self.assertFalse(result["checks"]["live_execution_requested"])

    def test_prepare_to_arm_that_ages_stale_blocks_on_wsta71_recheck(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            prepare = self.prepare_to_arm(root, ttl_sec=60)
            initial = root / "prepare" / "wsta63" / "initial-wsta54" / "wsta54_private_lease.json"
            artifact = json.loads(initial.read_text(encoding="utf-8"))
            expires = runner.wsta71.wsta65.wsta64.parse_utc_stamp(artifact["expires_utc"])
            self.assertIsNotNone(expires)
            later = runner.wsta72.wsta67.utc_stamp(expires - runner._dt.timedelta(seconds=10))
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "arming"),
                "--wsta72-prepare-to-arm-json",
                str(prepare),
                "--now-utc",
                later,
            ]))

        self.assertEqual(result["decision"], "wsta73-blocked-wsta71-recheck")
        self.assertEqual(result["gate_detail"]["wsta71_decision"], "wsta71-blocked-launch-not-ready")
        self.assertEqual(result["gate_detail"]["wsta71_gate_detail"]["session_state"], "STALE")

    def test_nonpass_prepare_to_arm_is_rejected(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            prepare = root / "bad" / "wsta72_prepare_to_arm.json"
            prepare.parent.mkdir(parents=True)
            prepare.write_text(json.dumps({
                "decision": "wsta72-blocked-wsta70",
                "pipeline": {"state": "NOT_READY"},
            }), encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "arming"),
                "--wsta72-prepare-to-arm-json",
                str(prepare),
            ]))

        self.assertEqual(result["decision"], "wsta73-blocked-prepare-to-arm-not-pass")

    def test_public_summary_markdown_and_template_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            prepare = self.prepare_to_arm(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "arming"),
                "--wsta72-prepare-to-arm-json",
                str(prepare),
            ]))
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            template_text = json.dumps(runner.template(), sort_keys=True)
            markdown = (root / "arming" / "wsta73_arming_packet.md").read_text(encoding="utf-8")
        tunnel_domain = "try" + "cloudflare.com"
        http_scheme = "http" + "://"
        https_scheme = "https" + "://"

        for text in (summary_text, template_text, markdown):
            self.assertNotIn(tunnel_domain, text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn(http_scheme, text.lower())
            self.assertNotIn(https_scheme, text.lower())
            self.assertNotIn(runner.wsta72.wsta63.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN, text)
            self.assertNotIn(runner.wsta72.wsta63.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN, text)

    def test_print_template_exits_without_packet(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA73 host-only", payload)
        self.assertIn("--wsta72-prepare-to-arm-json", payload)

    def test_source_keeps_live_and_raw_public_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("ARMING_PACKET_READY_DEFAULT_OFF", source)
        self.assertIn("wsta73-persistent-arming-packet-pass", source)
        self.assertIn("operator_acknowledgements_required", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"public_url_value_logged": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("a90ctl.py", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
