from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta208_real_service_seccomp_smoke_live.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta208_real_service_seccomp_smoke_live.py")
TOKEN_LITERAL = "WSTA161-" + "EXPLICIT-ALLOW-SECCOMP-LOAD"
FORBIDDEN_FLASH = "native_" + "init_flash.py"
FORBIDDEN_TUNNEL_HOST = "try" + "cloudflare.com"
FORBIDDEN_SSID = "ss" + "id="
FORBIDDEN_PSK = "ps" + "k="


class ServerDistroWsta208RealServiceSeccompSmokeLiveTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def health_ok(self) -> dict:
        return {
            "checks": {
                "bridge_ready": True,
                "version_ok": True,
                "status_ok": True,
                "selftest_fail_zero": True,
            }
        }

    def bridge_record(self, text: str) -> dict:
        return {"rc": 0, "text": text}

    def live_args(self, root: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta208-live"),
            "--local-image",
            str(root / "debian.img"),
            "--local-image-sha256",
            "fake-sha",
            "--wsta153-seccomp-policy-json",
            str(root / "inputs" / "wsta153_seccomp_policy.json"),
            "--wsta156-filter-manifest-json",
            str(root / "inputs" / "wsta156_seccomp_filter_manifest.json"),
            "--wsta156-filter-object",
            str(root / "inputs" / "wsta156_seccomp_filters.o"),
            *runner.ACK_FLAGS,
        ]

    def write_inputs(self, root: Path) -> dict[str, Path]:
        inputs = root / "inputs"
        inputs.mkdir(parents=True, exist_ok=True)
        policy = inputs / "wsta153_seccomp_policy.json"
        filter_manifest = inputs / "wsta156_seccomp_filter_manifest.json"
        filter_object = inputs / "wsta156_seccomp_filters.o"
        helper_manifest = inputs / "wsta161_seccomp_loader_helper_manifest.json"
        helper_binary = inputs / "a90-seccomp-loader-gated-apply"
        policy.write_text(
            json.dumps({"schema": "a90-wsta153-seccomp-policy-source-v1", "services": []}) + "\n",
            encoding="utf-8",
        )
        filter_manifest.write_text('{"schema":"test"}\n', encoding="utf-8")
        filter_object.write_bytes(b"obj")
        helper_manifest.write_text('{"exec_after_load_compiled":true}\n', encoding="utf-8")
        helper_binary.write_bytes(b"helper")
        helper_binary.chmod(0o755)
        return {
            "manifest": helper_manifest,
            "helper": helper_binary,
        }

    def helper_result(self, helper: dict[str, Path]) -> dict:
        return {
            "decision": runner.wsta161.PASS_DECISION,
            "artifact": {
                "manifest": runner.rel(helper["manifest"]),
                "helper_binary": runner.rel(helper["helper"]),
                "apply_code_compiled": True,
            },
            "manifest_checks": {
                "exec_after_load_compiled": True,
            },
        }

    def service_stdout(self) -> str:
        return "\n".join([
            "A90WSTA208_REAL_SERVICE_BEGIN",
            "A90WSTA208_LOOPBACK_UP_RC=0",
            "A90WSTA208_LOOPBACK_ADDR_PRESENT=1",
            "A90WSTA208_SMOKE_PID=123",
            "A90WSTA208_SMOKE_STARTED=1",
            "A90WSTA208_HTTP_RC=0",
            "A90WSTA208_HTTP_OUT_BEGIN",
            "HTTP/1.1 200 OK",
            "A90_DPUBLIC_SMOKE_OK",
            "A90WSTA208_HTTP_OUT_END",
            "A90WSTA208_SMOKE_LOG_BEGIN",
            "A90WSTA154_SECCOMP_SERVICE=dpublic-smoke-httpd",
            "A90WSTA164_SECCOMP_LOAD_ENV_GATE=1",
            "A90WSTA208_SECCOMP_EXEC_AFTER_LOAD=1",
            "a90_service_launcher_decision=exec-seccomp",
            "a90_service_launcher_service=dpublic-smoke-httpd",
            "a90_service_launcher_user=a90www",
            "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1",
            "A90WSTA161_SECCOMP_LOAD=1",
            "a90_seccomp_loader_decision=loaded",
            "A90WSTA208_EXEC_AFTER_LOAD=1",
            "a90-dpublic-smoke listening on 127.0.0.1:8080",
            "A90WSTA208_SMOKE_LOG_END",
            "A90WSTA208_LOOPBACK_OK=1",
            "A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1",
            "A90WSTA208_REAL_SERVICE_PASS",
            "",
        ])

    def test_default_run_is_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta208"),
            ]))

        self.assertEqual(result["decision"], "wsta208-blocked-real-service-live-required")
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["boot_flash"])
        self.assertFalse(result["safety"]["native_reboot"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])

    def test_remote_service_script_loads_before_exec_and_configures_loopback(self) -> None:
        script = runner.remote_service_script()

        self.assertIn("A90_SERVICE_LAUNCH_SECCOMP_EXEC_AFTER_LOAD=1", script)
        self.assertIn('"$LAUNCHER" dpublic-smoke-httpd "$SMOKE" 127.0.0.1 8080', script)
        self.assertIn("ip_cmd link set lo up", script)
        self.assertIn("ip_cmd addr add 127.0.0.1/8 dev lo", script)
        self.assertIn("A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1", script)
        self.assertIn("A90WSTA208_REAL_SERVICE_PASS", script)
        self.assertNotIn("cloudflared tunnel", script)
        self.assertNotIn(FORBIDDEN_TUNNEL_HOST, script)

    def test_parse_service_probe_requires_real_service_markers(self) -> None:
        parsed = runner.parse_service_probe({
            "returncode": 0,
            "stdout": self.service_stdout(),
            "stderr": "",
        })

        self.assertTrue(parsed["returncode_zero"])
        self.assertTrue(parsed["loaded_marker"])
        self.assertTrue(parsed["exec_after_load_marker"])
        self.assertTrue(parsed["real_service_markers"])
        self.assertTrue(parsed["loopback_ok"])
        self.assertTrue(parsed["pass_marker"])
        self.assertTrue(parsed["token_literal_absent"])

        missing = runner.parse_service_probe({
            "returncode": 0,
            "stdout": self.service_stdout().replace("A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1", ""),
            "stderr": "",
        })
        self.assertFalse(missing["real_service_markers"])

    def test_classify_requires_cleanup_and_post_health(self) -> None:
        checks = {
            "explicit_live_gate": True,
            "private_run_dir": True,
            "private_token_env_present": True,
            "private_token_matches_wsta161": True,
            "fresh_health_valid": True,
            "helper_built": True,
            "helper_exec_after_load_compiled": True,
            "dpublic_helpers_built": True,
            "local_image_present": True,
            "local_image_expected_sha": True,
            "ssh_key_generated": True,
            "native_stale_cleanup_ok": True,
            "remote_image_ready": True,
            "chroot_mount_ready": True,
            "dropbear_started": True,
            "debian_ssh_marker": True,
            "seccomp_asset_inputs_valid": True,
            "seccomp_assets_staged": True,
            "loopback_binaries_staged": True,
            "execution_returncode_zero": True,
            "seccomp_real_service_markers": True,
            "service_functional_under_seccomp": True,
            "chroot_cleanup_ok": True,
            "post_health_valid": True,
        }

        self.assertEqual(runner.classify({"checks": checks}), runner.PASS_DECISION)
        self.assertEqual(
            runner.classify({"checks": {**checks, "service_functional_under_seccomp": False}}),
            "wsta208-blocked-service-functional",
        )
        self.assertEqual(
            runner.classify({"checks": {**checks, "chroot_cleanup_ok": False}}),
            "wsta208-blocked-chroot-cleanup",
        )

    def test_mocked_live_path_execs_real_smoke_service_under_seccomp(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            (root / "debian.img").write_text("fake", encoding="utf-8")
            helper = self.write_inputs(root)
            mount_text = "A90D2_MOUNT_READY\nA90D2 mounted=1\n"
            start_text = "A90D2_DROPBEAR_STARTED\nA90D2 authorized_keys=1\nA90D2 shadow_temp_key_only=1\n"
            cleanup_text = "A90D2_CLEANUP_DONE\nA90D2 shadow_restored=1\n"
            postcheck_text = (
                "A90D2_POSTCHECK_DONE\n"
                "A90D2 post_mount_absent=1\n"
                "A90D2 post_loop_node_absent=1\n"
                "A90D2 post_dropbear_absent=1\n"
            )
            with mock.patch.dict(runner.os.environ, {
                runner.wsta193.PRIVATE_TOKEN_ENV: runner.wsta161.LOAD_TOKEN
            }), mock.patch.object(runner.wsta196, "run_readonly_health_checks", side_effect=[
                self.health_ok(),
                self.health_ok(),
            ]), mock.patch.object(runner, "build_exec_loader_helper", return_value=self.helper_result(helper)), \
                mock.patch.object(runner.wsta42, "build_dpublic_helpers", return_value={"ok": True}), \
                mock.patch.object(runner.d1, "sha256_file", return_value="fake-sha"), \
                mock.patch.object(runner.d2, "generate_ssh_key", return_value={"returncode": 0}), \
                mock.patch.object(runner.d2, "read_public_key", return_value="ssh-ed25519 test"), \
                mock.patch.object(runner.wsta94, "native_stale_cleanup", return_value={"cleaned": True}), \
                mock.patch.object(runner.wsta42, "prepare_remote_work_image", return_value=True), \
                mock.patch.object(runner.wsta19, "bridge_shell", side_effect=[
                    self.bridge_record(mount_text),
                    self.bridge_record(start_text),
                    self.bridge_record(cleanup_text),
                    self.bridge_record(postcheck_text),
                ]), mock.patch.object(runner.wsta19, "ssh_chroot_marker", return_value={
                    "marker": {"marker": True, "debian_version": "12.14"}
                }), mock.patch.object(runner, "stage_seccomp_assets", return_value={"staged": True}), \
                mock.patch.object(runner.wsta94, "stage_loopback_binaries", return_value={
                    "smoke_httpd": {"staged": True},
                    "http_get": {"staged": True},
                }), mock.patch.object(runner, "ssh_exec_token_script", return_value={
                    "returncode": 0,
                    "stdout": self.service_stdout(),
                    "stderr": "",
                }) as ssh_exec, mock.patch.object(runner.wsta42, "cleanup_dpublic", return_value={"cleaned": True}):
                    result = runner.run(runner.build_arg_parser().parse_args(self.live_args(root)))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["safety"]["seccomp_filter_loaded"])
        self.assertTrue(result["safety"]["seccomp_enforced"])
        self.assertTrue(result["safety"]["service_functional_under_seccomp"])
        self.assertTrue(result["checks"]["service_functional_under_seccomp"])
        remote_script = ssh_exec.call_args.args[2]
        self.assertIn("A90_SERVICE_LAUNCH_SECCOMP_EXEC_AFTER_LOAD=1", remote_script)
        self.assertNotIn(runner.wsta161.LOAD_TOKEN, json.dumps(result, sort_keys=True))

    def test_source_has_no_public_or_credential_surface(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn('"public_tunnel": False', source)
        self.assertIn('"wifi_connect": False', source)
        self.assertIn('"boot_flash": False', source)
        self.assertNotIn(TOKEN_LITERAL, source)
        self.assertNotIn(FORBIDDEN_FLASH, source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn(FORBIDDEN_TUNNEL_HOST, source)
        self.assertNotIn(FORBIDDEN_SSID, source.lower())
        self.assertNotIn(FORBIDDEN_PSK, source.lower())


if __name__ == "__main__":
    unittest.main()
