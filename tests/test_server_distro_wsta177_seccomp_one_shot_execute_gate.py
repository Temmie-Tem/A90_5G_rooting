from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta177_seccomp_one_shot_execute_gate.py")


class ServerDistroWsta177SeccompOneShotExecuteGateTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_wsta168_command(self, root: Path) -> tuple[Path, Path]:
        payload = {
            "schema": "a90-wsta168-seccomp-live-observation-command-v1",
            "state": "READY_TO_RUN_NOT_EXECUTED",
            "command": [
                "python3",
                "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py",
                "--run-id",
                "wsta168-seccomp-live-observation-execute",
                "--run-dir",
                str(root / "wsta167-live-run"),
                "--execute-seccomp-live-observation",
                "--allow-seccomp-live-observation",
                "--ack-no-correct-wsta161-token",
                "--ack-no-seccomp-load",
                "--ack-cleanup-required",
            ],
            "required_ack_flags": [
                "--execute-seccomp-live-observation",
                "--allow-seccomp-live-observation",
                "--ack-no-correct-wsta161-token",
                "--ack-no-seccomp-load",
                "--ack-cleanup-required",
            ],
            "expected_outcome": {
                "decision": "wsta167-seccomp-live-observation-pass",
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
                "scenario_returncode": 65,
            },
            "executed": False,
            "secret_values_logged": 0,
        }
        command_json = root / "wsta168_live_command.json"
        command_sh = root / "wsta168_live_command.sh"
        self.write_json(command_json, payload)
        command_sh.write_text("#!/bin/sh\nexec true\n", encoding="utf-8")
        return command_json, command_sh

    def write_wsta176_result(self, args, command_json: Path, command_sh: Path, *, bad_command: bool = False) -> dict:
        command = [
            "python3",
            "workspace/public/src/scripts/server-distro/run_wsta175_seccomp_handoff_execute_gate.py",
            "--run-id",
            "wsta176-seccomp-handoff-execute",
            "--run-dir",
            str(args.run_dir / "wsta175-live-run"),
            "--handoff-json",
            str(args.run_dir / "handoff.json"),
            "--execution-timeout",
            "1800.0",
            "--execute-wsta175-handoff",
            "--allow-wsta170-command-execution",
            "--ack-handoff-fresh",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]
        payload = {
            "schema": "a90-wsta176-wsta175-execute-command-v1",
            "state": "READY_TO_RUN_NOT_EXECUTED",
            "command": command,
            "required_ack_flags": [
                "--execute-wsta175-handoff",
                "--allow-wsta170-command-execution",
                "--ack-handoff-fresh",
                "--ack-no-correct-wsta161-token",
                "--ack-no-seccomp-load",
                "--ack-cleanup-required",
            ],
            "expected_outcome": {
                "decision": runner.wsta175.PASS_DECISION,
                "nested_wsta170_decision": runner.wsta175.wsta170.PASS_DECISION,
                "nested_wsta167_decision": runner.wsta175.wsta170.wsta167.PASS_DECISION,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
            "executed": False,
            "secret_values_logged": 0,
        }
        packet_json = args.run_dir / runner.wsta176.COMMAND_JSON_NAME
        packet_sh = args.run_dir / runner.wsta176.COMMAND_SH_NAME
        self.write_json(packet_json, payload)
        script = "#!/bin/sh\nexec " + " ".join(command) + "\n"
        if bad_command:
            script += "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD\n"
        packet_sh.write_text(script, encoding="utf-8")
        result = {
            "decision": runner.wsta176.PASS_DECISION,
            "gate_decision": "ok",
            "wsta168_command_json": runner.rel(command_json),
            "wsta168_command_sh": runner.rel(command_sh),
            "checks": {
                "fresh_handoff_valid": True,
                "source_gate_valid": True,
                "execution_command_valid": True,
            },
            "command": {
                "command_json": runner.rel(packet_json),
                "command_script": runner.rel(packet_sh),
                "state": "READY_TO_RUN_NOT_EXECUTED",
                "executed": False,
            },
            "safety": {
                "live_command_executed": False,
                "wsta175_execute_command_executed": False,
                "wsta170_execute_command_executed": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        }
        self.write_json(args.run_dir / runner.wsta176.SUMMARY_NAME, result)
        return result

    def base_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta177"),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
        ]

    def prepare_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.base_args(root, command_json, command_sh) + ["--prepare-wsta177-one-shot"]

    def execute_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.prepare_args(root, command_json, command_sh) + [
            "--execute-wsta177-one-shot",
            "--allow-wsta175-command-execution",
            "--ack-fresh-preflight",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]

    def test_prepare_gate_generates_fresh_preflight_but_does_not_execute(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[str] = []

            def fake_wsta176(args):
                calls.append("wsta176")
                return self.write_wsta176_result(args, command_json, command_sh)

            old_wsta176 = runner.wsta176.run
            old_exec = runner.run_generated_command
            runner.wsta176.run = fake_wsta176
            runner.run_generated_command = lambda command, *, timeout: (_ for _ in ()).throw(
                AssertionError(f"must not execute: {command} {timeout}")
            )
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
            finally:
                runner.wsta176.run = old_wsta176
                runner.run_generated_command = old_exec

        self.assertEqual(result["decision"], "wsta177-blocked-explicit-execution-gate-required")
        self.assertEqual(calls, ["wsta176"])
        self.assertTrue(result["checks"]["fresh_preflight_valid"])
        self.assertTrue(result["checks"]["execution_command_valid"])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_explicit_gate_executes_generated_command_and_validates_wsta175_result(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[list[str]] = []

            def fake_wsta176(args):
                return self.write_wsta176_result(args, command_json, command_sh)

            def fake_executor(command: list[str], *, timeout: float) -> dict:
                del timeout
                calls.append(command)
                run_dir = runner.command_run_dir(command)
                self.assertIsNotNone(run_dir)
                assert run_dir is not None
                self.write_json(run_dir / runner.wsta175.SUMMARY_NAME, {
                    "decision": runner.wsta175.PASS_DECISION,
                    "checks": {
                        "handoff_valid": True,
                        "handoff_fresh": True,
                        "command_artifacts_valid": True,
                        "execution_returncode_ok": True,
                        "wsta170_result_present": True,
                        "wsta170_result_valid": True,
                    },
                    "safety": {
                        "seccomp_filter_loaded": False,
                        "seccomp_enforced": False,
                        "correct_wsta161_token_supplied": False,
                        "boot_flash": False,
                        "native_reboot": False,
                        "wifi_connect": False,
                        "dhcp": False,
                        "public_tunnel": False,
                        "packet_filter_mutation": False,
                    },
                })
                return {"command": command, "returncode": 0, "stdout": "ok\n", "stderr": ""}

            old_wsta176 = runner.wsta176.run
            old_exec = runner.run_generated_command
            runner.wsta176.run = fake_wsta176
            runner.run_generated_command = fake_executor
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, command_json, command_sh)
                ))
            finally:
                runner.wsta176.run = old_wsta176
                runner.run_generated_command = old_exec

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(len(calls), 1)
        self.assertTrue(result["checks"]["wsta175_result_valid"])
        self.assertTrue(result["safety"]["live_command_executed"])

    def test_missing_prepare_gate_blocks_before_wsta176(self) -> None:
        def fail(*_args, **_kwargs):
            raise AssertionError("wsta176 should not run")

        old_wsta176 = runner.wsta176.run
        runner.wsta176.run = fail
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.base_args(root, command_json, command_sh)
                ))
        finally:
            runner.wsta176.run = old_wsta176

        self.assertEqual(result["decision"], "wsta177-blocked-explicit-prepare-gate-required")

    def test_invalid_generated_command_blocks_before_execution(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)

            def fake_wsta176(args):
                return self.write_wsta176_result(args, command_json, command_sh, bad_command=True)

            old_wsta176 = runner.wsta176.run
            old_exec = runner.run_generated_command
            runner.wsta176.run = fake_wsta176
            runner.run_generated_command = lambda command, *, timeout: (_ for _ in ()).throw(
                AssertionError(f"must not execute: {command} {timeout}")
            )
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, command_json, command_sh)
                ))
            finally:
                runner.wsta176.run = old_wsta176
                runner.run_generated_command = old_exec

        self.assertEqual(result["decision"], "wsta177-blocked-execution-command-invalid")
        self.assertFalse(result["execution_command_checks"]["correct_token_literal_absent"])


if __name__ == "__main__":
    unittest.main()
