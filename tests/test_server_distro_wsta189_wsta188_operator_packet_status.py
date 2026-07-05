from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta189_wsta188_operator_packet_status.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta189_wsta188_operator_packet_status.py")


class ServerDistroWsta189Wsta188OperatorPacketStatusTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_wsta168_command(self, root: Path) -> tuple[Path, Path]:
        command_json = root / "wsta168_live_command.json"
        command_sh = root / "wsta168_live_command.sh"
        self.write_json(command_json, {
            "schema": "a90-wsta168-seccomp-live-observation-command-v1",
            "state": "READY_TO_RUN_NOT_EXECUTED",
            "command": [
                "python3",
                "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py",
                "--run-dir",
                str(root / "wsta167-live-run"),
            ],
            "required_ack_flags": [],
            "expected_outcome": {},
            "executed": False,
            "secret_values_logged": 0,
        })
        command_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        return command_json, command_sh

    def packet_for(self, root: Path, *, command_json: Path, command_sh: Path) -> dict:
        packet_sh = root / "packet" / runner.wsta188.PACKET_SH_NAME
        packet_md = root / "packet" / runner.wsta188.PACKET_MD_NAME
        command = runner.wsta188.live_command_template(command_json, command_sh)
        return {
            "schema": "a90-wsta188-wsta187-no-load-operator-packet-v1",
            "state": "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF",
            "ready_for_no_load_live": True,
            "default_off": True,
            "source_wsta187_result": runner.rel(root / "source" / "wsta185_result.json"),
            "source_wsta187_run_dir": runner.rel(root / "source"),
            "source_wsta187_decision": "wsta187-blocked-explicit-execution-gate-required",
            "live_command_template": command,
            "live_command_script": runner.rel(packet_sh),
            "operator_acknowledgements_required": runner.wsta188.ACK_FLAGS,
            "operator_preflight_checks": [
                "run-wsta188-immediately-before-attended-live-observation",
                "confirm-WSTA187-source-gate-valid",
                "confirm-final-selftest-fail-zero-after-live-run",
            ],
            "abort_conditions": [
                "source-gate-not-pass",
                "bridge-or-device-health-unclear",
                "operator-not-present",
                "unexpected-seccomp-load-request",
                "unexpected-correct-token-request",
            ],
            "cleanup_expectations": [
                "WSTA167 work image restored to clean hash",
                "no public tunnel to retire",
                "no packet filter state to restore",
            ],
            "safety_boundary": {
                "boot_flash": False,
                "native_reboot": False,
                "wifi_connect": False,
                "dhcp": False,
                "public_tunnel": False,
                "packet_filter_mutation": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
            "json_path": runner.rel(root / "packet" / runner.wsta188.PACKET_JSON_NAME),
            "markdown_path": runner.rel(packet_md),
        }

    def write_packet_result(self, root: Path, *, command_json: Path, command_sh: Path, mutate=None) -> Path:
        packet = self.packet_for(root, command_json=command_json, command_sh=command_sh)
        if mutate:
            mutate(packet)
        payload = {
            "scope": "WSTA188 host-only WSTA187 no-load live operator packet",
            "decision": runner.wsta188.PASS_DECISION,
            "operator_packet": packet,
            "checks": {"operator_packet_valid": True, "wsta187_source_gate_valid": True},
            "safety": {"live_command_executed": False, "wsta187_live_command_executed": False},
        }
        path = root / "packet" / runner.wsta188.PACKET_JSON_NAME
        self.write_json(path, payload)
        return path

    def install_wsta188_fake(self, *, mode: str, calls: list[str]):
        def fake_wsta188(args):
            calls.append("wsta188")
            self.assertTrue(args.prepare_wsta188_operator_packet)
            packet = self.packet_for(args.run_dir, command_json=args.wsta168_command_json, command_sh=args.wsta168_command_sh)
            if mode == "drift":
                packet["operator_acknowledgements_required"] = packet["operator_acknowledgements_required"] + ["--new-ack"]
            result = {
                "scope": "WSTA188 host-only WSTA187 no-load live operator packet",
                "decision": runner.wsta188.PASS_DECISION if mode != "invalid" else "wsta188-blocked-wsta187-source-gate-invalid",
                "operator_packet": packet,
                "checks": {
                    "wsta187_source_gate_valid": mode != "invalid",
                    "operator_packet_valid": mode != "invalid",
                },
                "safety": {
                    "live_command_executed": False,
                    "wsta187_live_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta188.SUMMARY_NAME, result)
            return result

        old = runner.wsta188.run
        runner.wsta188.run = fake_wsta188
        return old

    def restore_wsta188_fake(self, old) -> None:
        runner.wsta188.run = old

    def test_missing_packet_blocks_before_recheck(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="ready", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(root / "missing" / runner.wsta188.PACKET_JSON_NAME),
                ]))
        finally:
            self.restore_wsta188_fake(old)

        self.assertEqual(result["decision"], "wsta189-blocked-operator-packet-missing")
        self.assertEqual(calls, [])

    def test_ready_packet_rechecks_and_reports_ready(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="ready", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                packet_path = self.write_packet_result(root, command_json=command_json, command_sh=command_sh)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(packet_path),
                ]))
                saved = json.loads((root / "status" / runner.STATUS_JSON_NAME).read_text(encoding="utf-8"))
                markdown = (root / "status" / runner.STATUS_MD_NAME).read_text(encoding="utf-8")
        finally:
            self.restore_wsta188_fake(old)

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        self.assertEqual(calls, ["wsta188"])
        status = result["operator_packet_status"]
        self.assertEqual(status["state"], "READY_TO_RUN_NO_LOAD_DEFAULT_OFF")
        self.assertTrue(status["ready_for_no_load_live"])
        self.assertTrue(status["packet_match"])
        self.assertTrue(status["template_match"])
        self.assertEqual(status["recommended_next_action"], "operator-may-run-wsta188-private-shell-wrapper-for-no-load-live")
        self.assertIn("WSTA188 Operator Packet Status", markdown)

    def test_recheck_drift_reports_drift_without_live_execution(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="drift", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                packet_path = self.write_packet_result(root, command_json=command_json, command_sh=command_sh)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(packet_path),
                ]))
        finally:
            self.restore_wsta188_fake(old)

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        status = result["operator_packet_status"]
        self.assertEqual(status["state"], "DRIFT_RECHECK_REQUIRED")
        self.assertFalse(status["ready_for_no_load_live"])
        self.assertFalse(status["packet_match"])
        self.assertTrue(status["template_match"])

    def test_invalid_recheck_blocks_status(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="invalid", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                packet_path = self.write_packet_result(root, command_json=command_json, command_sh=command_sh)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(packet_path),
                ]))
        finally:
            self.restore_wsta188_fake(old)

        self.assertEqual(result["decision"], "wsta189-blocked-wsta188-recheck-invalid")
        self.assertFalse(result["checks"]["wsta188_recheck_valid"])

    def test_invalid_packet_blocks_before_recheck(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="ready", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                packet_path = self.write_packet_result(
                    root,
                    command_json=command_json,
                    command_sh=command_sh,
                    mutate=lambda packet: packet.update({"state": "BAD"}),
                )
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(packet_path),
                ]))
        finally:
            self.restore_wsta188_fake(old)

        self.assertEqual(result["decision"], "wsta189-blocked-operator-packet-invalid")
        self.assertEqual(calls, [])

    def test_public_surfaces_are_redacted_and_host_only(self) -> None:
        calls: list[str] = []
        old = self.install_wsta188_fake(mode="ready", calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                packet_path = self.write_packet_result(root, command_json=command_json, command_sh=command_sh)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "status"),
                    "--wsta188-operator-packet-json",
                    str(packet_path),
                ]))
                summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
                template_text = json.dumps(runner.template(), sort_keys=True)
                markdown = (root / "status" / runner.STATUS_MD_NAME).read_text(encoding="utf-8")
        finally:
            self.restore_wsta188_fake(old)

        for text in (summary_text, template_text, markdown):
            self.assertNotIn("try" + "cloudflare.com", text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn("http" + "://", text.lower())
            self.assertNotIn("https" + "://", text.lower())
            self.assertNotIn("WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD", text)

    def test_print_template_exits_without_recheck(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA189 host-only", payload)
        self.assertIn("--wsta188-operator-packet-json", payload)

    def test_source_keeps_live_and_flash_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("wsta189-wsta188-operator-packet-status-pass", source)
        self.assertIn("READY_TO_RUN_NO_LOAD_DEFAULT_OFF", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"seccomp_filter_loaded": False', source)
        self.assertIn('"correct_wsta161_token_supplied": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
