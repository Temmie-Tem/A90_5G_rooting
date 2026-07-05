from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta183_seccomp_fresh_readiness_status.py")


class ServerDistroWsta183SeccompFreshReadinessStatusTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_bundle(self, root: Path) -> tuple[Path, Path]:
        bundle_json = root / "wsta180_operator_handoff.json"
        bundle_sh = root / "wsta180_operator_handoff_commands.sh"
        bundle_json.parent.mkdir(parents=True, exist_ok=True)
        bundle_json.write_text('{"schema":"a90-wsta180-seccomp-live-handoff-bundle-v1"}\n', encoding="utf-8")
        bundle_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        return bundle_json, bundle_sh

    def args(self, root: Path, bundle_json: Path, bundle_sh: Path, *extra: str) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta183"),
            "--wsta180-bundle-json",
            str(bundle_json),
            "--wsta180-bundle-sh",
            str(bundle_sh),
            *extra,
        ]

    def valid_source_result(self, args, bundle_json: Path, bundle_sh: Path) -> dict:
        result = {
            "decision": "wsta181-blocked-explicit-execution-gate-required",
            "gate_decision": "wsta181-blocked-explicit-execution-gate-required",
            "wsta180_bundle_json": runner.rel(bundle_json),
            "wsta180_bundle_sh": runner.rel(bundle_sh),
            "checks": {
                "handoff_bundle_valid": True,
                "execution_packet_valid": True,
                "post_run_audit_command_valid": True,
            },
            "safety": {
                "live_command_executed": False,
                "wsta181_execute_command_executed": False,
                "wsta178_execute_command_executed": False,
                "wsta177_execute_command_executed": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        }
        runner.write_json(args.run_dir / runner.wsta181.SUMMARY_NAME, result)
        return result

    def valid_readiness_result(self, args, source_json: Path, bundle_json: Path, bundle_sh: Path) -> dict:
        result = {
            "decision": runner.wsta182.PASS_DECISION,
            "wsta181_source_gate_json": runner.rel(source_json),
            "wsta180_bundle_json": runner.rel(bundle_json),
            "wsta180_bundle_sh": runner.rel(bundle_sh),
            "checks": {
                "source_gate_valid": True,
                "execution_command_valid": True,
            },
            "status": {
                "state": "READY_FOR_EXPLICIT_OPERATOR_APPROVAL",
                "blocking_condition": "explicit-wsta181-operator-approval-required",
                "status_json": runner.rel(args.run_dir / runner.wsta182.STATUS_JSON_NAME),
            },
            "command": {
                "state": "READY_TO_RUN_NOT_EXECUTED",
                "executed": False,
                "command_json": runner.rel(args.run_dir / runner.wsta182.COMMAND_JSON_NAME),
                "command_script": runner.rel(args.run_dir / runner.wsta182.COMMAND_SH_NAME),
            },
            "safety": {
                "live_command_executed": False,
                "wsta181_execute_command_executed": False,
                "wsta178_execute_command_executed": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        }
        runner.write_json(args.run_dir / runner.wsta182.SUMMARY_NAME, result)
        return result

    def test_fresh_readiness_runs_source_gate_then_status_without_execution(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            calls: list[str] = []

            def fake_wsta181(args):
                calls.append("wsta181")
                self.assertFalse(args.execute_wsta181_handoff)
                return self.valid_source_result(args, bundle_json, bundle_sh)

            def fake_wsta182(args):
                calls.append("wsta182")
                self.assertTrue(str(args.wsta181_source_gate_json).endswith(runner.wsta181.SUMMARY_NAME))
                return self.valid_readiness_result(args, args.wsta181_source_gate_json, bundle_json, bundle_sh)

            old_wsta181 = runner.wsta181.run
            old_wsta182 = runner.wsta182.run
            runner.wsta181.run = fake_wsta181
            runner.wsta182.run = fake_wsta182
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.args(root, bundle_json, bundle_sh, "--emit-wsta183-fresh-readiness")
                ))
            finally:
                runner.wsta181.run = old_wsta181
                runner.wsta182.run = old_wsta182

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(calls, ["wsta181", "wsta182"])
        self.assertTrue(result["checks"]["fresh_source_gate_valid"])
        self.assertTrue(result["checks"]["readiness_valid"])
        self.assertTrue(result["safety"]["fresh_source_gate_generated"])
        self.assertTrue(result["safety"]["readiness_status_generated"])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_missing_fresh_readiness_gate_blocks_before_nested_runs(self) -> None:
        def fail(*_args, **_kwargs):
            raise AssertionError("nested runner should not run")

        old_wsta181 = runner.wsta181.run
        runner.wsta181.run = fail
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                bundle_json, bundle_sh = self.write_bundle(root)
                result = runner.run(runner.build_arg_parser().parse_args(self.args(root, bundle_json, bundle_sh)))
        finally:
            runner.wsta181.run = old_wsta181

        self.assertEqual(result["decision"], "wsta183-blocked-explicit-fresh-readiness-gate-required")

    def test_invalid_fresh_source_gate_blocks_before_readiness(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            calls: list[str] = []

            def bad_wsta181(args):
                calls.append("wsta181")
                result = self.valid_source_result(args, bundle_json, bundle_sh)
                result["decision"] = runner.wsta181.PASS_DECISION
                runner.write_json(args.run_dir / runner.wsta181.SUMMARY_NAME, result)
                return result

            def fail_wsta182(*_args, **_kwargs):
                raise AssertionError("readiness should not run")

            old_wsta181 = runner.wsta181.run
            old_wsta182 = runner.wsta182.run
            runner.wsta181.run = bad_wsta181
            runner.wsta182.run = fail_wsta182
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.args(root, bundle_json, bundle_sh, "--emit-wsta183-fresh-readiness")
                ))
            finally:
                runner.wsta181.run = old_wsta181
                runner.wsta182.run = old_wsta182

        self.assertEqual(result["decision"], "wsta183-blocked-fresh-source-gate-invalid")
        self.assertEqual(calls, ["wsta181"])

    def test_invalid_readiness_blocks_final_pass(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)

            def fake_wsta181(args):
                return self.valid_source_result(args, bundle_json, bundle_sh)

            def bad_wsta182(args):
                result = self.valid_readiness_result(args, args.wsta181_source_gate_json, bundle_json, bundle_sh)
                result["status"]["state"] = "NOT_READY"
                runner.write_json(args.run_dir / runner.wsta182.SUMMARY_NAME, result)
                return result

            old_wsta181 = runner.wsta181.run
            old_wsta182 = runner.wsta182.run
            runner.wsta181.run = fake_wsta181
            runner.wsta182.run = bad_wsta182
            try:
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.args(root, bundle_json, bundle_sh, "--emit-wsta183-fresh-readiness")
                ))
            finally:
                runner.wsta181.run = old_wsta181
                runner.wsta182.run = old_wsta182

        self.assertEqual(result["decision"], "wsta183-blocked-readiness-invalid")
        self.assertFalse(result["readiness_checks"]["status_ready"])


if __name__ == "__main__":
    unittest.main()
