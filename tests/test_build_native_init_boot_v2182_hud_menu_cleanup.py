"""Regression tests for build_native_init_boot_v2182_hud_menu_cleanup."""

from __future__ import annotations

import json
import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_revalidation


v2182 = load_revalidation("build_native_init_boot_v2182_hud_menu_cleanup")


def namespace_chain(*names, leaf):
    current = leaf
    for name in reversed(names):
        current = types.SimpleNamespace(**{name: current})
    return current


def fake_base_args():
    return [
        "--cycle",
        "OLD",
        "--decision",
        "old-decision",
        "--cycle-label",
        "old-label",
        "--init-version",
        "0.0.0",
        "--init-build",
        "old-build",
        "--out-dir",
        "old-out",
        "--init-binary",
        "old-init",
        "--helper-binary",
        "old-helper",
        "--ramdisk-cpio",
        "old-ramdisk",
        "--boot-image",
        "old-boot",
        "--wifi-test-klog-prefix",
        "OLD",
        "--wifi-test-disable",
        "old-disable",
        "--wifi-test-log",
        "old-log",
        "--wifi-test-summary",
        "old-summary",
        "--wifi-test-helper-result",
        "old-helper-result",
        "--wifi-test-pid",
        "old-pid",
        "--wifi-test-watcher-pid",
        "old-watcher",
        "--wifi-test-property-root",
        "old-prop",
    ]


class FakeLegacyMkbootimgDir:
    def __init__(self, symlink=True) -> None:
        self.symlink = symlink
        self.unlinked = False

    def is_symlink(self) -> bool:
        return self.symlink

    def unlink(self) -> None:
        self.unlinked = True


def fake_v2178_module(fake_base, helper_builder=None, legacy_dir=None):
    def set_arg(args, key, value):
        index = args.index(key)
        args[index + 1] = value

    v726 = types.SimpleNamespace(
        set_arg=set_arg,
        v2168=namespace_chain(
            "prev2137",
            "prev2135",
            "prev2133",
            "prev2131",
            "prev2129",
            "prev2127",
            "prev2120",
            "prev2112",
            "prev2108",
            "prev2106",
            "prev2102",
            "prev2100",
            "prev2097",
            "prev2095",
            "prev2082",
            "prev2080",
            "prev2058",
            "prev2038",
            leaf=helper_builder or types.SimpleNamespace(patch_helper_builder=lambda base: None),
        ),
    )
    v2169 = types.SimpleNamespace(
        v726=v726,
        ensure_legacy_mkbootimg_link=lambda: True,
        LEGACY_MKBOOTIMG_DIR=legacy_dir or FakeLegacyMkbootimgDir(),
    )
    v2174 = types.SimpleNamespace(v2169=v2169)
    v2176 = types.SimpleNamespace(v2174=v2174)
    return types.SimpleNamespace(
        base_module=lambda: fake_base,
        configure_base=lambda: setattr(fake_base, "configured_by_v2178", True),
        REMOTE_PROPERTY_ROOT="/fake/property-root",
        EXPECTED_HELPER_MARKER="fake-marker",
        EXPECTED_HELPER_SHA256="fake-sha",
        EXTRA_INIT_FLAGS=("-DA90_TRANSPORT_STATUS_CONTRACT=1",),
        v2176=v2176,
    )


class BuildWrapperConfiguration(unittest.TestCase):
    def test_configure_base_rewrites_v2178_axes_for_hud_menu_baseline(self) -> None:
        old_v2178 = v2182.v2178
        fake_base = types.SimpleNamespace(
            DEFAULT_ARGS=fake_base_args(),
            base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]),
        )
        fake_v2178 = fake_v2178_module(fake_base)
        v2182.v2178 = fake_v2178
        try:
            v2182.configure_base()
        finally:
            v2182.v2178 = old_v2178

        args = dict(zip(fake_base.DEFAULT_ARGS[0::2], fake_base.DEFAULT_ARGS[1::2]))
        self.assertTrue(fake_base.configured_by_v2178)
        self.assertEqual(fake_v2178.OUT_DIR, v2182.OUT_DIR)
        self.assertEqual(fake_v2178.REPORT_PATH, v2182.REPORT_PATH)
        self.assertEqual(fake_v2178.BOOT_IMAGE, v2182.BOOT_IMAGE)
        self.assertEqual(fake_v2178.INIT_BINARY, v2182.INIT_BINARY)
        self.assertEqual(fake_v2178.RAMDISK_CPIO, v2182.RAMDISK_CPIO)
        self.assertEqual(args["--cycle"], "V2182")
        self.assertEqual(args["--decision"], "v2182-hud-menu-cleanup-source-build-pass")
        self.assertEqual(args["--cycle-label"], "v2182")
        self.assertEqual(args["--init-version"], "0.9.255")
        self.assertEqual(args["--init-build"], "v2182-hud-menu-cleanup")
        self.assertEqual(args["--wifi-test-klog-prefix"], "A90v2182")
        self.assertEqual(args["--wifi-test-disable"], "/cache/native-init-wifi-test-boot-v2182.disable")
        self.assertEqual(args["--wifi-test-log"], "/cache/native-init-wifi-test-boot-v2182.log")
        self.assertEqual(
            args["--wifi-test-helper-result"],
            "/cache/native-init-wifi-test-boot-v2182-helper.result",
        )
        self.assertEqual(args["--wifi-test-property-root"], v2182.REMOTE_PROPERTY_ROOT)
        self.assertIn("a90_android_execns_probe_v427_hud_menu_cleanup", args["--helper-binary"])
        self.assertEqual(fake_base.base.EXTRA_INIT_FLAGS, v2182.EXTRA_INIT_FLAGS)

    def test_main_patches_helper_and_removes_temporary_legacy_link(self) -> None:
        old_v2178 = v2182.v2178
        fake_base = types.SimpleNamespace(
            DEFAULT_ARGS=fake_base_args(),
            base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]),
            main=lambda: 1,
        )
        patched_bases = []
        helper_builder = types.SimpleNamespace(
            patch_helper_builder=lambda base: patched_bases.append(base),
        )
        legacy_dir = FakeLegacyMkbootimgDir(symlink=True)
        v2182.v2178 = fake_v2178_module(fake_base, helper_builder=helper_builder, legacy_dir=legacy_dir)
        try:
            rc = v2182.main()
        finally:
            v2182.v2178 = old_v2178

        self.assertEqual(rc, 1)
        self.assertEqual(patched_bases, [fake_base])
        self.assertIs(fake_base.render_report, v2182.render_report)
        self.assertTrue(legacy_dir.unlinked)

    def test_render_report_records_hud_storage_wifi_glance_and_menu_cleanup_scope(self) -> None:
        manifest = {
            "decision": "v2182-hud-menu-cleanup-source-build-pass",
            "base_boot": "workspace/private/inputs/boot_images/base.img",
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2182.img",
            "boot_sha256": "boot-sha",
            "init_version": "0.9.255",
            "init_build": "v2182-hud-menu-cleanup",
            "helper_marker": "a90_android_execns_probe v427",
            "helper_sha256": "helper-sha",
            "wifi_test": {
                "helper_runtime_mode": "wifi-companion",
                "helper_timeout_sec": 75,
            },
        }

        report = v2182.render_report(manifest)

        self.assertIn("# Native Init V2182 HUD/Menu Cleanup Source Build", report)
        self.assertIn("Decision: `v2182-hud-menu-cleanup-source-build-pass`", report)
        self.assertIn("HUD storage free/free-percent/read-write-rate line", report)
        self.assertIn("Wi-Fi state/profile/decision surfacing", report)
        self.assertIn("shared HUD status geometry", report)
        self.assertIn("removes duplicate STATUS/LIVE STATUS navigation", report)
        self.assertIn("USB NET STATUS versus Wi-Fi HUD status", report)
        self.assertIn("Raw SSID/PSK remain private-only", report)
        self.assertIn("No scan/connect/DHCP/ping is initiated", report)
        self.assertIn("No `/dev/subsys_esoc0`", report)

    def test_normalize_manifest_axes_records_promoted_hud_menu_baseline(self) -> None:
        old_out_dir = v2182.OUT_DIR
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                out_dir = Path(temp_dir)
                manifest_path = out_dir / "manifest.json"
                manifest_path.write_text(json.dumps({"decision": "pass"}), encoding="utf-8")
                v2182.OUT_DIR = out_dir

                v2182.normalize_manifest_axes()

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        finally:
            v2182.OUT_DIR = old_out_dir

        self.assertEqual(manifest["decision"], "pass")
        self.assertEqual(manifest["baseline_tag"], "v2182-hud-menu-cleanup")
        self.assertEqual(manifest["parent_baseline"], "v2178-wifi-profile-autoconnect")
        self.assertEqual(manifest["rollback_baseline"], "v2178-wifi-profile-autoconnect")
        self.assertEqual(manifest["version_axes"]["baseline_tag"], "v2182-hud-menu-cleanup")
        self.assertEqual(manifest["version_axes"]["parent_baseline"], "v2178-wifi-profile-autoconnect")
        self.assertEqual(manifest["version_axes"]["helper_version"], "helper-v427")
        self.assertEqual(manifest["version_axes"]["run_id"], "V2182")
        self.assertEqual(manifest["version_axes"]["promotion_run_id"], "V2183")
        self.assertIn("promoted boot/init baseline tag", manifest["version_axes"]["note"])


if __name__ == "__main__":
    unittest.main()
