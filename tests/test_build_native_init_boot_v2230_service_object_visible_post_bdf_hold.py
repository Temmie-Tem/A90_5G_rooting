"""Regression tests for build_native_init_boot_v2230_service_object_visible_post_bdf_hold."""

import json
import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_revalidation

v2230 = load_revalidation("build_native_init_boot_v2230_service_object_visible_post_bdf_hold")


def nested_namespace(*names, leaf):
    current = leaf
    for name in reversed(names):
        current = types.SimpleNamespace(**{name: current})
    return current


class BuildWrapperConfiguration(unittest.TestCase):
    def test_configure_base_rewrites_v2189_axes_and_long_hold_window(self):
        old_v2189 = v2230.v2189
        fake_base = types.SimpleNamespace(
            DEFAULT_ARGS=[
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
                "--wifi-test-helper-mode",
                "old-mode",
                "--wifi-test-watch-sec",
                "1",
                "--wifi-test-supervisor-timeout-sec",
                "2",
            ],
            base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]),
        )

        def set_arg(args, key, value):
            index = args.index(key)
            args[index + 1] = value

        v726 = types.SimpleNamespace(set_arg=set_arg)
        chain = nested_namespace("v2187", "v2182", "v2178", "v2176", "v2174", "v2169", "v726", leaf=v726)
        fake_v2189 = types.SimpleNamespace(
            base_module=lambda: fake_base,
            configure_base=lambda: setattr(fake_v2189, "configured", True),
            v2188=chain,
            EXTRA_INIT_FLAGS=["--flag"],
        )
        v2230.v2189 = fake_v2189
        try:
            v2230.configure_base()
        finally:
            v2230.v2189 = old_v2189

        args = dict(zip(fake_base.DEFAULT_ARGS[0::2], fake_base.DEFAULT_ARGS[1::2]))
        self.assertTrue(fake_v2189.configured)
        self.assertEqual(fake_v2189.OUT_DIR, v2230.OUT_DIR)
        self.assertEqual(fake_v2189.REPORT_PATH, v2230.REPORT_PATH)
        self.assertEqual(fake_v2189.REMOTE_PROPERTY_ROOT, v2230.REMOTE_PROPERTY_ROOT)
        self.assertEqual(args["--cycle"], "V2230")
        self.assertEqual(args["--decision"], "v2230-service-object-visible-post-bdf-hold-source-build-pass")
        self.assertEqual(args["--init-version"], "0.9.265")
        self.assertEqual(args["--init-build"], "v2230-service-object-visible-post-bdf-hold")
        self.assertEqual(args["--wifi-test-klog-prefix"], "A90v2230")
        self.assertEqual(args["--wifi-test-helper-mode"], "wlan-pd-service-object-visible-trigger")
        self.assertEqual(args["--wifi-test-watch-sec"], "155")
        self.assertEqual(args["--wifi-test-supervisor-timeout-sec"], "185")
        self.assertEqual(args["--wifi-test-property-root"], v2230.REMOTE_PROPERTY_ROOT)
        self.assertIn("a90_android_execns_probe_v429_service_object_visible_post_bdf_hold", args["--helper-binary"])
        self.assertEqual(fake_base.base.EXTRA_INIT_FLAGS, v2230.EXTRA_INIT_FLAGS)

    def test_render_report_includes_post_bdf_hold_route_and_safety_scope(self):
        manifest = {
            "decision": "v2230-service-object-visible-post-bdf-hold-source-build-pass",
            "base_boot": "workspace/private/inputs/boot_images/base.img",
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2230.img",
            "boot_sha256": "sha",
            "init_version": "0.9.265",
            "init_build": "v2230-service-object-visible-post-bdf-hold",
            "helper_marker": "a90_android_execns_probe v429",
            "helper_sha256": "helper-sha",
            "wifi_test": {
                "helper_mode": "wlan-pd-service-object-visible-trigger",
                "helper_runtime_mode": "wifi-companion-wlan-pd-service-object-visible-trigger-start-only",
                "helper_timeout_sec": 165,
                "supervisor_timeout_sec": 185,
                "watch_sec": 155,
                "helper_result": "/cache/result",
            },
        }

        report = v2230.render_report(manifest)

        self.assertIn("# Native Init V2230 Service-Object-Visible Post-BDF Hold Source Build", report)
        self.assertIn("Decision: `v2230-service-object-visible-post-bdf-hold-source-build-pass`", report)
        self.assertIn("post-BDF hold test boot", report)
        self.assertIn("Watch window: `155` seconds", report)
        self.assertIn("Supervisor timeout: `185`", report)
        self.assertIn("FW_READY/wlan0", report)
        self.assertIn("does not flash, reboot, scan/connect Wi-Fi", report)

    def test_normalize_manifest_axes_adds_v2230_version_metadata(self):
        old_out_dir = v2230.OUT_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out_dir = Path(tmp)
                manifest_path = out_dir / "manifest.json"
                manifest_path.write_text('{"decision": "pass"}', encoding="utf-8")
                v2230.OUT_DIR = out_dir

                v2230.normalize_manifest_axes()

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        finally:
            v2230.OUT_DIR = old_out_dir

        self.assertEqual(manifest["decision"], "pass")
        self.assertEqual(manifest["candidate_tag"], "v2230-service-object-visible-post-bdf-hold")
        self.assertEqual(manifest["parent_baseline"], "v2189-security-p0-stage-fix")
        self.assertEqual(manifest["rollback_baseline"], "v2189-security-p0-stage-fix")
        self.assertFalse(manifest["promoted_baseline"])
        self.assertEqual(manifest["version_axes"]["run_id"], "V2230")
        self.assertEqual(manifest["version_axes"]["helper_version"], "helper-v429")
        self.assertIn("long-hold service-object-visible observer test boot", manifest["version_axes"]["note"])
        self.assertIn("BDF/QMI progress but no wlan0", manifest["version_axes"]["note"])


if __name__ == "__main__":
    unittest.main()
