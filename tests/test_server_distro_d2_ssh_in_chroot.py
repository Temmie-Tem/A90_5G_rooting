from __future__ import annotations

import unittest

from _loader import load_script


d2 = load_script("workspace/public/src/scripts/server-distro/run_d2_ssh_in_chroot.py")


class ServerDistroD2SshInChrootTests(unittest.TestCase):
    def test_setup_script_starts_key_only_dropbear_without_userdata_or_flash(self) -> None:
        script = d2.d2_setup_script(
            "/mnt/sdext/a90/runtime/debian.img",
            "/mnt/sdext/a90/runtime/distro-root",
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKey a90-d2-test",
            "192.168.7.2",
            2222,
        )

        self.assertIn("A90D2_DROPBEAR_STARTED", script)
        self.assertIn("/usr/sbin/dropbear", script)
        self.assertIn("/usr/bin/dropbearkey", script)
        self.assertIn("/root/.ssh/authorized_keys", script)
        self.assertIn("-s -j -k", script)
        self.assertIn("shadow_temp_key_only=1", script)
        self.assertIn("mount -t ext4 -o rw", script)
        self.assertIn("losetup \"$LOOP\" \"$IMG\"", script)
        self.assertNotIn("/dev/block/sda33", script)
        self.assertNotIn("mkfs", script)
        self.assertNotIn(" userdata", script)

    def test_cleanup_script_stops_dropbear_restores_shadow_and_unmounts(self) -> None:
        script = d2.d2_cleanup_script("/mnt/sdext/a90/runtime/distro-root")
        postcheck = d2.d2_postcheck_script("/mnt/sdext/a90/runtime/distro-root")

        self.assertIn("A90D2_CLEANUP_BEGIN", script)
        self.assertIn("shadow_restored=1", script)
        self.assertIn("cleanup_mount_absent=1", script)
        self.assertIn("cleanup_loop_node_absent=1", script)
        self.assertIn("cleanup_dropbear_absent=1", script)
        self.assertIn("A90D2_CLEANUP_DONE", script)
        self.assertIn("A90D2_POSTCHECK_DONE", postcheck)
        self.assertIn("post_dropbear_absent=1", postcheck)
        self.assertIn("kill \"$PID\"", script)
        self.assertIn("umount \"$MNT\"", script)
        self.assertIn("losetup -d \"$LOOP\"", script)

    def test_parse_markers(self) -> None:
        setup = d2.parse_setup(
            """
A90D2 mounted=1
A90D2 authorized_keys=1
A90D2 shadow_temp_key_only=1
A90D2 loop_major=7
A90D2 loop_node_created=1
A90D2 hostkey_type=ed25519
A90D2 dropbear_pid=1234
A90D2_DROPBEAR_STARTED
"""
        )
        ssh = d2.parse_ssh_marker(
            """
A90D2_SSH_MARKER
debian_version=12.14
stage_marker=present
"""
        )
        cleanup = d2.parse_cleanup(
            """
A90D2 shadow_restored=1
A90D2 cleanup_mount_absent=1
A90D2 cleanup_loop_node_absent=1
A90D2 cleanup_dropbear_absent=1
A90D2_CLEANUP_DONE
"""
        )
        postcheck = d2.parse_postcheck(
            """
A90D2 post_mount_absent=1
A90D2 post_loop_node_absent=1
A90D2 post_dropbear_absent=1
A90D2_POSTCHECK_DONE
"""
        )

        self.assertTrue(setup["started"])
        self.assertTrue(setup["mounted"])
        self.assertEqual(setup["loop_major"], "7")
        self.assertEqual(setup["hostkey_type"], "ed25519")
        self.assertTrue(ssh["marker"])
        self.assertEqual(ssh["debian_version"], "12.14")
        self.assertTrue(ssh["stage_marker_present"])
        self.assertTrue(cleanup["done"])
        self.assertTrue(cleanup["shadow_restored"])
        self.assertTrue(cleanup["dropbear_cleanup_ok"])
        self.assertTrue(postcheck["done"])
        self.assertTrue(postcheck["dropbear_absent"])


if __name__ == "__main__":
    unittest.main()
