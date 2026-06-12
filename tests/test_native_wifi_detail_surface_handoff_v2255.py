"""Regression tests for native_wifi_detail_surface_handoff_v2255."""

import unittest
from pathlib import Path

from _loader import load_revalidation

v2255 = load_revalidation("native_wifi_detail_surface_handoff_v2255")


def result(stdout: str, *, ok: bool = True):
    return {"ok": ok, "stdout": stdout}


def status_text(*, forbidden=False, missing_field=None):
    lines = [
        "A90P1 BEGIN ignored=1",
        "decision=wifi-status-ok",
        "wlan0_present=1",
        "default_route_present=1",
        "gateway_label=192.168.0.1",
        "gateway_rc=0",
        "gateway_masked=1",
        "resolv_conf.present=1",
        "resolv_conf.nameserver_count=2",
        "secret_values_logged=0",
    ]
    if missing_field is not None:
        lines = [line for line in lines if not line.startswith(f"{missing_field}=")]
    if forbidden:
        lines.extend([
            "scan_result_count=3",
            "supplicant.command.0=CONNECT",
            "dhcp_ready=1",
            "internet.ping_rc=0",
        ])
    return "\n".join(lines) + "\n"


class StatusSurfaceParsing(unittest.TestCase):
    def test_parse_key_values_preserves_duplicates_and_ignores_protocol_lines(self):
        values = v2255.parse_key_values(
            "A90P1 BEGIN rc=0\n"
            " default_route_present=0 \n"
            "default_route_present=1\n"
            "no equals\n"
            "=bad\n"
        )

        self.assertEqual(values["default_route_present"], ["0", "1"])
        self.assertEqual(v2255.last_value(values, "default_route_present"), "1")
        self.assertEqual(v2255.last_value(values, "missing", "fallback"), "fallback")
        self.assertNotIn("rc", values)

    def test_sanitize_field_value_redacts_network_identifiers_only_when_present(self):
        self.assertEqual(v2255.sanitize_field_value("gateway_label", "192.168.0.1"), "<redacted-present>")
        self.assertEqual(v2255.sanitize_field_value("gateway_label", "-"), "-")
        self.assertEqual(v2255.sanitize_field_value("mac", "00:11:22:33:44:55"), "<redacted-present>")
        self.assertEqual(v2255.sanitize_field_value("default_route_present", "1"), "1")

    def test_classify_wifi_status_requires_v2254_fields_and_redacts_gateway(self):
        classification = v2255.classify_wifi_status(result(status_text()))

        self.assertTrue(classification["ok"])
        self.assertTrue(classification["all_required_fields_present"])
        self.assertTrue(classification["no_forbidden_runtime_actions"])
        self.assertEqual(classification["decision"], "wifi-status-ok")
        self.assertEqual(classification["wlan0_present"], "1")
        self.assertEqual(classification["default_route_present"], "1")
        self.assertEqual(classification["gateway_masked"], "1")
        self.assertEqual(classification["nameserver_count"], "2")
        self.assertEqual(classification["secret_values_logged"], "0")
        self.assertEqual(classification["sanitized_values"]["gateway_label"], "<redacted-present>")

    def test_classify_wifi_status_detects_missing_fields_and_forbidden_actions(self):
        missing = v2255.classify_wifi_status(result(status_text(missing_field="gateway_rc")))
        forbidden = v2255.classify_wifi_status(result(status_text(forbidden=True)))

        self.assertFalse(missing["all_required_fields_present"])
        self.assertFalse(missing["field_present"]["gateway_rc"])
        self.assertFalse(forbidden["no_forbidden_runtime_actions"])
        self.assertEqual(
            forbidden["forbidden_runtime_actions_detected"],
            {"scan": True, "connect": True, "dhcp": True, "ping": True},
        )

    def test_classify_screenapp_accepts_title_or_rendered_text(self):
        titled = v2255.classify_screenapp(result("screenapp.title=wifi-status\nscreenapp.rc=0\nscreenapp.presented=1\n"))
        rendered = v2255.classify_screenapp(result("WIFI STATUS\nscreenapp.presented=0\n", ok=False))

        self.assertTrue(titled["ok"])
        self.assertEqual(titled["screenapp_title"], "wifi-status")
        self.assertEqual(titled["screenapp_presented"], "1")
        self.assertTrue(titled["mentions_wifi_status"])
        self.assertFalse(rendered["ok"])
        self.assertTrue(rendered["mentions_wifi_status"])


class CommandAndHealthHelpers(unittest.TestCase):
    def test_flash_command_includes_version_sha_selftest_and_optional_from_native(self):
        image = Path("workspace/private/inputs/boot_images/test.img")

        native = v2255.flash_command(image, "expected version", "abc123", from_native=True)
        recovery = v2255.flash_command(image, "expected version", "abc123", from_native=False)

        self.assertEqual(native[:2], ["python3", "workspace/public/src/scripts/revalidation/native_init_flash.py"])
        self.assertIn(image, native)
        self.assertEqual(native[native.index("--expect-version") + 1], "expected version")
        self.assertEqual(native[native.index("--expect-sha256") + 1], "abc123")
        self.assertEqual(native[native.index("--verify-protocol") + 1], "selftest")
        self.assertIn("--from-native", native)
        self.assertNotIn("--from-native", recovery)

    def test_dry_run_commands_cover_verify_flash_observe_rollback_and_postflight(self):
        plan = v2255.dry_run_commands({
            "test_image_sha256": "test-sha",
            "rollback_image_sha256": "rollback-sha",
        })

        self.assertIn("--verify-only", plan["current_verify"])
        self.assertIn("test-sha", plan["flash_test_boot"])
        self.assertEqual(plan["test_observations"], [["cmdv1", "wifi", "status"], ["cmdv1", "screenapp", "wifi-status"]])
        self.assertIn("rollback-sha", plan["rollback"])
        self.assertEqual(plan["post_rollback"], [["cmdv1", "version"], ["cmdv1", "status"], ["cmdv1", "selftest"]])

    def test_classify_test_health_allows_status_version_fallback(self):
        health = v2255.classify_test_health(
            result("wrong version"),
            result(f"status\nversion={v2255.TEST_EXPECT_VERSION}\n"),
            result("selftest\nfail=0\n"),
        )
        failed = v2255.classify_test_health(result("wrong"), result("status"), result("fail=1"))

        self.assertTrue(health["version_ok"])
        self.assertEqual(health["version_ok_source"], "status_fallback")
        self.assertTrue(health["status_ok"])
        self.assertTrue(health["selftest_ok"])
        self.assertFalse(failed["version_ok"])
        self.assertFalse(failed["selftest_ok"])


class ManifestClassification(unittest.TestCase):
    def test_classify_manifest_covers_dry_run_ready_and_blocked(self):
        ready = v2255.classify_manifest({
            "execute": False,
            "preflight": {
                "build_manifest_exists": True,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": True,
                "rollback_image_exists": True,
                "fallback_image_exists": True,
            },
        })
        blocked = v2255.classify_manifest({
            "execute": False,
            "preflight": {
                "build_manifest_exists": True,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": False,
                "rollback_image_exists": True,
                "fallback_image_exists": True,
            },
        })

        self.assertEqual(ready["decision"], "v2255-wifi-detail-surface-dry-run-ready")
        self.assertTrue(ready["pass"])
        self.assertEqual(blocked["decision"], "v2255-wifi-detail-surface-dry-run-blocked")
        self.assertFalse(blocked["pass"])

    def test_classify_manifest_covers_live_failure_and_success_branches(self):
        good_health = {"version_ok": True, "status_ok": True, "selftest_ok": True}
        good_status = {"all_required_fields_present": True, "no_forbidden_runtime_actions": True}
        good_screen = {"ok": True, "screenapp_presented": "1"}
        cases = [
            (
                {"execute": True, "rollback": {"selftest_ok": False}},
                "v2255-wifi-detail-surface-rollback-selftest-failed",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "live_block": "preflight-current-baseline-failed"},
                "v2255-wifi-detail-surface-preflight-failed-no-flash",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "live_block": "test-flash-failed"},
                "v2255-wifi-detail-surface-test-flash-failed-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "test_health": {"version_ok": True, "status_ok": False, "selftest_ok": True}},
                "v2255-wifi-detail-surface-test-health-failed-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "test_health": good_health, "observations": {"wifi_status": {"all_required_fields_present": False}}},
                "v2255-wifi-detail-surface-missing-status-fields-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "test_health": good_health, "observations": {"wifi_status": {"all_required_fields_present": True, "no_forbidden_runtime_actions": False}}},
                "v2255-wifi-detail-surface-forbidden-action-detected-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "test_health": good_health, "observations": {"wifi_status": good_status, "screenapp_wifi_status": {"ok": True, "screenapp_presented": "0"}}},
                "v2255-wifi-detail-surface-screenapp-not-presented-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "test_health": good_health, "observations": {"wifi_status": good_status, "screenapp_wifi_status": good_screen}},
                "v2255-wifi-detail-surface-live-pass",
                True,
            ),
        ]

        for manifest, decision, passed in cases:
            with self.subTest(decision=decision):
                classified = v2255.classify_manifest(manifest)
                self.assertEqual(classified["decision"], decision)
                self.assertEqual(classified["pass"], passed)


class ReportAndResidualState(unittest.TestCase):
    def manifest(self, *, execute=False, observations=None, **overrides):
        field_present = {field: True for field in v2255.REQUIRED_STATUS_FIELDS}
        sanitized = {field: "1" for field in v2255.REQUIRED_STATUS_FIELDS}
        sanitized["gateway_label"] = "<redacted-present>"
        manifest = {
            "result": {"decision": "v2255-wifi-detail-surface-dry-run-ready", "pass": True, "reason": "ready"},
            "execute": execute,
            "out_dir": "workspace/private/runs/wifi/unit",
            "phase_timer_contract": "phase-timer-v1",
            "residual_state_contract": "residual-state-v1",
            "preflight": {
                "test_image": "workspace/private/inputs/boot_images/test.img",
                "test_image_sha256": "test-sha",
                "test_expect_version": v2255.TEST_EXPECT_VERSION,
                "rollback_image": "workspace/private/inputs/boot_images/rollback.img",
                "rollback_image_sha256": "rollback-sha",
                "rollback_expect_version": v2255.ROLLBACK_EXPECT_VERSION,
                "fallback_image_exists": True,
            },
            "current_preflight": {"verify_ok": True, "selftest_ok": True},
            "test_flash": {"ok": True},
            "test_health": {"version_ok": True, "status_ok": True, "selftest_ok": True, "version_ok_source": "version"},
            "rollback": {"ok": True, "attempt": "from-native", "version_ok": True, "status_ok": True, "selftest_ok": True},
            "observations": observations or {
                "wifi_status": {
                    "ok": True,
                    "all_required_fields_present": True,
                    "field_present": field_present,
                    "sanitized_values": sanitized,
                    "secret_values_logged": "0",
                    "gateway_masked": "1",
                    "forbidden_runtime_actions_detected": {"scan": False, "connect": False, "dhcp": False, "ping": False},
                },
                "screenapp_wifi_status": {"ok": True, "screenapp_presented": "1"},
            },
        }
        manifest.update(overrides)
        return manifest

    def test_residual_state_marks_dry_run_no_touch_and_failed_rollback_cleanup(self):
        dry = v2255.residual_state({"execute": False})
        failed = v2255.residual_state({
            "execute": True,
            "test_flash": {"ok": True},
            "rollback": {"ok": False, "selftest_ok": False, "attempt": "from-recovery"},
            "observations": {
                "wifi_status": {
                    "all_required_fields_present": True,
                    "forbidden_runtime_actions_detected": {"scan": False},
                },
                "screenapp_wifi_status": {"screenapp_presented": "1"},
            },
        })

        self.assertFalse(dry["device_touched"])
        self.assertEqual(dry["rollback_attempt"], "not-needed-dry-run")
        self.assertFalse(dry["wifi_scan_connect"])
        self.assertTrue(failed["device_touched"])
        self.assertTrue(failed["cleanup_required"])
        self.assertEqual(failed["residual_risk"], "rollback-health-incomplete")

    def test_render_report_dry_run_includes_plan_and_safety_scope(self):
        report = v2255.render_report(self.manifest(dry_run_commands={"test_observations": [["cmdv1", "wifi", "status"]]}))

        self.assertIn("# Native Init V2255 Wi-Fi Detail Surface Live", report)
        self.assertIn("Decision: `v2255-wifi-detail-surface-dry-run-ready`", report)
        self.assertIn("Dry-Run Plan", report)
        self.assertIn("wifi status", report)
        self.assertIn("Flash path is limited to boot partition", report)

    def test_render_report_live_redacts_status_values_and_records_forbidden_scope(self):
        live = self.manifest(execute=True)
        live["result"] = {
            "decision": "v2255-wifi-detail-surface-live-pass",
            "pass": True,
            "reason": "live pass",
        }

        report = v2255.render_report(live)

        self.assertIn("Status Field Classification", report)
        self.assertIn("`gateway_label`: present=`True` value=`<redacted-present>`", report)
        self.assertIn("secret_values_logged: `0`", report)
        self.assertIn("forbidden scan/connect/DHCP/ping markers", report)
        self.assertNotIn("192.168.0.1", report)


if __name__ == "__main__":
    unittest.main()
