from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta155_seccomp_launcher_dry_run_rootfs_proof.py")


class ServerDistroWsta155SeccompLauncherDryRunRootfsProofTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def service(self, name: str, allowlist: list[str]) -> dict:
        return {
            "service": name,
            "profile_name": f"seccomp-{name}-observed-v1",
            "source_state": f"{name}-live-proven",
            "architecture": "aarch64",
            "default_action": "ERRNO(EPERM)",
            "allowlist": allowlist,
            "allowlist_count": len(allowlist),
            "deny_by_default": True,
            "enforcement": {
                "enabled": False,
                "reason": "source-only fixture",
            },
            "redaction": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }

    def source_policy(self) -> dict:
        return {
            "schema": "a90-wsta153-seccomp-policy-source-v1",
            "state": "SECCOMP_POLICY_DRAFT_FROM_LIVE_BASELINES",
            "enforcement_state": "SOURCE_ONLY_NOT_ENFORCED",
            "default_action": "ERRNO(EPERM)",
            "architecture": "aarch64",
            "services": [
                self.service("dpublic-smoke-httpd", ["bind", "execve", "listen", "write"]),
                self.service("cloudflared-quick-tunnel", ["connect", "execve", "socket", "write"]),
                self.service("dropbear-admin-usb", ["accept", "bind", "execve", "listen", "socket"]),
                self.service("dpublic-hud-intent", ["execve", "fsync", "openat", "renameat", "write"]),
            ],
            "service_count": 4,
            "excluded_boundaries": [
                {"name": "wsta-native-uplink-helper"},
                {"name": "native-dpublic-hud-presenter"},
            ],
            "redaction": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }

    def test_valid_policy_stages_rootfs_and_observes_dry_run_markers(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            policy_path = root / "inputs" / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta155"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--emit-seccomp-launcher-dry-run-proof",
            ]))
            stdout = (root / "wsta155" / runner.STDOUT_NAME).read_text(encoding="utf-8")
            missing_stdout = (root / "wsta155" / runner.MISSING_MAP_STDOUT_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["stage"]["seccomp_launcher_policy"]["staged"])
        self.assertTrue(result["stage"]["seccomp_launcher_policy"]["hud_maps_to_intent"])
        self.assertFalse(result["proof"]["filter_load_enabled"])
        self.assertFalse(result["safety"]["seccomp_enforced"])
        self.assertIn("A90WSTA154_SECCOMP_DRY_RUN_ONLY=1", stdout)
        self.assertIn("A90WSTA154_SECCOMP_FILTER_LOAD=0", stdout)
        self.assertIn("A90WSTA154_SECCOMP_POLICY_SERVICE=dpublic-hud-intent", stdout)
        self.assertIn("fake_setpriv_args=--no-new-privs --reuid a90hud --regid a90hud", stdout)
        self.assertIn("blocked-seccomp-map-missing", missing_stdout)
        self.assertTrue(result["checks"]["proof_missing_map_blocks_before_exec"])

    def test_gate_blocks_without_explicit_flag_or_private_paths(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            policy_path = root / "inputs" / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta155"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
            ]))
        self.assertEqual(result["decision"], "wsta155-blocked-explicit-gate-required")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = root / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta155"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--emit-seccomp-launcher-dry-run-proof",
            ]))
        self.assertEqual(result["decision"], "wsta155-blocked-nonprivate-run-dir")

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            policy_path = Path(outside) / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta155"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--emit-seccomp-launcher-dry-run-proof",
            ]))
        self.assertEqual(result["decision"], "wsta155-blocked-policy-json-nonprivate")


if __name__ == "__main__":
    unittest.main()
