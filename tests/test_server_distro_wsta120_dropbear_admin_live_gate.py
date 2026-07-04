from __future__ import annotations

import argparse
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta120_dropbear_admin_live_gate.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta120_dropbear_admin_live_gate.py")


def args(**overrides) -> argparse.Namespace:
    defaults = {
        "execute_dropbear_admin_live": False,
        "allow_dropbear_admin_live": False,
        "ack_admin_key_material": False,
        "ack_root_login_negative_test": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class ServerDistroWsta120DropbearAdminLiveGateTests(unittest.TestCase):
    def test_explicit_live_gate_requires_all_acknowledgements(self) -> None:
        self.assertEqual(
            runner.explicit_live_gate(args()),
            (False, "wsta120-blocked-dropbear-admin-live-required"),
        )
        self.assertEqual(
            runner.explicit_live_gate(args(execute_dropbear_admin_live=True)),
            (False, "wsta120-blocked-dropbear-admin-live-allow-required"),
        )
        self.assertEqual(
            runner.explicit_live_gate(args(
                execute_dropbear_admin_live=True,
                allow_dropbear_admin_live=True,
            )),
            (False, "wsta120-blocked-admin-key-material-ack-required"),
        )
        self.assertEqual(
            runner.explicit_live_gate(args(
                execute_dropbear_admin_live=True,
                allow_dropbear_admin_live=True,
                ack_admin_key_material=True,
            )),
            (False, "wsta120-blocked-root-login-negative-test-ack-required"),
        )
        self.assertEqual(
            runner.explicit_live_gate(args(
                execute_dropbear_admin_live=True,
                allow_dropbear_admin_live=True,
                ack_admin_key_material=True,
                ack_root_login_negative_test=True,
            )),
            (True, "ok"),
        )

    def test_safety_is_inert_until_live_gate(self) -> None:
        inert = runner.safety(False)
        live = runner.safety(True)

        self.assertFalse(inert["device_action"])
        self.assertFalse(inert["boot_flash"])
        self.assertFalse(inert["public_tunnel"])
        self.assertFalse(inert["admin_key_material"])
        self.assertEqual(inert["secret_values_logged"], 0)
        self.assertTrue(live["device_action"])
        self.assertEqual(live["admin_key_material"], "explicit-live-gated-private-run-key")
        self.assertTrue(live["root_login_negative_test"])
        self.assertFalse(live["boot_flash"])

    def test_admin_stage_script_uses_admin_model_without_root_authorized_keys(self) -> None:
        script = runner.admin_native_stage_and_start_script(
            "/mnt/a90",
            "ssh-ed25519 AAAATEST operator@example",
            "192.168.7.2",
            2222,
        )

        self.assertIn("A90WSTA120_ADMIN_STAGE_BEGIN", script)
        self.assertIn("A90WSTA120_ADMIN_STAGE_DONE", script)
        self.assertIn("a90admin:x:3903:3903:A90 admin a90admin:/home/a90admin:/bin/sh", script)
        self.assertIn("a90admin:x:3903:3903:A90 service a90admin:/nonexistent:/usr/sbin/nologin", script)
        self.assertIn("A90WSTA120_ACCOUNT_CONFLICT", script)
        self.assertIn("/home/a90admin/.ssh/authorized_keys", script)
        self.assertIn("/root/.ssh/authorized_keys", script)
        self.assertIn('/bin/busybox rm -f "$M$ROOT_KEYS"', script)
        self.assertIn("A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=1", script)
        self.assertIn("a90admin:*:19700:0:99999:7:::", script)
        self.assertIn('grep -Fqx "$SHADOW_LINE"', script)
        self.assertIn('cp "$M/etc/shadow" "$M/tmp/a90_d2_shadow.bak"', script)
        self.assertIn("/usr/sbin/dropbear -F -E", script)
        self.assertIn("-s -w -j -k", script)
        self.assertNotIn("$M/root/.ssh/authorized_keys\" > ", script)

    def test_parse_stage_requires_root_denied_admin_key_and_safe_dropbear(self) -> None:
        record = {
            "text": "\n".join([
                "A90WSTA120_ADMIN_STAGE_BEGIN",
                "A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=1",
                "A90WSTA120_ADMIN_PASSWD_LINE=1",
                "A90WSTA120_ADMIN_GROUP_LINE=1",
                "A90WSTA120_ADMIN_SHADOW_LINE=1",
                "A90WSTA120_ADMIN_AUTHORIZED_KEYS=1",
                "A90WSTA120_DROPBEAR_PRESENT=1",
                "A90WSTA120_HOSTKEY_TYPE=ed25519",
                "A90WSTA120_DROPBEAR_COMMAND=/usr/sbin/dropbear -F -E -r /tmp/a90_dropbear_admin_hostkey -p 192.168.7.2:2222 -P /tmp/a90_dropbear_admin.pid -s -w -j -k",
                "A90WSTA120_DROPBEAR_ALIVE=1",
                "A90WSTA120_DROPBEAR_LISTEN=1",
                "A90WSTA120_ADMIN_STAGE_DONE",
            ])
        }
        parsed = runner.parse_stage(record)
        missing_root_absent = runner.parse_stage({"text": str(record["text"]).replace(
            "A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=1",
            "A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=0",
        )})

        self.assertTrue(parsed["stage_done"])
        self.assertTrue(parsed["root_authorized_keys_absent"])
        self.assertTrue(parsed["admin_shadow_line"])
        self.assertTrue(parsed["dropbear_command_safe"])
        self.assertFalse(missing_root_absent["root_authorized_keys_absent"])

    def test_admin_ssh_parse_requires_a90admin_identity(self) -> None:
        parsed = runner.parse_admin_ssh({
            "returncode": 0,
            "stdout": "\n".join([
                "A90WSTA120_ADMIN_UID=3903",
                "A90WSTA120_ADMIN_GID=3903",
                "A90WSTA120_ADMIN_USER=a90admin",
                "A90WSTA120_ADMIN_GROUP=a90admin",
            ]),
        })
        wrong_uid = runner.parse_admin_ssh({
            "returncode": 0,
            "stdout": "A90WSTA120_ADMIN_UID=0\nA90WSTA120_ADMIN_GID=0",
        })

        self.assertTrue(parsed["ssh_ok"])
        self.assertTrue(parsed["uid_3903"])
        self.assertTrue(parsed["gid_3903"])
        self.assertTrue(parsed["user_a90admin"])
        self.assertTrue(parsed["group_a90admin"])
        self.assertFalse(wrong_uid["uid_3903"])

    def test_admin_cleanup_parse_requires_key_and_dropbear_absent(self) -> None:
        cleanup_script = runner.admin_key_cleanup_script("/mnt/a90")
        parsed = runner.parse_admin_cleanup({
            "text": "\n".join([
                "A90WSTA120_ADMIN_CLEANUP_BEGIN",
                "A90WSTA120 admin_keys_absent=1",
                "A90WSTA120 dropbear_absent=1",
                "A90WSTA120_ADMIN_CLEANUP_DONE",
            ])
        })
        dirty = runner.parse_admin_cleanup({"text": "A90WSTA120 admin_keys_absent=0"})
        pending_dropbear = {
            "admin_key_cleanup_parse": {
                "cleanup_done": True,
                "admin_keys_absent": True,
                "dropbear_absent": False,
            }
        }

        self.assertIn("for i in 1 2 3 4 5", cleanup_script)
        self.assertIn("kill -9", cleanup_script)
        self.assertTrue(parsed["cleanup_done"])
        self.assertTrue(parsed["admin_keys_absent"])
        self.assertTrue(parsed["dropbear_absent"])
        self.assertTrue(runner.admin_key_cleanup_ok(pending_dropbear))
        self.assertFalse(dirty["admin_keys_absent"])

    def test_classify_orders_root_rejection_before_cleanup(self) -> None:
        result = {"checks": {
            "explicit_live_gate": True,
            "local_image_present": True,
            "baseline_selftest_fail_zero": True,
            "native_stale_cleanup_ok": True,
            "remote_image_ready": True,
            "chroot_mount_ready": True,
            "admin_stage_script_uploaded": True,
            "admin_stage_pass": True,
            "admin_ssh_pass": True,
            "root_ssh_rejected": False,
            "admin_key_cleanup_ok": False,
            "chroot_cleanup_ok": False,
            "final_selftest_fail_zero": False,
        }}

        self.assertEqual(runner.classify(result), "wsta120-blocked-root-ssh-not-rejected")

    def test_source_is_bounded_and_reuses_wsta119_model(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("run_wsta119_dropbear_admin_model", source)
        self.assertIn("ack_root_login_negative_test", source)
        self.assertIn("root_authorized_keys_absent", source)
        self.assertIn("a90admin", source)
        self.assertNotIn("native_init_flash.py", source)


if __name__ == "__main__":
    unittest.main()
