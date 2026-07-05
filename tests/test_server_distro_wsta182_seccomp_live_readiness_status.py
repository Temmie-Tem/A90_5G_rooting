from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta182_seccomp_live_readiness_status.py")


class ServerDistroWsta182SeccompLiveReadinessStatusTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_bundle(self, root: Path) -> tuple[Path, Path]:
        bundle_json = root / "wsta180_operator_handoff.json"
        bundle_sh = root / "wsta180_operator_handoff_commands.sh"
        self.write_json(bundle_json, {"schema": "a90-wsta180-seccomp-live-handoff-bundle-v1"})
        bundle_sh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        return bundle_json, bundle_sh

    def write_wsta181_source_gate(
        self,
        root: Path,
        bundle_json: Path,
        bundle_sh: Path,
        *,
        decision: str = "wsta181-blocked-explicit-execution-gate-required",
        expected_result_missing: bool = True,
    ) -> Path:
        result = {
            "decision": decision,
            "gate_decision": decision,
            "wsta180_bundle_json": runner.rel(bundle_json),
            "wsta180_bundle_sh": runner.rel(bundle_sh),
            "bundle": {
                "state": "READY_FOR_OPERATOR_APPROVAL_NOT_EXECUTED",
                "execute_packet_json": "workspace/private/runs/server-distro/wsta178.json",
                "execute_packet_script": "workspace/private/runs/server-distro/wsta178.sh",
                "expected_wsta177_result_json": "workspace/private/runs/server-distro/wsta177_result.json",
            },
            "checks": {
                "explicit_execution_gate": False,
                "handoff_bundle_valid": True,
                "execution_packet_valid": True,
                "post_run_audit_command_valid": True,
            },
            "handoff_bundle_checks": {
                "bundle_private": True,
                "bundle_script_private": True,
                "schema_ok": True,
                "state_ready": True,
                "bundle_not_executed": True,
                "execute_packet_not_executed": True,
                "command_json_private": True,
                "command_sh_private": True,
                "command_json_present": True,
                "command_sh_present": True,
                "expected_result_private": True,
                "expected_result_missing": expected_result_missing,
                "post_run_audit_expected_pass": True,
                "post_run_audit_command_is_string_list": True,
                "post_run_audit_run_dir_private": True,
            },
            "execution_packet_checks": {
                "schema_ok": True,
                "ready_not_executed": True,
                "not_executed": True,
                "command_is_string_list": True,
                "command_targets_wsta177": True,
                "all_ack_flags_present": True,
                "correct_token_literal_absent": True,
                "no_external_network_inputs": True,
                "expected_wsta177_pass": True,
                "expected_wsta175_pass": True,
                "expected_wsta170_pass": True,
                "expected_wsta167_pass": True,
                "expected_no_seccomp_load": True,
                "expected_no_seccomp_enforce": True,
                "expected_no_correct_token": True,
                "secret_values_logged_zero": True,
                "command_json_private": True,
                "command_sh_private": True,
                "inferred_result_path_private": True,
                "command_run_dir_private": True,
            },
            "post_run_audit_command_checks": {
                "command_is_string_list": True,
                "command_targets_wsta179": True,
                "audit_gate_present": True,
                "no_execute_wsta177_gate": True,
                "no_wsta175_execute_gate": True,
                "no_wsta170_execute_gate": True,
                "correct_token_literal_absent": True,
                "no_external_network_inputs": True,
            },
            "safety": {
                "device_action_requested": False,
                "live_command_executed": False,
                "wsta178_execute_command_executed": False,
                "wsta177_execute_command_executed": False,
                "wsta175_execute_command_executed": False,
                "wsta170_execute_command_executed": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        }
        source_gate = root / "wsta181_result.json"
        self.write_json(source_gate, result)
        return source_gate

    def base_args(self, root: Path, source_gate: Path, bundle_json: Path, bundle_sh: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta182"),
            "--wsta181-source-gate-json",
            str(source_gate),
            "--wsta180-bundle-json",
            str(bundle_json),
            "--wsta180-bundle-sh",
            str(bundle_sh),
        ]

    def status_args(self, root: Path, source_gate: Path, bundle_json: Path, bundle_sh: Path) -> list[str]:
        return self.base_args(root, source_gate, bundle_json, bundle_sh) + [
            "--emit-wsta182-readiness-status"
        ]

    def test_readiness_status_emits_wsta181_execution_command_without_executing(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            source_gate = self.write_wsta181_source_gate(root, bundle_json, bundle_sh)
            result = runner.run(runner.build_arg_parser().parse_args(
                self.status_args(root, source_gate, bundle_json, bundle_sh)
            ))
            status = json.loads((root / "wsta182" / runner.STATUS_JSON_NAME).read_text(encoding="utf-8"))
            command = json.loads((root / "wsta182" / runner.COMMAND_JSON_NAME).read_text(encoding="utf-8"))
            script = (root / "wsta182" / runner.COMMAND_SH_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(status["state"], "READY_FOR_EXPLICIT_OPERATOR_APPROVAL")
        self.assertEqual(status["blocking_condition"], "explicit-wsta181-operator-approval-required")
        self.assertTrue(result["checks"]["source_gate_valid"])
        self.assertTrue(result["checks"]["execution_command_valid"])
        self.assertTrue(result["safety"]["readiness_status_generated"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertEqual(command["schema"], "a90-wsta182-wsta181-execute-command-v1")
        self.assertFalse(command["executed"])
        self.assertIn("workspace/public/src/scripts/server-distro/run_wsta181_seccomp_handoff_execute_audit_gate.py", command["command"])
        self.assertIn("--execute-wsta181-handoff", command["command"])
        self.assertIn("--allow-wsta178-command-execution", command["command"])
        self.assertIn("--ack-post-run-audit-required", command["command"])
        self.assertIn("--execute-wsta181-handoff", script)
        self.assertNotIn("WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD", script)

    def test_missing_status_gate_blocks_before_source_gate(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            source_gate = self.write_wsta181_source_gate(root, bundle_json, bundle_sh)
            result = runner.run(runner.build_arg_parser().parse_args(
                self.base_args(root, source_gate, bundle_json, bundle_sh)
            ))

        self.assertEqual(result["decision"], "wsta182-blocked-explicit-status-gate-required")
        self.assertFalse((root / "wsta182" / runner.STATUS_JSON_NAME).exists())

    def test_stale_existing_result_blocks_readiness(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            source_gate = self.write_wsta181_source_gate(
                root,
                bundle_json,
                bundle_sh,
                expected_result_missing=False,
            )
            result = runner.run(runner.build_arg_parser().parse_args(
                self.status_args(root, source_gate, bundle_json, bundle_sh)
            ))

        self.assertEqual(result["decision"], "wsta182-blocked-source-gate-invalid")
        self.assertFalse(result["source_gate_checks"]["expected_result_missing"])
        self.assertFalse((root / "wsta182" / runner.COMMAND_JSON_NAME).exists())

    def test_pass_decision_source_gate_is_rejected(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            bundle_json, bundle_sh = self.write_bundle(root)
            source_gate = self.write_wsta181_source_gate(
                root,
                bundle_json,
                bundle_sh,
                decision=runner.wsta181.PASS_DECISION,
            )
            result = runner.run(runner.build_arg_parser().parse_args(
                self.status_args(root, source_gate, bundle_json, bundle_sh)
            ))

        self.assertEqual(result["decision"], "wsta182-blocked-source-gate-invalid")
        self.assertFalse(result["source_gate_checks"]["decision_is_explicit_gate_block"])


if __name__ == "__main__":
    unittest.main()
