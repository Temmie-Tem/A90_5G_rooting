from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta214_apparmor_feasibility.py")


class ServerDistroWsta214AppArmorFeasibilityTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def d0_summary(self, *, apparmor: str = "missing") -> dict:
        return {
            "decision": "d0-public-summary-test",
            "kernel_config": {
                "CONFIG_SECURITY_APPARMOR": apparmor,
                "CONFIG_SECURITYFS": "missing",
                "CONFIG_DEFAULT_SECURITY": "missing",
                "CONFIG_SECCOMP": "y",
                "CONFIG_SECCOMP_FILTER": "y",
            },
            "filesystems": {
                "ext4": True,
                "overlay": False,
                "tmpfs": True,
            },
            "lsm": {},
            "proc_security": {},
        }

    def debian_eye_summary(self) -> dict:
        return {
            "decision": "debian-eye-test",
            "vendor_userspace_absent": {
                "cloudflared": True,
                "wpa_supplicant": True,
            },
            "redaction": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }

    def write_source(self, root: Path, text: str = "# no mac tooling staged\n") -> Path:
        path = root / "inputs" / "rootfs_source.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_valid(self, *, apparmor: str = "missing", source_text: str = "# no mac tooling staged\n"):
        with self.private_tmp() as tmp:
            root = Path(tmp)
            d0_path = root / "inputs" / "d0.json"
            debian_path = root / "inputs" / "debian_eye.json"
            source_path = self.write_source(root, source_text)
            self.write_json(d0_path, self.d0_summary(apparmor=apparmor))
            self.write_json(debian_path, self.debian_eye_summary())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta214"),
                "--d0-public-summary-json",
                str(d0_path),
                "--debian-eye-public-summary-json",
                str(debian_path),
                "--source-path",
                str(source_path),
                "--audit-apparmor-feasibility",
            ]))
            audit = json.loads((root / "wsta214" / runner.RESULT_NAME).read_text(encoding="utf-8"))
            markdown = (root / "wsta214" / runner.MARKDOWN_NAME).read_text(encoding="utf-8")
        return result, audit, markdown

    def test_current_missing_kernel_config_marks_apparmor_unavailable(self) -> None:
        result, audit, markdown = self.run_valid()

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(audit["schema"], runner.AUDIT_SCHEMA)
        self.assertEqual(audit["state"], runner.AUDIT_STATE_UNAVAILABLE)
        self.assertEqual(audit["kernel"]["CONFIG_SECURITY_APPARMOR"], "missing")
        self.assertFalse(audit["kernel"]["kernel_config_ready"])
        self.assertFalse(audit["runtime"]["apparmor_runtime_observed"])
        self.assertFalse(audit["userspace"]["apparmor_userspace_staged"])
        self.assertFalse(audit["profile_source"]["ready"])
        self.assertFalse(audit["profile_source"]["load_profiles_allowed"])
        self.assertIn("CONFIG_SECURITY_APPARMOR=y", audit["profile_source"]["blocked_missing_evidence"])
        self.assertEqual(audit["preferred_current_hardening_lever"], "legacy-iptables-loopback-default-drop")
        self.assertIn("State: `APPARMOR_NOT_AVAILABLE_UNDER_CURRENT_EVIDENCE`", markdown)
        self.assertIn("Profile load allowed: `false`", markdown)

    def test_gate_blocks_without_explicit_flag_or_private_inputs(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            d0_path = root / "inputs" / "d0.json"
            debian_path = root / "inputs" / "debian_eye.json"
            source_path = self.write_source(root)
            self.write_json(d0_path, self.d0_summary())
            self.write_json(debian_path, self.debian_eye_summary())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta214"),
                "--d0-public-summary-json",
                str(d0_path),
                "--debian-eye-public-summary-json",
                str(debian_path),
                "--source-path",
                str(source_path),
            ]))
        self.assertEqual(result["decision"], "wsta214-blocked-explicit-gate-required")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d0_path = root / "d0.json"
            debian_path = root / "debian_eye.json"
            source_path = root / "source.py"
            self.write_json(d0_path, self.d0_summary())
            self.write_json(debian_path, self.debian_eye_summary())
            source_path.write_text("# test\n", encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta214"),
                "--d0-public-summary-json",
                str(d0_path),
                "--debian-eye-public-summary-json",
                str(debian_path),
                "--source-path",
                str(source_path),
                "--audit-apparmor-feasibility",
            ]))
        self.assertEqual(result["decision"], "wsta214-blocked-nonprivate-run-dir")

    def test_ready_state_requires_kernel_and_runtime_or_userspace(self) -> None:
        result, audit, _markdown = self.run_valid(
            apparmor="y",
            source_text='PACKAGES = ["apparmor", "apparmor_parser", "aa-status"]\n',
        )

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(audit["state"], runner.AUDIT_STATE_READY)
        self.assertTrue(audit["kernel"]["kernel_config_ready"])
        self.assertTrue(audit["userspace"]["apparmor_userspace_staged"])
        self.assertTrue(audit["profile_source"]["ready"])
        self.assertFalse(audit["profile_source"]["load_profiles_allowed"])

    def test_validation_catches_invalid_ready_claim(self) -> None:
        _result, audit, _markdown = self.run_valid()
        audit["state"] = runner.AUDIT_STATE_READY
        self.assertFalse(runner.validate_audit(audit)["ready_requires_kernel_and_runtime_or_userspace"])


if __name__ == "__main__":
    unittest.main()
