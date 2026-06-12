"""Regression tests for native_kernel_a90_boot_window_handoff_v2225."""

import argparse
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2225 = load_revalidation("native_kernel_a90_boot_window_handoff_v2225")


class CommandAndPreflightHelpers(unittest.TestCase):
    def test_sha256_and_load_build_manifest_with_missing_file(self):
        old_manifest = v2225.V2224_MANIFEST
        try:
            with tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp) / "data.bin"
                data.write_bytes(b"v2225")
                v2225.V2224_MANIFEST = Path(tmp) / "missing.json"

                self.assertEqual(
                    v2225.sha256(data),
                    "d6b6cc519564d0f401fabab7fb7f8f43a86459a5918582422f9b9d80dcc3f2be",
                )
                self.assertEqual(v2225.load_build_manifest(), {})
        finally:
            v2225.V2224_MANIFEST = old_manifest

    def test_a90ctl_command_includes_hide_on_busy_and_allow_error(self):
        args = argparse.Namespace(bridge_host="127.0.0.1", bridge_port=54321, timeout=17.0)

        command = v2225.a90ctl_command(args, ["cat", "/cache/result"], allow_error=True)

        self.assertEqual(command[:2], ["python3", "workspace/public/src/scripts/revalidation/a90ctl.py"])
        self.assertIn("--hide-on-busy", command)
        self.assertIn("--allow-error", command)
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "54321")
        self.assertEqual(command[command.index("--timeout") + 1], "17.0")
        self.assertEqual(command[-2:], ["cat", "/cache/result"])

    def test_flash_command_adds_expected_safety_arguments(self):
        image = Path("workspace/private/inputs/boot_images/test.img")

        native = v2225.flash_command(image, "expected version", "abc123", from_native=True)
        recovery = v2225.flash_command(image, "expected version", "abc123", from_native=False)

        self.assertEqual(native[:2], ["python3", "workspace/public/src/scripts/revalidation/native_init_flash.py"])
        self.assertIn(image, native)
        self.assertIn("--expect-version", native)
        self.assertEqual(native[native.index("--expect-version") + 1], "expected version")
        self.assertEqual(native[native.index("--expect-sha256") + 1], "abc123")
        self.assertEqual(native[native.index("--verify-protocol") + 1], "selftest")
        self.assertIn("--from-native", native)
        self.assertNotIn("--from-native", recovery)

    def test_dry_run_commands_render_flash_collect_parse_and_rollback_steps(self):
        plan = v2225.dry_run_commands({
            "test_image_sha256": "test-sha",
            "rollback_image_sha256": "rollback-sha",
        })

        self.assertIn("preflight", plan)
        self.assertIn("flash_test_boot", plan)
        self.assertIn("collect", plan)
        self.assertIn("parse", plan)
        self.assertIn("rollback", plan)
        self.assertIn("postflight", plan)
        self.assertEqual(len(plan["collect"]), len(v2225.HELPER_REMOTE_PATHS))
        self.assertIn("test-sha", plan["flash_test_boot"])
        self.assertIn("rollback-sha", plan["rollback"])


class ArtifactDiagnosisAndClassification(unittest.TestCase):
    def write_artifact(self, text: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        with tmp:
            tmp.write(text)
        return Path(tmp.name)

    def test_diagnose_artifacts_classifies_property_root_missing(self):
        path = self.write_artifact(
            "helper_status=setup-error\n"
            "setup_error=lstat property root: No such file or directory\n"
            "helper_exit_code=20\n"
        )
        try:
            diagnosis = v2225.diagnose_artifacts([path])
        finally:
            path.unlink()

        self.assertEqual(diagnosis["kind"], "property-root-missing")
        self.assertEqual(diagnosis["decision"], "helper-setup-error-property-root-missing")
        self.assertEqual(diagnosis["helper_exit_code"], 20)

    def test_diagnose_artifacts_classifies_setup_error_present_and_unknown(self):
        setup = self.write_artifact("helper_status=setup-error\nchild_exit_code=20\n")
        present = self.write_artifact("A90_EXECNS_RESULT_FILE_BEGIN\nhelper_result_size=12\n")
        unknown = self.write_artifact("ordinary log\n")
        try:
            self.assertEqual(v2225.diagnose_artifacts([setup])["kind"], "setup-error")
            self.assertEqual(v2225.diagnose_artifacts([present])["kind"], "helper-artifacts-present")
            self.assertEqual(v2225.diagnose_artifacts([unknown])["kind"], "unknown")
        finally:
            setup.unlink()
            present.unlink()
            unknown.unlink()

    def test_classify_dry_run_ready_and_blocked(self):
        ready = v2225.classify({
            "execute": False,
            "preflight": {
                "v2224_manifest_pass": True,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": True,
                "rollback_image_exists": True,
            },
        })
        blocked = v2225.classify({
            "execute": False,
            "preflight": {
                "v2224_manifest_pass": False,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": True,
                "rollback_image_exists": True,
            },
        })

        self.assertEqual(ready["decision"], "v2225-boot-window-handoff-dry-run-ready")
        self.assertTrue(ready["pass"])
        self.assertEqual(blocked["decision"], "v2225-boot-window-handoff-dry-run-blocked")
        self.assertFalse(blocked["pass"])

    def test_classify_live_branches(self):
        cases = [
            (
                {"execute": True, "live_block": "v2222-preflight-failed"},
                "v2225-boot-window-handoff-preflight-failed-no-flash",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": False}},
                "v2225-boot-window-handoff-rollback-selftest-failed",
                False,
            ),
            (
                {"execute": True, "live_block": "test-flash-failed", "rollback": {"ok": True, "selftest_ok": True}},
                "v2225-boot-window-handoff-test-flash-failed-rollback-pass",
                False,
            ),
            (
                {
                    "execute": True,
                    "rollback": {"ok": True, "selftest_ok": True},
                    "collect": {"diagnosis": {"kind": "property-root-missing"}},
                },
                "v2225-boot-window-helper-property-root-missing-rollback-pass",
                False,
            ),
            (
                {
                    "execute": True,
                    "rollback": {"ok": True, "selftest_ok": True},
                    "collect": {"parser": {"parsed_pass": True}},
                },
                "v2225-boot-window-helper-parsed-rollback-pass",
                True,
            ),
            (
                {
                    "execute": True,
                    "rollback": {"ok": True, "selftest_ok": True},
                    "collect": {"parser": {"parsed_pass": False}},
                },
                "v2225-boot-window-helper-parse-incomplete-rollback-pass",
                False,
            ),
        ]

        for manifest, decision, passed in cases:
            with self.subTest(decision=decision):
                result = v2225.classify(manifest)
                self.assertEqual(result["decision"], decision)
                self.assertEqual(result["pass"], passed)


class ReportAndResidualState(unittest.TestCase):
    def manifest(self, **overrides):
        manifest = {
            "result": {"decision": "v2225-boot-window-handoff-dry-run-ready", "pass": True, "reason": "ready"},
            "preflight": {
                "test_image": "workspace/private/inputs/boot_images/test.img",
                "test_image_sha256": "test-sha",
                "test_expect_version": v2225.TEST_EXPECT_VERSION,
                "rollback_image": "workspace/private/inputs/boot_images/rollback.img",
                "rollback_image_sha256": "rollback-sha",
                "rollback_expect_version": v2225.ROLLBACK_EXPECT_VERSION,
            },
            "execute": False,
            "out_dir": "workspace/private/runs/kernel/v2225",
            "steps": [],
        }
        manifest.update(overrides)
        return manifest

    def test_render_report_includes_dry_run_plan_and_safety_scope(self):
        manifest = self.manifest(dry_run_commands={"postflight": ["python3", "a90ctl.py", "selftest"]})

        report = v2225.render_report(manifest)

        self.assertIn("# Native Init V2225 A90 Boot-Window Handoff Runner", report)
        self.assertIn("Decision: `v2225-boot-window-handoff-dry-run-ready`", report)
        self.assertIn("Live mode requires `--execute` plus the exact confirmation token", report)
        self.assertIn("Dry-Run Command Plan", report)
        self.assertIn("does not flash, reboot, write device partitions", report)

    def test_render_report_includes_property_root_live_diagnosis(self):
        manifest = self.manifest(
            execute=True,
            result={
                "decision": "v2225-boot-window-helper-property-root-missing-rollback-pass",
                "pass": False,
                "reason": "missing",
            },
            rollback={"ok": True, "selftest_ok": True},
            collect={
                "parser": {"parsed_decision": "nohit", "parsed_pass": False},
                "diagnosis": {"kind": "property-root-missing", "decision": "helper-setup-error-property-root-missing"},
            },
        )

        report = v2225.render_report(manifest)

        self.assertIn("Live Evidence", report)
        self.assertIn("Live Diagnosis", report)
        self.assertIn("property root was missing", report)
        self.assertIn("Next unit: rebuild with a present/staged property root", report)

    def test_residual_state_tracks_flash_rollback_and_cleanup(self):
        dry = v2225.residual_state(self.manifest())
        ok = v2225.residual_state(self.manifest(
            execute=True,
            steps=[{"name": "flash-v2224-from-native", "ok": True}],
            rollback={"ok": True, "selftest_ok": True, "attempt": "from-native"},
        ))
        bad = v2225.residual_state(self.manifest(
            execute=True,
            steps=[{"name": "flash-v2224-from-native", "ok": True}],
            rollback={"ok": False, "selftest_ok": False, "attempt": "from-recovery"},
        ))

        self.assertFalse(dry["device_touched"])
        self.assertFalse(dry["flash_reboot"])
        self.assertTrue(dry["rollback_ok"])
        self.assertTrue(ok["device_touched"])
        self.assertTrue(ok["flash_reboot"])
        self.assertTrue(ok["test_flash_ok"])
        self.assertTrue(ok["rollback_ok"])
        self.assertEqual(ok["rollback_attempt"], "from-native")
        self.assertFalse(ok["cleanup_required"])
        self.assertTrue(bad["cleanup_required"])
        self.assertEqual(bad["residual_risk"], "rollback-or-selftest-incomplete")
        self.assertTrue(bad["partition_write"])
        self.assertFalse(bad["wifi_scan_connect"])
        self.assertFalse(bad["probe_write_user_executed"])


if __name__ == "__main__":
    unittest.main()
