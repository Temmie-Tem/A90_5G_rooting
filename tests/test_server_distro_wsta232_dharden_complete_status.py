from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta232_dharden_complete_status.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta232_dharden_complete_status.py")


class ServerDistroWsta232DhardenCompleteStatusTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def status(self) -> dict:
        return {
            "scope": "WSTA108 host-only operator server status bundle",
            "decision": runner.WSTA108_PASS_DECISION,
            "gate_decision": "ok",
            "checks": {
                "packet_filter_ready": True,
                "seccomp_real_services_live_proven": True,
                "capability_drop_nonroot_services_live_proven": True,
                "native_uplink_boundary_policy_defined": True,
                "default_drop_hardening_policy_defined": True,
                "attended_default_drop_live_proven": True,
                "cloudflared_model_defined": True,
                "cloudflared_runtime_live_proven": True,
                "cloudflared_egress_allowlist_policy_defined": True,
                "cloudflared_egress_allowlist_live_proven": True,
                "cloudflared_egress_allowlist_live_route_values_redacted": True,
                "apparmor_unavailable_under_current_evidence": True,
                "apparmor_profile_load_disabled": True,
                "apparmor_immediate_lever_parked": True,
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
            "server_status": {
                "state": "SERVER_PROFILE_READY_DEFAULT_OFF",
                "operator_next_actions": [
                    "keep-public-exposure-default-off",
                    "use-explicit-wsta88-live-gate-only-when-attended",
                    runner.SOURCE_NEXT_ACTION,
                ],
                "exposure": {
                    "public_state": "PUBLIC_OFF",
                    "default_public_off": True,
                },
                "packet_filter": {
                    "ready": True,
                    "state": "PACKET_FILTER_REQUIRED_DEFAULT_OFF",
                },
                "redaction": {
                    "public_url_value_logged": False,
                    "secret_values_logged": 0,
                },
                "hardening": {
                    "blocking_before_enforcement": [],
                    "launcher_proof": {
                        "remaining_profiles": [],
                    },
                    "syscall_trace_proof": {
                        "remaining_profiles": [],
                    },
                    "seccomp_enforcement_proof": {
                        "seccomp_real_services_live_proven": True,
                        "seccomp_filter_loaded": True,
                        "seccomp_enforced": True,
                    },
                    "capability_drop_proof": {
                        "nonroot_services_capability_drop_live_proven": True,
                        "remaining_nonroot_services": [],
                    },
                    "native_uplink_boundary_policy": {
                        "native_uplink_boundary_policy_defined": True,
                        "connectivity_stays_native_owned": True,
                        "not_debian_launcher_or_seccomp_target": True,
                    },
                    "default_drop_hardening_policy": {
                        "default_drop_hardening_policy_defined": True,
                    },
                    "attended_default_drop_live": {
                        "attended_default_drop_live_proven": True,
                    },
                    "cloudflared_egress_allowlist_policy": {
                        "cloudflared_egress_allowlist_policy_defined": True,
                    },
                    "cloudflared_egress_allowlist_live": {
                        "state": "CLOUDFLARED_EGRESS_ALLOWLIST_ATTENDED_LIVE_PROVEN",
                        "cloudflared_egress_allowlist_live_proven": True,
                        "manual_stop_cleanup_ok": True,
                        "public_state_after_manual_stop": "PUBLIC_OFF",
                    },
                    "apparmor_feasibility": {
                        "apparmor_unavailable_under_current_evidence": True,
                        "profile_load_allowed": False,
                        "preferred_current_hardening_lever": "legacy-iptables-loopback-default-drop",
                    },
                },
            },
            "safety": {
                "device_action": False,
                "public_tunnel": False,
                "packet_filter_mutation": False,
            },
        }

    def valid_args(self, root: Path):
        status_path = root / "inputs" / "wsta108_operator_server_status.json"
        self.write_json(status_path, self.status())
        return runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta232"),
            "--emit-dharden-complete-status",
            "--wsta108-server-status-json",
            str(status_path),
        ])

    def test_default_run_is_fail_closed_and_host_only(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta232"),
            ]))

        self.assertEqual(result["decision"], "wsta232-blocked-explicit-emit-dharden-complete-status-required")
        for key in ("device_action", "boot_flash", "native_reboot", "wifi_connect", "packet_filter_mutation"):
            self.assertFalse(result["safety"][key])
        self.assertFalse(result["safety"]["public_tunnel"])
        self.assertFalse(result["safety"]["public_smoke"])

    def test_valid_wsta108_status_emits_dharden_complete_status(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(self.valid_args(root))
            saved = json.loads((root / "wsta232" / runner.RESULT_NAME).read_text(encoding="utf-8"))
            status = json.loads((root / "wsta232" / runner.STATUS_JSON_NAME).read_text(encoding="utf-8"))
            markdown = (root / "wsta232" / runner.STATUS_MD_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        self.assertEqual(status["state"], runner.COMPLETE_STATE)
        self.assertTrue(status["complete"])
        self.assertEqual(status["public_state"], "PUBLIC_OFF")
        self.assertTrue(status["public_exposure_default_off"])
        self.assertEqual(status["remaining_blockers"]["blocking_before_enforcement"], [])
        self.assertEqual(status["remaining_blockers"]["launcher_remaining_profiles"], [])
        self.assertEqual(status["remaining_blockers"]["syscall_remaining_profiles"], [])
        self.assertEqual(status["operator_next_actions"], runner.CLOSEOUT_NEXT_ACTIONS)
        self.assertEqual(status["retired_source_next_actions"], [runner.SOURCE_NEXT_ACTION])
        self.assertEqual(status["recommended_next_unit"], "attended-cold-boot-persistence-smoke-measurement")
        self.assertTrue(all(result["checks"][key] for key in runner.REQUIRED_TRUE_CHECKS))
        self.assertIn("WSTA232 D-HARDEN Complete Status", markdown)
        self.assertIn(runner.PASS_DECISION, markdown)

    def test_non_pass_wsta108_status_blocks_complete_status(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.status()
            status["decision"] = "wsta108-blocked"
            status_path = root / "inputs" / "wsta108_operator_server_status.json"
            self.write_json(status_path, status)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta232"),
                "--emit-dharden-complete-status",
                "--wsta108-server-status-json",
                str(status_path),
            ]))

        self.assertEqual(result["decision"], "wsta232-blocked-dharden-complete-incomplete")
        self.assertFalse(result["checks"]["wsta108_pass"])
        self.assertIn("wsta108_pass", result["gate_detail"]["failed_required_checks"])
        self.assertFalse((root / "wsta232" / runner.STATUS_JSON_NAME).exists())

    def test_missing_landed_lever_blocks_complete_status(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.status()
            status["checks"]["cloudflared_egress_allowlist_live_proven"] = False
            status_path = root / "inputs" / "wsta108_operator_server_status.json"
            self.write_json(status_path, status)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta232"),
                "--emit-dharden-complete-status",
                "--wsta108-server-status-json",
                str(status_path),
            ]))

        self.assertEqual(result["decision"], "wsta232-blocked-dharden-complete-incomplete")
        self.assertFalse(result["checks"]["cloudflared_egress_allowlist_live_proven"])
        self.assertIn("cloudflared_egress_allowlist_live_proven", result["gate_detail"]["failed_required_checks"])

    def test_nonprivate_run_or_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "wsta108_operator_server_status.json"
            self.write_json(status_path, self.status())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta232"),
                "--emit-dharden-complete-status",
                "--wsta108-server-status-json",
                str(status_path),
            ]))

        self.assertEqual(result["decision"], "wsta232-blocked-nonprivate-run-dir")

        with self.private_tmp() as private_tmp, tempfile.TemporaryDirectory() as public_tmp:
            private_root = Path(private_tmp)
            public_root = Path(public_tmp)
            status_path = public_root / "wsta108_operator_server_status.json"
            self.write_json(status_path, self.status())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(private_root / "wsta232"),
                "--emit-dharden-complete-status",
                "--wsta108-server-status-json",
                str(status_path),
            ]))

        self.assertEqual(result["decision"], "wsta232-blocked-wsta108-server-status-nonprivate")

    def test_source_keeps_live_public_and_secret_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("--emit-dharden-complete-status", source)
        self.assertIn("D_HARDEN_COMPLETE_DEFAULT_OFF", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"packet_filter_mutation": False', source)
        self.assertIn('"public_url_value_logged": False', source)
        self.assertIn('"secret_values_logged": 0', source)
        self.assertNotIn("native_" + "init_flash.py", source)
        self.assertNotIn("try" + "cloudflare.com", source)
        self.assertNotIn("ssid" + "=", source.lower())
        self.assertNotIn("psk" + "=", source.lower())
        self.assertNotIn("http" + "://", source.lower())
        self.assertNotIn("https" + "://", source.lower())


if __name__ == "__main__":
    unittest.main()
