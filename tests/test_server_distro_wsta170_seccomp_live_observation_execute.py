from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta170_seccomp_live_observation_execute.py")


class ServerDistroWsta170SeccompLiveObservationExecuteTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_wsta168_command(self, root: Path, *, correct_token: bool = False) -> tuple[Path, Path, list[str], Path]:
        nested_run_dir = root / "wsta167-live-run"
        command = [
            "python3",
            "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py",
            "--run-id",
            "wsta168-seccomp-live-observation-execute",
            "--run-dir",
            str(nested_run_dir),
            "--execute-seccomp-live-observation",
            "--allow-seccomp-live-observation",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]
        payload = {
            "schema": "a90-wsta168-seccomp-live-observation-command-v1",
            "state": "READY_TO_RUN_NOT_EXECUTED",
            "command": command,
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
        script = "#!/bin/sh\nexec " + " ".join(command) + "\n"
        if correct_token:
            script += "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD\n"
        command_sh.write_text(script, encoding="utf-8")
        return command_json, command_sh, command, nested_run_dir

    def write_wsta169_proof(self, path: Path, command_json: Path, command_sh: Path, *, decision: str | None = None) -> None:
        command_checks = {
            "command_json_present": True,
            "command_sh_present": True,
            "schema_ok": True,
            "ready_not_executed": True,
            "payload_not_executed": True,
            "command_targets_wsta167": True,
            "script_targets_wsta167": True,
            "all_ack_flags_present": True,
            "correct_token_absent": True,
            "expected_no_load": True,
            "expected_no_enforce": True,
        }
        self.write_json(path, {
            "decision": decision or runner.wsta169.PASS_DECISION,
            "wsta168_command_json": runner.rel(command_json),
            "wsta168_command_sh": runner.rel(command_sh),
            "checks": {
                "explicit_gate": True,
                "command_ready": True,
                "bridge_ready": True,
                "version_ok": True,
                "status_ok": True,
                "selftest_fail_zero": True,
            },
            "command_checks": command_checks,
            "safety": {
                "live_command_executed": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        })

    def base_args(self, root: Path, proof: Path, command_json: Path, command_sh: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta170"),
            "--wsta169-readiness-json",
            str(proof),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
        ]

    def execute_args(self, root: Path, proof: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.base_args(root, proof, command_json, command_sh) + [
            "--execute-wsta170-no-load-live-observation",
            "--allow-wsta168-command-execution",
            "--ack-readiness-proof-current",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]

    def test_default_blocks_after_validating_readiness_and_command(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh, _command, _nested = self.write_wsta168_command(root)
            proof = root / "wsta169_result.json"
            self.write_wsta169_proof(proof, command_json, command_sh)

            old_executor = runner.run_generated_command
            runner.run_generated_command = lambda command, *, timeout: (_ for _ in ()).throw(
                AssertionError(f"must not execute: {command} {timeout}")
            )
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.base_args(root, proof, command_json, command_sh)
                ))
            finally:
                runner.run_generated_command = old_executor

        self.assertEqual(result["decision"], "wsta170-blocked-explicit-execution-gate-required")
        self.assertTrue(result["checks"]["readiness_proof_valid"])
        self.assertTrue(result["checks"]["command_ready"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertFalse(result["safety"]["device_action"])

    def test_explicit_gate_executes_generated_command_and_accepts_nested_pass(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh, expected_command, nested_run_dir = self.write_wsta168_command(root)
            proof = root / "wsta169_result.json"
            self.write_wsta169_proof(proof, command_json, command_sh)
            calls: list[list[str]] = []

            def fake_executor(command: list[str], *, timeout: float) -> dict:
                del timeout
                calls.append(command)
                self.write_json(nested_run_dir / runner.wsta167.RESULT_NAME, {
                    "decision": runner.wsta167.PASS_DECISION,
                    "checks": {
                        "observation_pass": True,
                        "chroot_cleanup_ok": True,
                        "final_selftest_fail_zero": True,
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

            old_executor = runner.run_generated_command
            runner.run_generated_command = fake_executor
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, proof, command_json, command_sh)
                ))
            finally:
                runner.run_generated_command = old_executor

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(calls, [expected_command])
        self.assertTrue(result["checks"]["nested_result_valid"])
        self.assertEqual(result["nested_result"]["decision"], runner.wsta167.PASS_DECISION)
        self.assertTrue(result["safety"]["live_command_executed"])

    def test_invalid_readiness_or_command_blocks_before_execution(self) -> None:
        def fail_executor(command: list[str], *, timeout: float) -> dict:
            raise AssertionError(f"must not execute: {command} {timeout}")

        old_executor = runner.run_generated_command
        runner.run_generated_command = fail_executor
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh, _command, _nested = self.write_wsta168_command(root)
                proof = root / "wsta169_result.json"
                self.write_wsta169_proof(proof, command_json, command_sh, decision="blocked")
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, proof, command_json, command_sh)
                ))
            self.assertEqual(result["decision"], "wsta170-blocked-readiness-proof-invalid")

            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh, _command, _nested = self.write_wsta168_command(root, correct_token=True)
                proof = root / "wsta169_result.json"
                self.write_wsta169_proof(proof, command_json, command_sh)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, proof, command_json, command_sh)
                ))
            self.assertEqual(result["decision"], "wsta170-blocked-command-invalid")
            self.assertFalse(result["command_checks"]["correct_token_absent"])
        finally:
            runner.run_generated_command = old_executor

    def test_execution_without_nested_result_blocks(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh, _command, _nested = self.write_wsta168_command(root)
            proof = root / "wsta169_result.json"
            self.write_wsta169_proof(proof, command_json, command_sh)

            old_executor = runner.run_generated_command
            runner.run_generated_command = lambda command, *, timeout: {
                "command": command,
                "returncode": 0,
                "stdout": "ok\n",
                "stderr": "",
            }
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, proof, command_json, command_sh)
                ))
            finally:
                runner.run_generated_command = old_executor

        self.assertEqual(result["decision"], "wsta170-blocked-nested-result-missing")
        self.assertFalse(result["checks"]["nested_result_present"])


if __name__ == "__main__":
    unittest.main()
