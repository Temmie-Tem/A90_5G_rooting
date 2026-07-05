from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta187_fresh_wsta185_orchestrator.py")


class ServerDistroWsta187FreshWsta185OrchestratorTests(unittest.TestCase):
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
                str(root / "stale-wsta167-run"),
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
            str(root / "wsta187"),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
        ]

    def prepare_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.base_args(root, command_json, command_sh) + [
            "--prepare-wsta187-fresh-orchestrator",
        ]

    def execute_args(self, root: Path, command_json: Path, command_sh: Path) -> list[str]:
        return self.prepare_args(root, command_json, command_sh) + [
            "--execute-wsta187-fresh-orchestrator",
            "--allow-wsta185-handoff-execution",
            "--ack-fresh-sequence",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]

    def install_success_fakes(self, *, execute_expected: bool, calls: list[str]) -> dict:
        def fake_wsta177(args):
            calls.append("wsta177")
            result = {
                "scope": "WSTA177 one-shot no-load seccomp execution gate",
                "decision": "wsta177-blocked-explicit-execution-gate-required",
                "checks": {"fresh_preflight_valid": True, "execution_command_valid": True},
                "safety": {
                    "live_command_executed": False,
                    "wsta175_execute_command_executed": False,
                    "wsta170_execute_command_executed": False,
                    "seccomp_filter_loaded": False,
                    "seccomp_enforced": False,
                    "correct_wsta161_token_supplied": False,
                },
            }
            self.write_json(args.run_dir / runner.wsta177.SUMMARY_NAME, result)
            return result

        def fake_wsta178(args):
            calls.append("wsta178")
            command_json = args.run_dir / runner.wsta178.COMMAND_JSON_NAME
            command_sh = args.run_dir / runner.wsta178.COMMAND_SH_NAME
            rebased_json = args.run_dir / runner.wsta178.REBASED_WSTA168_COMMAND_JSON_NAME
            rebased_sh = args.run_dir / runner.wsta178.REBASED_WSTA168_COMMAND_SH_NAME
            self.write_json(command_json, {"schema": "a90-wsta178-wsta177-execute-command-v1"})
            command_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            self.write_json(rebased_json, {"schema": "a90-wsta168-seccomp-live-observation-command-v1"})
            rebased_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            result = {
                "scope": "WSTA178 host-only WSTA177 one-shot execution preflight",
                "decision": runner.wsta178.PASS_DECISION,
                "checks": {
                    "source_gate_valid": True,
                    "rebased_wsta168_command_valid": True,
                    "execution_command_valid": True,
                },
                "command": {
                    "command_json": runner.rel(command_json),
                    "command_script": runner.rel(command_sh),
                },
                "rebased_wsta168_command": {
                    "wsta167_run_dir": runner.rel(args.run_dir / "rebased-wsta168-command" / "wsta167-live-run"),
                },
                "safety": {"live_command_executed": False, "seccomp_filter_loaded": False},
            }
            self.write_json(args.run_dir / runner.wsta178.SUMMARY_NAME, result)
            return result

        def fake_wsta180(args):
            calls.append("wsta180")
            bundle_json = args.run_dir / runner.wsta180.BUNDLE_JSON_NAME
            bundle_sh = args.run_dir / runner.wsta180.BUNDLE_SH_NAME
            self.write_json(bundle_json, {"schema": "a90-wsta180-seccomp-live-handoff-bundle-v1"})
            bundle_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            result = {
                "scope": "WSTA180 operator handoff bundle for no-load live observation",
                "decision": runner.wsta180.PASS_DECISION,
                "checks": {
                    "pre_run_audit_missing_result": True,
                    "execution_packet_valid": True,
                    "post_run_audit_command_valid": True,
                    "bundle_valid": True,
                },
                "bundle": {
                    "bundle_json": runner.rel(bundle_json),
                    "operator_commands_script": runner.rel(bundle_sh),
                },
                "safety": {"live_command_executed": False, "seccomp_filter_loaded": False},
            }
            self.write_json(args.run_dir / runner.wsta180.SUMMARY_NAME, result)
            return result

        def fake_wsta184(args):
            calls.append("wsta184")
            handoff_json = args.run_dir / runner.wsta184.HANDOFF_NAME
            self.write_json(handoff_json, {"schema": "a90-wsta184-expiring-wsta181-execute-handoff-v1"})
            result = {
                "scope": "WSTA184 expiring WSTA181 execution handoff",
                "decision": runner.wsta184.PASS_DECISION,
                "checks": {
                    "fresh_readiness_valid": True,
                    "freshness_valid": True,
                    "readiness_valid": True,
                    "command_valid": True,
                },
                "handoff": {
                    "handoff_json": runner.rel(handoff_json),
                    "executed": False,
                    "expires_utc": "20990101T000000Z",
                },
                "safety": {"live_command_executed": False, "seccomp_filter_loaded": False},
            }
            self.write_json(args.run_dir / runner.wsta184.SUMMARY_NAME, result)
            return result

        def fake_wsta185(args):
            calls.append("wsta185")
            self.assertEqual(args.execute_wsta185_handoff, execute_expected)
            if execute_expected:
                result = {
                    "scope": "WSTA185 expiring WSTA184 handoff execute gate",
                    "decision": runner.wsta185.PASS_DECISION,
                    "checks": {
                        "handoff_valid": True,
                        "command_artifacts_valid": True,
                        "freshness_valid": True,
                        "execution_returncode_ok": True,
                        "wsta181_result_valid": True,
                    },
                    "handoff": {"wsta181_result_json": runner.rel(args.run_dir / runner.wsta185.wsta181.SUMMARY_NAME)},
                    "wsta181_result": {
                        "decision": runner.wsta185.wsta181.PASS_DECISION,
                        "post_run_audit_decision": runner.wsta185.wsta181.wsta179.PASS_DECISION,
                        "deep_audit": {
                            "wsta167_decision_pass": True,
                            "wsta170_decision_pass": True,
                            "wsta175_decision_pass": True,
                        },
                    },
                    "safety": {
                        "device_action": "wsta185-wsta181-expiring-handoff-no-load-live-observation",
                        "wsta181_execute_command_executed": True,
                        "wsta178_execute_command_executed": True,
                        "wsta177_execute_command_executed": True,
                        "wsta175_execute_command_executed": True,
                        "wsta170_execute_command_executed": True,
                        "post_run_audit_executed": True,
                        "live_command_executed": True,
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
                }
            else:
                result = {
                    "scope": "WSTA185 expiring WSTA184 handoff execute gate",
                    "decision": "wsta185-blocked-explicit-execution-gate-required",
                    "checks": {
                        "handoff_valid": True,
                        "command_artifacts_valid": True,
                        "freshness_valid": True,
                    },
                    "handoff": {"wsta181_result_json": runner.rel(args.run_dir / runner.wsta185.wsta181.SUMMARY_NAME)},
                    "safety": {
                        "live_command_executed": False,
                        "wsta181_execute_command_executed": False,
                        "seccomp_filter_loaded": False,
                        "seccomp_enforced": False,
                        "correct_wsta161_token_supplied": False,
                    },
                }
            self.write_json(args.run_dir / runner.wsta185.SUMMARY_NAME, result)
            return result

        old = {
            "wsta177": runner.wsta177.run,
            "wsta178": runner.wsta178.run,
            "wsta180": runner.wsta180.run,
            "wsta184": runner.wsta184.run,
            "wsta185": runner.wsta185.run,
        }
        runner.wsta177.run = fake_wsta177
        runner.wsta178.run = fake_wsta178
        runner.wsta180.run = fake_wsta180
        runner.wsta184.run = fake_wsta184
        runner.wsta185.run = fake_wsta185
        return old

    def restore_fakes(self, old: dict) -> None:
        runner.wsta177.run = old["wsta177"]
        runner.wsta178.run = old["wsta178"]
        runner.wsta180.run = old["wsta180"]
        runner.wsta184.run = old["wsta184"]
        runner.wsta185.run = old["wsta185"]

    def test_missing_prepare_gate_blocks_before_any_stage(self) -> None:
        calls: list[str] = []
        old = self.install_success_fakes(execute_expected=False, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.base_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_fakes(old)

        self.assertEqual(result["decision"], "wsta187-blocked-explicit-prepare-gate-required")
        self.assertEqual(calls, [])

    def test_prepare_builds_fresh_sequence_and_stops_at_wsta185_source_gate(self) -> None:
        calls: list[str] = []
        old = self.install_success_fakes(execute_expected=False, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_fakes(old)

        self.assertEqual(result["decision"], "wsta187-blocked-explicit-execution-gate-required")
        self.assertEqual(calls, ["wsta177", "wsta178", "wsta180", "wsta184", "wsta185"])
        self.assertTrue(result["checks"]["wsta177_source_valid"])
        self.assertTrue(result["checks"]["wsta178_preflight_valid"])
        self.assertTrue(result["checks"]["wsta180_bundle_valid"])
        self.assertTrue(result["checks"]["wsta184_handoff_valid"])
        self.assertTrue(result["checks"]["wsta185_source_valid"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertIn("rebased_wsta167_run_dir", result["stages"]["wsta178_preflight"])
        self.assertTrue(result["stages"]["wsta177_source_gate"]["result_json"].endswith("/wsta177_result.json"))
        self.assertTrue(result["stages"]["wsta178_preflight"]["result_json"].endswith("/wsta178_result.json"))
        self.assertTrue(result["stages"]["wsta180_bundle"]["result_json"].endswith("/wsta180_result.json"))
        self.assertTrue(result["stages"]["wsta184_handoff"]["result_json"].endswith("/wsta184_result.json"))
        self.assertTrue(result["stages"]["wsta185"]["result_json"].endswith("/wsta185_result.json"))

    def test_full_ack_executes_wsta185_and_requires_deep_evidence(self) -> None:
        calls: list[str] = []
        old = self.install_success_fakes(execute_expected=True, calls=calls)
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_fakes(old)

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["checks"]["wsta185_execution_valid"])
        self.assertTrue(result["safety"]["wsta181_execute_command_executed"])
        self.assertTrue(result["safety"]["wsta175_execute_command_executed"])
        self.assertTrue(result["safety"]["wsta170_execute_command_executed"])
        self.assertTrue(result["wsta185_execution_checks"]["deep_wsta167_pass"])
        self.assertTrue(result["wsta185_source_checks"]["handoff_valid"])

    def test_execution_failure_is_classified_as_execution_invalid(self) -> None:
        calls: list[str] = []
        old = self.install_success_fakes(execute_expected=True, calls=calls)

        def failing_wsta185(args):
            calls.append("wsta185")
            self.assertTrue(args.execute_wsta185_handoff)
            result = {
                "scope": "WSTA185 expiring WSTA184 handoff execute gate",
                "decision": "wsta185-blocked-wsta181-returncode",
                "checks": {
                    "handoff_valid": True,
                    "command_artifacts_valid": True,
                    "freshness_valid": True,
                    "execution_returncode_ok": False,
                    "wsta181_result_valid": False,
                },
                "handoff": {"wsta181_result_json": runner.rel(args.run_dir / runner.wsta185.wsta181.SUMMARY_NAME)},
                "wsta181_result": {},
                "safety": {
                    "wsta181_execute_command_executed": True,
                    "wsta178_execute_command_executed": True,
                    "wsta177_execute_command_executed": True,
                    "wsta175_execute_command_executed": False,
                    "wsta170_execute_command_executed": False,
                    "post_run_audit_executed": False,
                    "live_command_executed": True,
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
            }
            self.write_json(args.run_dir / runner.wsta185.SUMMARY_NAME, result)
            return result

        runner.wsta185.run = failing_wsta185
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.execute_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_fakes(old)

        self.assertEqual(result["decision"], "wsta187-blocked-wsta185-execution-invalid")
        self.assertTrue(result["checks"]["wsta185_source_valid"])
        self.assertFalse(result["checks"]["wsta185_execution_valid"])

    def test_invalid_wsta178_stage_blocks_before_bundle(self) -> None:
        calls: list[str] = []
        old = self.install_success_fakes(execute_expected=False, calls=calls)

        def bad_wsta178(args):
            calls.append("wsta178")
            result = {
                "scope": "WSTA178 host-only WSTA177 one-shot execution preflight",
                "decision": "bad",
                "checks": {"source_gate_valid": False},
                "command": {},
                "rebased_wsta168_command": {},
                "safety": {"live_command_executed": False, "seccomp_filter_loaded": False},
            }
            self.write_json(args.run_dir / runner.wsta178.SUMMARY_NAME, result)
            return result

        runner.wsta178.run = bad_wsta178
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args(
                    self.prepare_args(root, command_json, command_sh)
                ))
        finally:
            self.restore_fakes(old)

        self.assertEqual(result["decision"], "wsta187-blocked-wsta178-preflight-invalid")
        self.assertEqual(calls, ["wsta177", "wsta178"])


if __name__ == "__main__":
    unittest.main()
