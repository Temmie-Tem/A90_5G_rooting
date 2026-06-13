"""Regression tests for build_native_init_boot_v2188_security_p0_hardening."""

from __future__ import annotations

import json
import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_revalidation


v2188 = load_revalidation("build_native_init_boot_v2188_security_p0_hardening")


def nested_namespace(*names, leaf):
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


class BuildWrapperConfiguration(unittest.TestCase):
    def test_configure_base_rewrites_v2187_axes_for_security_hardening_candidate(self) -> None:
        old_v2187 = v2188.v2187
        fake_base = types.SimpleNamespace(
            DEFAULT_ARGS=fake_base_args(),
            base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]),
        )

        def set_arg(args, key, value):
            index = args.index(key)
            args[index + 1] = value

        v726 = types.SimpleNamespace(set_arg=set_arg)
        chain = nested_namespace("v2178", "v2176", "v2174", "v2169", "v726", leaf=v726)
        fake_v2187 = types.SimpleNamespace(
            base_module=lambda: fake_base,
            configure_base=lambda: setattr(fake_v2187, "configured", True),
            EXTRA_INIT_FLAGS=("-DIGNORED-BY-WRAPPER=1",),
            REMOTE_PROPERTY_ROOT="/fake/property/root",
            EXPECTED_HELPER_MARKER="fake-marker",
            EXPECTED_HELPER_SHA256="fake-sha",
            v2182=chain,
        )
        v2188.v2187 = fake_v2187
        try:
            v2188.configure_base()
        finally:
            v2188.v2187 = old_v2187

        args = dict(zip(fake_base.DEFAULT_ARGS[0::2], fake_base.DEFAULT_ARGS[1::2]))
        self.assertTrue(fake_v2187.configured)
        self.assertEqual(fake_v2187.OUT_DIR, v2188.OUT_DIR)
        self.assertEqual(fake_v2187.REPORT_PATH, v2188.REPORT_PATH)
        self.assertEqual(fake_v2187.BOOT_IMAGE, v2188.BOOT_IMAGE)
        self.assertEqual(fake_v2187.INIT_BINARY, v2188.INIT_BINARY)
        self.assertEqual(fake_v2187.RAMDISK_CPIO, v2188.RAMDISK_CPIO)
        self.assertEqual(args["--cycle"], "V2188")
        self.assertEqual(args["--decision"], "v2188-security-p0-hardening-source-build-pass")
        self.assertEqual(args["--cycle-label"], "v2188")
        self.assertEqual(args["--init-version"], "0.9.260")
        self.assertEqual(args["--init-build"], "v2188-security-p0-hardening")
        self.assertEqual(args["--wifi-test-klog-prefix"], "A90v2188")
        self.assertEqual(args["--wifi-test-disable"], "/cache/native-init-wifi-test-boot-v2188.disable")
        self.assertEqual(args["--wifi-test-log"], "/cache/native-init-wifi-test-boot-v2188.log")
        self.assertEqual(
            args["--wifi-test-helper-result"],
            "/cache/native-init-wifi-test-boot-v2188-helper.result",
        )
        self.assertEqual(args["--wifi-test-property-root"], v2188.REMOTE_PROPERTY_ROOT)
        self.assertIn("a90_android_execns_probe_v427_security_p0_hardening", args["--helper-binary"])
        self.assertEqual(fake_base.base.EXTRA_INIT_FLAGS, v2188.EXTRA_INIT_FLAGS)

    def test_render_report_records_p0_hardening_without_runtime_wifi_actions(self) -> None:
        manifest = {
            "decision": "v2188-security-p0-hardening-source-build-pass",
            "base_boot": "workspace/private/inputs/boot_images/base.img",
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2188.img",
            "boot_sha256": "boot-sha",
            "init_version": "0.9.260",
            "init_build": "v2188-security-p0-hardening",
            "helper_marker": "a90_android_execns_probe v427",
            "helper_sha256": "helper-sha",
            "wifi_test": {
                "helper_runtime_mode": "wifi-companion",
                "helper_timeout_sec": 75,
            },
        }

        report = v2188.render_report(manifest)

        self.assertIn("# Native Init V2188 Security P0 Hardening Source Build", report)
        self.assertIn("Decision: `v2188-security-p0-hardening-source-build-pass`", report)
        self.assertIn("root-executed Wi-Fi artifacts are checked", report)
        self.assertIn("caller-pinned boot image SHA256", report)
        self.assertIn("does not initiate Wi-Fi connect, DHCP, route/DNS changes, or ping", report)
        self.assertIn("native_init_flash.py --expect-sha256", report)
        self.assertIn("No `/dev/subsys_esoc0`", report)

    def test_normalize_manifest_axes_keeps_v2188_as_unpromoted_test_candidate(self) -> None:
        old_out_dir = v2188.OUT_DIR
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                out_dir = Path(temp_dir)
                manifest_path = out_dir / "manifest.json"
                manifest_path.write_text(json.dumps({"decision": "pass"}), encoding="utf-8")
                v2188.OUT_DIR = out_dir

                v2188.normalize_manifest_axes()

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        finally:
            v2188.OUT_DIR = old_out_dir

        self.assertEqual(manifest["decision"], "pass")
        self.assertEqual(manifest["candidate_tag"], "v2188-security-p0-hardening")
        self.assertEqual(manifest["parent_baseline"], "v2187-screenapp-ui-validation")
        self.assertEqual(manifest["rollback_baseline"], "v2187-screenapp-ui-validation")
        self.assertFalse(manifest["promoted_baseline"])
        self.assertEqual(manifest["version_axes"]["run_id"], "V2188")
        self.assertEqual(manifest["version_axes"]["helper_version"], "helper-v427")
        self.assertIn("security P0 hardening test-boot candidate", manifest["version_axes"]["note"])


if __name__ == "__main__":
    unittest.main()
