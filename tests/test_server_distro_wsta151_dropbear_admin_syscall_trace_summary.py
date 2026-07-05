from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta151_dropbear_admin_syscall_trace_summary.py")
wsta151 = runner.wsta151


class ServerDistroWsta151DropbearAdminSyscallTraceSummaryTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def source_result(self) -> dict:
        syscalls = [
            "accept",
            "bind",
            "brk",
            "close",
            "execve",
            "listen",
            "socket",
            "write",
        ]
        return {
            "decision": wsta151.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta151-live-test",
            "local_image_sha256": wsta151.WSTA115_STRACE_IMAGE_SHA256,
            "safety": {
                "boot_flash": False,
                "native_reboot": False,
                "wifi_connect": False,
                "dhcp": False,
                "public_tunnel": False,
                "public_smoke": False,
                "packet_filter_mutation": False,
                "userdata_touch": False,
                "switch_root": False,
            },
            "checks": {
                "admin_trace_stage_pass": True,
                "admin_ssh_pass": True,
                "root_ssh_rejected": True,
                "syscall_core_observed": True,
                "syscall_accept_observed": True,
                "trace_artifact_saved": True,
                "dropbear_log_policy_clean": True,
                "trace_cleanup_ok": True,
                "chroot_cleanup_ok": True,
                "final_selftest_fail_zero": True,
            },
            "syscall_profile": {
                "schema": "a90-wsta151-dropbear-admin-syscall-profile-v1",
                "service": "dropbear-admin-usb",
                "scope": "dropbear-admin-usb-daemon",
                "daemon": "/usr/sbin/dropbear",
                "daemon_privilege_model": "root-boundary-auth-daemon",
                "bind": "192.168.7.2:2222",
                "network_scope": "usb-ncm-admin-only",
                "password_login_disabled": True,
                "root_login_disabled": True,
                "forwarding_disabled": True,
                "admin_login_uid_gid_proven": True,
                "root_ssh_rejected": True,
                "root_authorized_keys_absent": True,
                "core_syscalls": list(wsta151.CORE_SYSCALLS),
                "accept_syscalls": list(wsta151.ACCEPT_SYSCALLS),
                "core_syscalls_observed": True,
                "accept_observed": True,
                "syscall_count": len(syscalls),
                "syscall_names": syscalls,
                "trace_artifacts": {
                    "all_saved": True,
                    "raw_trace": {"sha256": "raw-sha"},
                    "syscall_list": {"sha256": "syscalls-sha"},
                    "dropbear_log": {"sha256": "log-sha"},
                },
                "public_url_value_logged": False,
                "admin_public_key_value_logged": False,
                "secret_values_logged": 0,
            },
            "final_version": {
                "text": "A90 Linux init 0.11.158 (v3402-dpublic-hud-presenter-restart-policy)",
            },
            "final_selftest": {
                "text": "selftest: pass=12 warn=1 fail=0",
            },
            "public_url_value_logged": False,
            "admin_public_key_value_logged": False,
            "secret_values_logged": 0,
        }

    def test_summarize_source_passes_for_valid_wsta151_result(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            source_path = root / "source" / "wsta151_result.json"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(json.dumps(self.source_result()) + "\n", encoding="utf-8")

            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "summary"),
                "--source-json",
                str(source_path),
                "--summarize-wsta151-dropbear-admin-trace",
            ]))
            proof = json.loads((root / "summary" / runner.RESULT_NAME).read_text(encoding="utf-8"))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(proof["decision"], runner.PASS_DECISION)
        self.assertEqual(proof["schema"], "a90-wsta151-dropbear-admin-syscall-trace-live-v1")
        self.assertEqual(proof["service"], "dropbear-admin-usb")
        self.assertEqual(proof["scope"], "dropbear-admin-usb-daemon")
        self.assertEqual(proof["uid"], 3903)
        self.assertEqual(proof["gid"], 3903)
        self.assertEqual(proof["bind"], "192.168.7.2:2222")
        self.assertTrue(proof["admin_login_uid_gid_proven"])
        self.assertTrue(proof["root_ssh_rejected"])
        self.assertTrue(proof["password_login_disabled"])
        self.assertTrue(proof["root_login_disabled"])
        self.assertTrue(proof["forwarding_disabled"])
        self.assertTrue(proof["core_syscalls_observed"])
        self.assertTrue(proof["accept_observed"])
        self.assertTrue(proof["trace_artifacts_saved"])
        self.assertEqual(proof["raw_trace_sha256"], "raw-sha")
        self.assertEqual(proof["dropbear_log_sha256"], "log-sha")
        self.assertFalse(proof["public_url_value_logged"])
        self.assertFalse(proof["admin_public_key_value_logged"])
        self.assertEqual(proof["secret_values_logged"], 0)

    def test_validation_fails_closed_on_missing_accept_or_bad_policy(self) -> None:
        source = self.source_result()
        source["syscall_profile"]["syscall_names"].remove("accept")
        self.assertFalse(runner.validate_source_result(source)["accept_syscall_proven"])

        source = self.source_result()
        source["checks"]["dropbear_log_policy_clean"] = False
        self.assertFalse(runner.validate_source_result(source)["log_policy_clean"])

        source = self.source_result()
        source["syscall_profile"]["root_login_disabled"] = False
        self.assertFalse(runner.validate_source_result(source)["daemon_policy_proven"])

    def test_default_and_nonprivate_runs_block(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            source_path = root / "source.json"
            source_path.write_text(json.dumps(self.source_result()) + "\n", encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "summary"),
                "--source-json",
                str(source_path),
            ]))
        self.assertEqual(result["decision"], "wsta151-summary-blocked-explicit-gate-required")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "source.json"
            source_path.write_text(json.dumps(self.source_result()) + "\n", encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "summary"),
                "--source-json",
                str(source_path),
                "--summarize-wsta151-dropbear-admin-trace",
            ]))
        self.assertEqual(result["decision"], "wsta151-summary-blocked-nonprivate-run-dir")


if __name__ == "__main__":
    unittest.main()
