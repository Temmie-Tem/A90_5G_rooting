from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta172_seccomp_fresh_execute_preflight.py")


class ServerDistroWsta172SeccompFreshExecutePreflightTests(unittest.TestCase):
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

    def base_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta172"),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
        ]

    def gated_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.base_args(root, command_json, command_sh) + ["--emit-fresh-wsta170-execute-preflight"]

    def fake_pass_bundle(self, calls: list[str], command_json: Path, command_sh: Path):
        def fake_wsta169(args):
            calls.append("wsta169")
            result = {
                "decision": runner.wsta169.PASS_DECISION,
                "wsta168_command_json": runner.rel(command_json),
                "wsta168_command_sh": runner.rel(command_sh),
                "checks": {
                    "command_ready": True,
                    "bridge_ready": True,
                    "version_ok": True,
                    "status_ok": True,
                    "selftest_fail_zero": True,
                },
                "safety": {
                    "live_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta169.SUMMARY_NAME, result)
            return result

        def fake_wsta170(args):
            calls.append("wsta170")
            self.assertEqual(args.wsta169_readiness_json.name, runner.wsta169.SUMMARY_NAME)
            self.assertFalse(args.execute_wsta170_no_load_live_observation)
            result = {
                "decision": "wsta170-blocked-explicit-execution-gate-required",
                "wsta169_readiness_json": runner.rel(args.wsta169_readiness_json),
                "wsta168_command_json": runner.rel(command_json),
                "wsta168_command_sh": runner.rel(command_sh),
                "checks": {
                    "readiness_proof_valid": True,
                    "command_ready": True,
                },
                "safety": {
                    "device_action": False,
                    "live_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta170.SUMMARY_NAME, result)
            return result

        def fake_wsta171(args):
            calls.append("wsta171")
            self.assertEqual(args.wsta170_source_gate_json.name, runner.wsta170.SUMMARY_NAME)
            self.assertTrue(args.emit_wsta170_execute_preflight)
            result = {
                "decision": runner.wsta171.PASS_DECISION,
                "wsta170_source_gate_json": runner.rel(args.wsta170_source_gate_json),
                "wsta169_readiness_json": runner.rel(args.wsta169_readiness_json),
                "wsta168_command_json": runner.rel(command_json),
                "wsta168_command_sh": runner.rel(command_sh),
                "checks": {
                    "source_gate_valid": True,
                    "readiness_valid": True,
                    "wsta168_command_valid": True,
                    "execution_command_valid": True,
                },
                "command": {
                    "command_json": runner.rel(args.run_dir / runner.wsta171.COMMAND_JSON_NAME),
                    "command_script": runner.rel(args.run_dir / runner.wsta171.COMMAND_SH_NAME),
                    "state": "READY_TO_RUN_NOT_EXECUTED",
                    "executed": False,
                },
                "safety": {
                    "live_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta171.SUMMARY_NAME, result)
            return result

        return fake_wsta169, fake_wsta170, fake_wsta171

    def swap_nested(self, fake_wsta169, fake_wsta170, fake_wsta171):
        old = (runner.wsta169.run, runner.wsta170.run, runner.wsta171.run)
        runner.wsta169.run = fake_wsta169
        runner.wsta170.run = fake_wsta170
        runner.wsta171.run = fake_wsta171
        return old

    def restore_nested(self, old) -> None:
        runner.wsta169.run, runner.wsta170.run, runner.wsta171.run = old

    def test_fresh_bundle_runs_readiness_source_gate_and_preflight(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[str] = []
            old = self.swap_nested(*self.fake_pass_bundle(calls, command_json, command_sh))
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.gated_args(root, command_json, command_sh)
                ))
            finally:
                self.restore_nested(old)

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(calls, ["wsta169", "wsta170", "wsta171"])
        self.assertTrue(result["checks"]["fresh_readiness_valid"])
        self.assertTrue(result["checks"]["source_gate_valid"])
        self.assertTrue(result["checks"]["execute_preflight_valid"])
        self.assertTrue(result["safety"]["wsta170_execute_command_generated"])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_gate_blocks_before_nested_runs(self) -> None:
        def fail(*_args, **_kwargs):
            raise AssertionError("nested runner should not run")

        old = self.swap_nested(fail, fail, fail)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.base_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_nested(old)
        self.assertEqual(result["decision"], "wsta172-blocked-explicit-bundle-gate-required")

    def test_invalid_fresh_readiness_blocks_before_source_gate(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[str] = []

            def bad_wsta169(args):
                calls.append("wsta169")
                result = {
                    "decision": "blocked",
                    "wsta168_command_json": runner.rel(command_json),
                    "wsta168_command_sh": runner.rel(command_sh),
                    "checks": {"command_ready": False},
                    "safety": {
                        "live_command_executed": False,
                        "seccomp_filter_loaded": False,
                        "seccomp_enforced": False,
                        "correct_wsta161_token_supplied": False,
                    },
                }
                self.write_json(args.run_dir / runner.wsta169.SUMMARY_NAME, result)
                return result

            def fail(*_args, **_kwargs):
                raise AssertionError("later nested runner should not run")

            old = self.swap_nested(bad_wsta169, fail, fail)
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.gated_args(root, command_json, command_sh)
                ))
            finally:
                self.restore_nested(old)

        self.assertEqual(result["decision"], "wsta172-blocked-fresh-readiness-invalid")
        self.assertEqual(calls, ["wsta169"])

    def test_invalid_execute_preflight_blocks(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[str] = []
            fake_wsta169, fake_wsta170, fake_wsta171 = self.fake_pass_bundle(calls, command_json, command_sh)

            def bad_wsta171(args):
                result = fake_wsta171(args)
                result["decision"] = "blocked"
                return result

            old = self.swap_nested(fake_wsta169, fake_wsta170, bad_wsta171)
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.gated_args(root, command_json, command_sh)
                ))
            finally:
                self.restore_nested(old)

        self.assertEqual(result["decision"], "wsta172-blocked-execute-preflight-invalid")
        self.assertEqual(calls, ["wsta169", "wsta170", "wsta171"])


if __name__ == "__main__":
    unittest.main()
