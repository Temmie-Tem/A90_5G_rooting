from __future__ import annotations

import unittest

from _loader import load_script


d0 = load_script("workspace/public/src/scripts/server-distro/collect_d0_device_inventory.py")


def rec(name: str, text: str) -> dict[str, object]:
    return {"name": name, "text": text, "rc": 0, "status": "ok"}


class ServerDistroD0InventoryTests(unittest.TestCase):
    def test_observation_commands_are_read_only(self) -> None:
        forbidden = (" mkfs", " mke2fs", " dd ", " of=", " mount ", " losetup ", " rm ", " reboot")
        for obs in d0.OBSERVATIONS:
            command = f" {obs.command} "
            self.assertNotIn(">>", command, obs)
            self.assertNotRegex(command, r"(^|[^2])>\s*/", obs)
            for token in forbidden:
                self.assertNotIn(token, command, obs)

    def test_classify_inventory_summary(self) -> None:
        raw = {
            "observations": [
                rec(
                    "df",
                    "\n".join([
                        "Filesystem 1K-blocks Used Available Use% Mounted on",
                        "/dev/block/mmcblk0p1 61407232 8400000 53000000 14% /mnt/sdext",
                        "__A90_D0_DF_K__",
                        "Filesystem 1K-blocks Used Available Use% Mounted on",
                        "/dev/block/mmcblk0p1 61407232 8400000 53000000 14% /mnt/sdext",
                    ]),
                ),
                rec(
                    "userdata_identity",
                    "\n".join([
                        "userdata_real=",
                        "userdata_device=/dev/block/sda33",
                        "userdata_block=sda33",
                        "userdata_sectors=244140625",
                    ]),
                ),
                rec(
                    "mounts",
                    "\n".join([
                        "/dev/block/mmcblk0p1 /mnt/sdext ext4 rw,seclabel,relatime 0 0",
                        "tmpfs /tmp tmpfs rw,nosuid,nodev 0 0",
                        "proc /proc proc rw,relatime 0 0",
                    ]),
                ),
                rec(
                    "busybox_applets",
                    "\n".join(["ash", "cat", "chroot", "losetup", "mount", "switch_root", "tar"]),
                ),
                rec(
                    "loop_dm_filesystems",
                    "\n".join([
                        "crw------- 1 root root 10, 237 /dev/loop-control",
                        "brw------- 1 root root 7, 0 /dev/loop0",
                        "__A90_D0_PROC_DEVICES__",
                        "Block devices:",
                        "  7 loop",
                        "__A90_D0_FILESYSTEMS__",
                        "nodev\ttmpfs",
                        "\text4",
                        "nodev\toverlay",
                    ]),
                ),
                rec(
                    "kernel_config",
                    "\n".join([
                        "CONFIG_NAMESPACES=y",
                        "CONFIG_NET_NS=y",
                        "CONFIG_SECCOMP=y",
                        "CONFIG_SECCOMP_FILTER=y",
                        "CONFIG_TUN=y",
                        "CONFIG_BLK_DEV_LOOP=y",
                        "CONFIG_EXT4_FS=y",
                        "# CONFIG_OVERLAY_FS is not set",
                    ]),
                ),
                rec("tun_device", "crw-rw-rw- 1 root root 10, 200 /dev/net/tun"),
                rec("mem_cpu", "MemTotal:        5504000 kB\n__A90_D0_CPU_COUNT__\n8\n"),
            ],
            "host_staging": {
                "image_present": True,
                "image_size_bytes": 2147483648,
                "cloudflared_present": True,
            },
        }

        summary = d0.classify_inventory(raw)

        self.assertEqual(summary["decision"], "server-distro-d0-device-live-read-only-inventory-pass")
        self.assertTrue(summary["read_only"])
        self.assertFalse(summary["flash_performed"])
        self.assertEqual(summary["sd"]["mountpoint"], "/mnt/sdext")
        self.assertGreater(summary["sd"]["available_1k"] * 1024, 2147483648)
        self.assertEqual(summary["userdata"]["block"], "sda33")
        self.assertEqual(summary["userdata"]["realpath"], "/dev/block/sda33")
        self.assertEqual(summary["userdata"]["bytes"], 125000000000)
        self.assertTrue(summary["required_applets"]["chroot"])
        self.assertTrue(summary["required_applets"]["switch_root"])
        self.assertFalse(summary["required_applets"]["mkfs.ext4"])
        self.assertTrue(summary["filesystems"]["ext4"])
        self.assertTrue(summary["loop_dm"]["loop_control_present"])
        self.assertTrue(summary["loop_dm"]["loop_block_major_present"])
        self.assertTrue(summary["loop_available"])
        self.assertTrue(summary["tun_device_present"])
        self.assertEqual(summary["kernel_config"]["CONFIG_OVERLAY_FS"], "n")
        self.assertEqual(summary["mem_cpu"]["cpu_count"], 8)
        self.assertTrue(summary["d1_chroot_mvp_ready"])


if __name__ == "__main__":
    unittest.main()
