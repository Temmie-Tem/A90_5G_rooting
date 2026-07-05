from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta188_wsta187_operator_packet.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta188_wsta187_operator_packet.py")


class ServerDistroWsta188Wsta187OperatorPacketTests(unittest.TestCase):
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

    def base_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta188"),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
        ]

    def prepare_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.base_args(root, command_json, command_sh) + [
            "--prepare-wsta188-operator-packet",
        ]

    def install_wsta187_fake(self, *, valid: bool, calls: list[str]):
        def fake_wsta187(args):
            calls.append("wsta187")
            self.assertTrue(args.prepare_wsta187_fresh_orchestrator)
            self.assertFalse(args.execute_wsta187_fresh_orchestrator)
            result = {
                "scope": "WSTA187 fresh WSTA185 no-load live orchestrator",
                "decision": (
                    "wsta187-blocked-explicit-execution-gate-required"
                    if valid
                    else "wsta187-blocked-wsta178-preflight-invalid"
                ),
                "run_dir": runner.rel(args.run_dir),
                "checks": {
                    "wsta177_source_valid": valid,
                    "wsta178_preflight_valid": valid,
                    "wsta180_bundle_valid": valid,
                    "wsta184_handoff_valid": valid,
                    "wsta185_source_valid": valid,
                    "explicit_execution_gate": False,
                },
                "stages": {
                    "wsta185": {
                        "result_json": runner.rel(args.run_dir / "wsta185-source-gate" / runner.wsta187.wsta185.SUMMARY_NAME),
                    },
                },
                "safety": {
                    "live_command_executed": False,
                    "wsta185_execute_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta187.SUMMARY_NAME, result)
            return result

        old = runner.wsta187.run
        runner.wsta187.run = fake_wsta187
        return old

    def restore_wsta187_fake(self, old) -> None:
        runner.wsta187.run = old

    def test_missing_prepare_gate_blocks_before_source_gate(self) -> None:
        calls: list[str] = []
        old = self.install_wsta187_fake(valid=True, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.base_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_wsta187_fake(old)

        self.assertEqual(result["decision"], "wsta188-blocked-explicit-prepare-gate-required")
        self.assertEqual(calls, [])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_prepare_renders_operator_packet_without_live_execution(self) -> None:
        calls: list[str] = []
        old = self.install_wsta187_fake(valid=True, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
                saved = json.loads((root / "wsta188" / runner.PACKET_JSON_NAME).read_text(encoding="utf-8"))
                script = (root / "wsta188" / runner.PACKET_SH_NAME).read_text(encoding="utf-8")
                markdown = (root / "wsta188" / runner.PACKET_MD_NAME).read_text(encoding="utf-8")
        finally:
            self.restore_wsta187_fake(old)

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        self.assertEqual(calls, ["wsta187"])
        self.assertTrue(result["checks"]["wsta187_source_gate_valid"])
        self.assertTrue(result["checks"]["operator_packet_valid"])
        self.assertFalse(result["safety"]["wsta187_live_command_executed"])
        packet = result["operator_packet"]
        self.assertEqual(packet["state"], "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF")
        self.assertIn("--execute-wsta187-fresh-orchestrator", packet["operator_acknowledgements_required"])
        self.assertIn("--ack-no-seccomp-load", packet["operator_acknowledgements_required"])
        self.assertIn("<fresh-timestamp>", json.dumps(packet["live_command_template"]))
        self.assertIn("${ts}", script)
        self.assertIn("PYTHONPYCACHEPREFIX", script)
        self.assertIn("WSTA187 No-Load Live Operator Packet", markdown)

    def test_invalid_wsta187_source_gate_blocks_packet(self) -> None:
        calls: list[str] = []
        old = self.install_wsta187_fake(valid=False, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_wsta187_fake(old)

        self.assertEqual(result["decision"], "wsta188-blocked-wsta187-source-gate-invalid")
        self.assertEqual(calls, ["wsta187"])
        self.assertFalse(result["checks"]["wsta187_source_gate_valid"])
        self.assertNotIn("operator_packet", result)

    def test_public_surfaces_are_redacted_and_host_only(self) -> None:
        calls: list[str] = []
        old = self.install_wsta187_fake(valid=True, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
                summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
                template_text = json.dumps(runner.template(), sort_keys=True)
                markdown = (root / "wsta188" / runner.PACKET_MD_NAME).read_text(encoding="utf-8")
        finally:
            self.restore_wsta187_fake(old)

        for text in (summary_text, template_text, markdown):
            self.assertNotIn("try" + "cloudflare.com", text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn("http" + "://", text.lower())
            self.assertNotIn("https" + "://", text.lower())
            self.assertNotIn("WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD", text)

    def test_print_template_exits_without_source_gate(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA188 host-only", payload)
        self.assertIn("--prepare-wsta188-operator-packet", payload)

    def test_source_keeps_live_and_flash_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("wsta188-wsta187-operator-packet-pass", source)
        self.assertIn("READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"seccomp_filter_loaded": False', source)
        self.assertIn('"correct_wsta161_token_supplied": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
