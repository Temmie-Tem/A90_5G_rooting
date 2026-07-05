from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta159_seccomp_loader_checkonly_rootfs_proof.py")


class ServerDistroWsta159SeccompLoaderCheckonlyRootfsProofTests(unittest.TestCase):
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

    def write_filter_artifact(self, root: Path) -> tuple[Path, Path]:
        object_path = root / "inputs" / "wsta156_seccomp_filters.o"
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(b"fake-wsta159-object")
        object_sha = hashlib.sha256(object_path.read_bytes()).hexdigest()
        manifest = {
            "schema": "a90-wsta156-seccomp-nonloaded-filter-artifact-v1",
            "state": "SECCOMP_FILTER_ARTIFACT_COMPILED_NOT_LOADED",
            "source_policy_schema": "a90-wsta153-seccomp-policy-source-v1",
            "source_policy_enforcement_state": "SOURCE_ONLY_NOT_ENFORCED",
            "service_count": 4,
            "loaded": False,
            "enforced": False,
            "artifact_sha256": {"object": object_sha},
            "services": [
                {"service": "dpublic-smoke-httpd", "instruction_count": 9, "missing_syscalls": []},
                {"service": "cloudflared-quick-tunnel", "instruction_count": 11, "missing_syscalls": []},
                {"service": "dropbear-admin-usb", "instruction_count": 13, "missing_syscalls": []},
                {"service": "dpublic-hud-intent", "instruction_count": 15, "missing_syscalls": []},
            ],
            "redaction": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }
        manifest_path = root / "inputs" / "wsta156_seccomp_filter_manifest.json"
        self.write_json(manifest_path, manifest)
        return manifest_path, object_path

    def compile_fake_loader_helper(self, root: Path) -> Path:
        source = root / "inputs" / "fake_loader.c"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "  puts(\"A90WSTA158_LOADER_CHECK_ONLY=1\");\n"
            "  puts(\"A90WSTA158_SECCOMP_LOAD=0\");\n"
            "  puts(\"A90WSTA158_PROFILE service=dpublic-hud policy_service=dpublic-hud-intent profile=seccomp-dpublic-hud-intent-observed-v1 len=49\");\n"
            "  puts(\"a90_seccomp_loader_decision=check-only\");\n"
            "  return 0;\n"
            "}\n",
            encoding="utf-8",
        )
        helper = root / "inputs" / "a90-seccomp-loader-checkonly"
        completed = subprocess.run(
            ["aarch64-linux-gnu-gcc", "-static", "-Os", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(helper)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60.0,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return helper

    def write_loader_helper(self, root: Path) -> tuple[Path, Path]:
        helper = self.compile_fake_loader_helper(root)
        helper_sha = hashlib.sha256(helper.read_bytes()).hexdigest()
        manifest = {
            "schema": "a90-wsta158-seccomp-loader-checkonly-helper-v1",
            "state": "SECCOMP_LOADER_HELPER_CHECK_ONLY_LINKED",
            "helper_sha256": helper_sha,
            "helper_file": "ELF 64-bit LSB executable, ARM aarch64, statically linked",
            "default_mode": "check-only",
            "load_enabled": False,
            "enforced": False,
            "redaction": {
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }
        manifest_path = root / "inputs" / "wsta158_seccomp_loader_helper_manifest.json"
        self.write_json(manifest_path, manifest)
        return manifest_path, helper

    def test_valid_artifacts_prove_helper_checkonly_before_enforce_block(self) -> None:
        self.assertIsNotNone(shutil.which("aarch64-linux-gnu-gcc"))
        self.assertIsNotNone(shutil.which("qemu-aarch64"))
        with self.private_tmp() as tmp:
            root = Path(tmp)
            policy_path = root / "inputs" / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            filter_manifest, filter_object = self.write_filter_artifact(root)
            helper_manifest, helper_binary = self.write_loader_helper(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta159"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--wsta156-filter-manifest-json",
                str(filter_manifest),
                "--wsta156-filter-object",
                str(filter_object),
                "--wsta158-loader-helper-manifest-json",
                str(helper_manifest),
                "--wsta158-loader-helper",
                str(helper_binary),
                "--emit-seccomp-loader-checkonly-rootfs-proof",
            ]))
            dry_stdout = (root / "wsta159" / runner.DRY_RUN_STDOUT_NAME).read_text(encoding="utf-8")
            enforce_stdout = (root / "wsta159" / runner.ENFORCE_STDOUT_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["stage"]["seccomp_loader_helper"]["staged"])
        self.assertFalse(result["stage"]["seccomp_loader_helper"]["seccomp_enforced"])
        self.assertIn("A90WSTA159_SECCOMP_HELPER_PRESENT=1", dry_stdout)
        self.assertIn("fake_setpriv_args=--no-new-privs --reuid a90hud --regid a90hud", dry_stdout)
        self.assertIn("A90WSTA159_SECCOMP_HELPER_PRESENT=1", enforce_stdout)
        self.assertIn("A90WSTA158_LOADER_CHECK_ONLY=1", enforce_stdout)
        self.assertIn("A90WSTA158_SECCOMP_LOAD=0", enforce_stdout)
        self.assertIn("service=dpublic-hud policy_service=dpublic-hud-intent", enforce_stdout)
        self.assertIn("A90WSTA159_SECCOMP_HELPER_CHECK_ONLY_OK=1", enforce_stdout)
        self.assertIn("blocked-seccomp-enforce-unimplemented", enforce_stdout)
        self.assertTrue(result["proof_checks"]["enforce_blocks_before_exec"])

    def test_gate_blocks_without_explicit_flag_or_private_helper(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            policy_path = root / "inputs" / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            filter_manifest, filter_object = self.write_filter_artifact(root)
            helper_manifest, helper_binary = self.write_loader_helper(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta159"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--wsta156-filter-manifest-json",
                str(filter_manifest),
                "--wsta156-filter-object",
                str(filter_object),
                "--wsta158-loader-helper-manifest-json",
                str(helper_manifest),
                "--wsta158-loader-helper",
                str(helper_binary),
            ]))
        self.assertEqual(result["decision"], "wsta159-blocked-explicit-gate-required")

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_root = Path(outside)
            policy_path = root / "inputs" / "wsta153_seccomp_policy.json"
            self.write_json(policy_path, self.source_policy())
            filter_manifest, filter_object = self.write_filter_artifact(root)
            helper_manifest, helper_binary = self.write_loader_helper(outside_root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta159"),
                "--wsta153-seccomp-policy-json",
                str(policy_path),
                "--wsta156-filter-manifest-json",
                str(filter_manifest),
                "--wsta156-filter-object",
                str(filter_object),
                "--wsta158-loader-helper-manifest-json",
                str(helper_manifest),
                "--wsta158-loader-helper",
                str(helper_binary),
                "--emit-seccomp-loader-checkonly-rootfs-proof",
            ]))
        self.assertEqual(result["decision"], "wsta159-blocked-helper-manifest-nonprivate")


if __name__ == "__main__":
    unittest.main()
