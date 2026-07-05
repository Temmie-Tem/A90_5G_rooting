from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/server-distro/run_wsta221_cloudflared_egress_allowlist_policy.py"
)


class ServerDistroWsta221CloudflaredEgressAllowlistPolicyTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def operator_status(self) -> dict:
        return {
            "decision": runner.WSTA108_PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta220-test",
            "checks": {
                "attended_default_drop_live_proven": True,
                "cloudflared_runtime_live_proven": True,
                "cloudflared_model_defined": True,
                "apparmor_immediate_lever_parked": True,
            },
            "server_status": {
                "exposure": {
                    "public_state": "PUBLIC_OFF",
                    "default_public_off": True,
                },
                "hardening": {
                    "attended_default_drop_live": {
                        "state": runner.WSTA219_LIVE_STATE,
                        "attended_default_drop_live_proven": True,
                    },
                    "default_drop_hardening_policy": {
                        "state": runner.WSTA216_POLICY_STATE,
                        "default_drop_hardening_policy_defined": True,
                    },
                    "cloudflared_model": {
                        "model_defined": True,
                    },
                    "cloudflared_runtime": {
                        "cloudflared_live_proven": True,
                        "private_url_redacted": True,
                    },
                    "apparmor_feasibility": {
                        "apparmor_unavailable_under_current_evidence": True,
                        "profile_load_allowed": False,
                    },
                },
                "operator_next_actions": [
                    "keep-public-exposure-default-off",
                    "use-explicit-wsta88-live-gate-only-when-attended",
                    "continue-next-hardening-layer-after-attended-default-drop-live",
                    "move-to-next-hardening-layer-after-attended-default-drop-live",
                ],
            },
        }

    def cloudflared_model(self) -> dict:
        model = runner.wsta122.cloudflared_service_model()
        return {
            "decision": runner.wsta122.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta122-test",
            "cloudflared_service_model": model,
            "checks": runner.wsta122.validate_model(model),
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        }

    def cloudflared_runtime(self) -> dict:
        return {
            "decision": runner.wsta125.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta125-test",
            "checks": {
                "egress_route_ready": True,
                "cloudflared_uid_gid_pass": True,
                "cloudflared_no_new_privs_pass": True,
                "cloudflared_cap_eff_zero_pass": True,
                "cloudflared_command_shape_pass": True,
                "cloudflared_outbound_only_pass": True,
                "private_url_artifact_saved": True,
                "trace_file_nonempty": True,
                "syscall_profile_nonempty": True,
                "syscall_core_observed": True,
                "trace_artifact_saved": True,
                "runtime_cleanup_ok": True,
                "packet_filter_restore_pass": True,
                "final_selftest_fail_zero": True,
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
            "runtime_probe": {
                "returncode": 0,
                "parsed": {
                    "runtime_done": True,
                    "uid_3902": True,
                    "gid_3902": True,
                    "no_new_privs": True,
                    "cap_eff_zero": True,
                    "command_has_tunnel": True,
                    "command_no_autoupdate": True,
                    "command_origin": True,
                    "command_metrics": True,
                    "outbound_only": True,
                    "outbound_observed": True,
                    "established_outbound": True,
                    "cloudflared_listen_nonloopback": False,
                    "syscall_profile_nonempty": True,
                    "syscall_names": ["execve", "socket", "connect", "read", "write"],
                },
            },
            "egress_route_preflight": {
                "ready": True,
                "route_ok": True,
                "target_redacted": True,
            },
            "private_url_artifact": {
                "url_artifact_saved": True,
                "stdout_redacted": True,
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
            "safety": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }

    def run_valid_policy(self):
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status_path = root / "inputs" / "wsta108_operator_server_status.json"
            model_path = root / "inputs" / "wsta122_cloudflared_service_model.json"
            runtime_path = root / "inputs" / "wsta125_result.json"
            self.write_json(status_path, self.operator_status())
            self.write_json(model_path, self.cloudflared_model())
            self.write_json(runtime_path, self.cloudflared_runtime())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta221"),
                "--emit-egress-allowlist-policy",
                "--wsta220-operator-status-json",
                str(status_path),
                "--wsta122-cloudflared-model-json",
                str(model_path),
                "--wsta125-cloudflared-runtime-json",
                str(runtime_path),
            ]))
            policy = json.loads((root / "wsta221" / runner.POLICY_NAME).read_text(encoding="utf-8"))
            markdown = (root / "wsta221" / runner.MARKDOWN_NAME).read_text(encoding="utf-8")
        return result, policy, markdown

    def test_valid_evidence_emits_cloudflared_egress_allowlist_policy(self) -> None:
        result, policy, markdown = self.run_valid_policy()

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["checks"]["operator_status_ready"])
        self.assertTrue(result["checks"]["cloudflared_model_ready"])
        self.assertTrue(result["checks"]["cloudflared_runtime_ready"])
        self.assertEqual(policy["schema"], runner.POLICY_SCHEMA)
        self.assertEqual(policy["state"], runner.POLICY_STATE)
        self.assertEqual(policy["hardening_lever"], runner.HARDENING_LEVER)
        self.assertEqual(policy["service"], runner.SERVICE)
        self.assertEqual(policy["target_identity"]["uid"], 3902)
        self.assertFalse(policy["live_execution_requested"])
        self.assertFalse(policy["packet_filter_mutation_by_wsta221"])
        self.assertTrue(policy["policy_contract"]["fail_closed_if_owner_match_unavailable"])
        self.assertIn("derive redacted DNS/TLS egress route", " ".join(policy["next_live_gate_requirements"]))
        self.assertIn("Hardening lever: `legacy-iptables-cloudflared-egress-allowlist`", markdown)

    def test_gate_blocks_without_explicit_flag_or_private_inputs(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status_path = root / "inputs" / "wsta108_operator_server_status.json"
            model_path = root / "inputs" / "wsta122_cloudflared_service_model.json"
            runtime_path = root / "inputs" / "wsta125_result.json"
            self.write_json(status_path, self.operator_status())
            self.write_json(model_path, self.cloudflared_model())
            self.write_json(runtime_path, self.cloudflared_runtime())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta221"),
                "--wsta220-operator-status-json",
                str(status_path),
                "--wsta122-cloudflared-model-json",
                str(model_path),
                "--wsta125-cloudflared-runtime-json",
                str(runtime_path),
            ]))
        self.assertEqual(result["decision"], "wsta221-blocked-explicit-gate-required")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "wsta108_operator_server_status.json"
            model_path = root / "wsta122_cloudflared_service_model.json"
            runtime_path = root / "wsta125_result.json"
            self.write_json(status_path, self.operator_status())
            self.write_json(model_path, self.cloudflared_model())
            self.write_json(runtime_path, self.cloudflared_runtime())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta221"),
                "--emit-egress-allowlist-policy",
                "--wsta220-operator-status-json",
                str(status_path),
                "--wsta122-cloudflared-model-json",
                str(model_path),
                "--wsta125-cloudflared-runtime-json",
                str(runtime_path),
            ]))
        self.assertEqual(result["decision"], "wsta221-blocked-nonprivate-run-dir")

    def test_runtime_must_prove_outbound_observed(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status_path = root / "inputs" / "wsta108_operator_server_status.json"
            model_path = root / "inputs" / "wsta122_cloudflared_service_model.json"
            runtime_path = root / "inputs" / "wsta125_result.json"
            runtime = self.cloudflared_runtime()
            runtime["runtime_probe"]["parsed"]["outbound_observed"] = False
            self.write_json(status_path, self.operator_status())
            self.write_json(model_path, self.cloudflared_model())
            self.write_json(runtime_path, runtime)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta221"),
                "--emit-egress-allowlist-policy",
                "--wsta220-operator-status-json",
                str(status_path),
                "--wsta122-cloudflared-model-json",
                str(model_path),
                "--wsta125-cloudflared-runtime-json",
                str(runtime_path),
            ]))

        self.assertEqual(result["decision"], "wsta221-blocked-cloudflared-runtime-incomplete")
        self.assertFalse(result["checks"]["runtime_outbound_only_observed"])

    def test_policy_validation_catches_mutation_regression(self) -> None:
        _result, policy, _markdown = self.run_valid_policy()
        self.assertTrue(runner.validate_policy(policy)["no_mutation_here"])
        policy["packet_filter_mutation_by_wsta221"] = True
        self.assertFalse(runner.validate_policy(policy)["no_mutation_here"])


if __name__ == "__main__":
    unittest.main()
