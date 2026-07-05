from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta209_dropbear_admin_seccomp_live.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta209_dropbear_admin_seccomp_live.py")
TOKEN_LITERAL = "WSTA161-" + "EXPLICIT-ALLOW-SECCOMP-LOAD"
FORBIDDEN_FLASH = "native_" + "init_flash.py"
FORBIDDEN_TUNNEL_HOST = "try" + "cloudflare.com"
FORBIDDEN_SSID = "ss" + "id="
FORBIDDEN_PSK = "ps" + "k="


class ServerDistroWsta209DropbearAdminSeccompLiveTests(unittest.TestCase):
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
            str(root / "wsta209-live"),
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
        policy.write_text('{"schema":"a90-wsta153-seccomp-policy-source-v1","services":[]}\n', encoding="utf-8")
        filter_manifest.write_text('{"schema":"test"}\n', encoding="utf-8")
        filter_object.write_bytes(b"obj")
        helper_manifest.write_text('{"exec_after_load_compiled":true}\n', encoding="utf-8")
        helper_binary.write_bytes(b"helper")
        helper_binary.chmod(0o755)
        return {"manifest": helper_manifest, "helper": helper_binary}

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

    def stage_text(self) -> str:
        return "\n".join([
            "A90WSTA209_ADMIN_SECCOMP_STAGE_BEGIN",
            "A90WSTA209_ASSET_PRESENT=1",
            "A90WSTA209_SECCOMP_ASSETS_STAGED=1",
            "A90WSTA209_ROOT_AUTHORIZED_KEYS_ABSENT=1",
            "A90WSTA209_ADMIN_PASSWD_LINE=1",
            "A90WSTA209_ADMIN_GROUP_LINE=1",
            "A90WSTA209_ADMIN_SHADOW_LINE=1",
            "A90WSTA209_ADMIN_AUTHORIZED_KEYS=1",
            "A90WSTA209_DROPBEAR_PRESENT=1",
            "A90WSTA209_LOADER_HELPER_PRESENT=1",
            "A90WSTA209_HOSTKEY_TYPE=ed25519",
            "A90WSTA209_DROPBEAR_COMMAND=/usr/sbin/dropbear -F -E -r /tmp/key -p 192.168.7.2:2222 -P /tmp/pid -s -w -j -k",
            "A90WSTA209_DROPBEAR_ALIVE=1",
            "A90WSTA209_DROPBEAR_LISTEN=1",
            "A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1",
            "A90WSTA209_ADMIN_SECCOMP_STAGE_DONE",
            "",
        ])

    def admin_ssh_record(self) -> dict:
        return {
            "returncode": 0,
            "stdout": "\n".join([
                "A90WSTA120_ADMIN_UID=3903",
                "A90WSTA120_ADMIN_GID=3903",
                "A90WSTA120_ADMIN_USER=a90admin",
                "A90WSTA120_ADMIN_GROUP=a90admin",
                "",
            ]),
            "stderr": "",
        }

    def test_default_run_is_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta209"),
            ]))

        self.assertEqual(result["decision"], "wsta209-blocked-dropbear-admin-seccomp-live-required")
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["boot_flash"])
        self.assertFalse(result["safety"]["native_reboot"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])

    def test_stage_script_execs_dropbear_through_seccomp_helper_as_root_boundary(self) -> None:
        script = runner.dropbear_seccomp_stage_script(
            "/mnt/root",
            "ssh-ed25519 test",
            "192.168.7.2",
            2222,
        )

        self.assertIn("--service dropbear-admin-usb --apply --exec --", script)
        self.assertIn("/usr/sbin/dropbear -F -E -r", script)
        self.assertIn("-s -w -j -k", script)
        self.assertIn("LOAD_TOKEN=$(/bin/busybox cat \"$TOKEN_FILE\")", script)
        self.assertIn("A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1", script)
        self.assertIn("A90WSTA209_ADMIN_SECCOMP_STAGE_DONE", script)
        self.assertNotIn(TOKEN_LITERAL, script)
        self.assertNotIn(FORBIDDEN_TUNNEL_HOST, script)

    def test_parse_stage_requires_seccomp_dropbear_markers(self) -> None:
        parsed = runner.parse_stage({"text": self.stage_text()})

        self.assertTrue(parsed["stage_done"])
        self.assertTrue(parsed["assets_present"])
        self.assertTrue(parsed["seccomp_assets_staged"])
        self.assertTrue(parsed["dropbear_alive"])
        self.assertTrue(parsed["seccomp_dropbear_markers"])
        self.assertTrue(parsed["token_literal_absent"])

        missing = runner.parse_stage({"text": self.stage_text().replace("A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1", "")})
        self.assertFalse(missing["seccomp_dropbear_markers"])

    def test_classify_requires_admin_login_root_reject_and_cleanup(self) -> None:
        checks = {
            "explicit_live_gate": True,
            "private_run_dir": True,
            "private_token_env_present": True,
            "private_token_matches_wsta161": True,
            "fresh_health_valid": True,
            "helper_built": True,
            "helper_exec_after_load_compiled": True,
            "local_image_present": True,
            "local_image_expected_sha": True,
            "ssh_key_generated": True,
            "native_stale_cleanup_ok": True,
            "remote_image_ready": True,
            "seccomp_asset_inputs_valid": True,
            "seccomp_assets_installed": True,
            "stage_script_uploaded": True,
            "chroot_mount_ready": True,
            "admin_seccomp_stage_pass": True,
            "seccomp_dropbear_markers": True,
            "admin_ssh_pass": True,
            "root_ssh_rejected": True,
            "admin_seccomp_cleanup_ok": True,
            "chroot_cleanup_ok": True,
            "post_health_valid": True,
        }

        self.assertEqual(runner.classify({"checks": checks}), runner.PASS_DECISION)
        self.assertEqual(
            runner.classify({"checks": {**checks, "admin_ssh_pass": False}}),
            "wsta209-blocked-admin-ssh",
        )
        self.assertEqual(
            runner.classify({"checks": {**checks, "root_ssh_rejected": False}}),
            "wsta209-blocked-root-ssh-not-rejected",
        )

    def test_cleanup_ok_accepts_dropbear_removed_by_final_chroot_cleanup_only(self) -> None:
        result = {
            "admin_seccomp_cleanup_parse": {
                "cleanup_done": True,
                "admin_keys_absent": True,
                "asset_dir_absent": True,
                "dropbear_absent": False,
            },
            "cleanup_parse": {"dropbear_cleanup_ok": True},
        }

        self.assertTrue(runner.cleanup_ok(result))
        result["cleanup_parse"]["dropbear_cleanup_ok"] = False
        self.assertFalse(runner.cleanup_ok(result))

    def test_mocked_live_path_proves_admin_login_under_seccomp(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            (root / "debian.img").write_text("fake", encoding="utf-8")
            helper = self.write_inputs(root)
            cleanup_text = "\n".join([
                "A90WSTA209_ADMIN_SECCOMP_CLEANUP_BEGIN",
                "A90WSTA209 admin_keys_absent=1",
                "A90WSTA209 dropbear_absent=1",
                "A90WSTA209 asset_dir_absent=1",
                "A90WSTA209_ADMIN_SECCOMP_CLEANUP_DONE",
                "",
            ])
            chroot_cleanup = (
                "A90D2_CLEANUP_DONE\n"
                "A90D2 shadow_restored=1\n"
                "A90D2 cleanup_mount_absent=1\n"
                "A90D2 cleanup_loop_node_absent=1\n"
                "A90D2 cleanup_dropbear_absent=1\n"
            )
            postcheck = (
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
                mock.patch.object(runner.d1, "sha256_file", return_value="fake-sha"), \
                mock.patch.object(runner.d2, "generate_ssh_key", return_value={"returncode": 0}), \
                mock.patch.object(runner.d2, "read_public_key", return_value="ssh-ed25519 test"), \
                mock.patch.object(runner.wsta94, "native_stale_cleanup", return_value={"cleaned": True}), \
                mock.patch.object(runner.wsta42, "prepare_remote_work_image", return_value=True), \
                mock.patch.object(runner, "install_seccomp_assets", return_value={
                    "installed": True,
                    "token_input_redacted": True,
                }), mock.patch.object(runner, "install_file", return_value={"installed": True}), \
                mock.patch.object(runner.wsta19, "bridge_shell", side_effect=[
                    self.bridge_record("A90D2_MOUNT_READY\nA90D2 mounted=1\n"),
                    self.bridge_record(cleanup_text),
                    self.bridge_record(chroot_cleanup),
                    self.bridge_record(postcheck),
                ]), mock.patch.object(runner.wsta120, "bridge_run_script_file", return_value={
                    "rc": 0,
                    "text": self.stage_text(),
                }), mock.patch.object(runner.wsta120, "ssh_probe", side_effect=[
                    self.admin_ssh_record(),
                    {"returncode": 255, "stdout": "", "stderr": "permission denied"},
                ]):
                    result = runner.run(runner.build_arg_parser().parse_args(self.live_args(root)))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["safety"]["seccomp_filter_loaded"])
        self.assertTrue(result["safety"]["seccomp_enforced"])
        self.assertTrue(result["safety"]["service_functional_under_seccomp"])
        self.assertTrue(result["checks"]["root_ssh_rejected"])
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
