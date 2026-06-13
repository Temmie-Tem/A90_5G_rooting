from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_revalidation


rescan = load_revalidation("local_security_rescan.py")


class PureScanHelpers(unittest.TestCase):
    def test_status_pass_fail_local_pass_and_residual_state_counts(self) -> None:
        checks = [
            rescan.Check("S001", "good", "PASS", "ok", "note"),
            rescan.Check("S002", "warn", "WARN", "lab boundary", "note"),
            rescan.Check("S003", "bad", "FAIL", "missing guard", "note"),
        ]

        self.assertEqual(rescan.status_from(True), "PASS")
        self.assertEqual(rescan.status_from(False), "FAIL")
        self.assertFalse(rescan.local_scan_pass(checks))

        state = rescan.residual_state(checks)

        self.assertFalse(state["device_touched"])
        self.assertFalse(state["flash_reboot"])
        self.assertFalse(state["partition_write"])
        self.assertFalse(state["credentials_used"])
        self.assertFalse(state["dhcp_routes_ping"])
        self.assertEqual(state["local_security_fail_count"], 1)
        self.assertEqual(state["local_security_warn_count"], 1)
        self.assertFalse(state["selftest_ok"])
        self.assertEqual(state["residual_risk"], "local-security-failures")

        clean_state = rescan.residual_state([checks[0], checks[1]])
        self.assertTrue(clean_state["selftest_ok"])
        self.assertEqual(clean_state["residual_risk"], "none")

    def test_render_metadata_redacts_to_phase_and_residual_contracts(self) -> None:
        rendered = rescan.render_run_metadata({
            "phase_timer_contract": "phase-v1",
            "phase_timers": [{"name": "scan", "ok": True}],
            "residual_state_contract": "residual-v1",
            "residual_state": {"device_touched": False},
            "private_internal": "must-not-render",
        })

        payload = json.loads(rendered)

        self.assertEqual(payload["phase_timer_contract"], "phase-v1")
        self.assertEqual(payload["phase_timers"], [{"name": "scan", "ok": True}])
        self.assertEqual(payload["residual_state_contract"], "residual-v1")
        self.assertEqual(payload["residual_state"], {"device_touched": False})
        self.assertNotIn("private_internal", payload)

    def test_render_report_counts_warns_failures_and_metadata(self) -> None:
        checks = [
            rescan.Check("S001", "bound", "PASS", "`a90_config.h` ok", "safe"),
            rescan.Check("S002", "boundary", "WARN", "trusted lab", "accepted"),
            rescan.Check("S003", "identity", "FAIL", "missing SHA", "blocker"),
        ]
        metadata = {
            "phase_timer_contract": "phase-v1",
            "phase_timers": [{"name": "host_security_scan", "ok": True}],
            "residual_state_contract": "residual-v1",
            "residual_state": {"local_security_fail_count": 1},
        }

        with mock.patch.object(rescan, "git_head", return_value="abc1234"):
            report = rescan.render_report(
                checks,
                baseline="baseline-x",
                title="Unit Local Security Rescan",
                metadata=metadata,
            )

        self.assertIn("# Unit Local Security Rescan", report)
        self.assertIn("Baseline: `baseline-x`", report)
        self.assertIn("Git HEAD: `abc1234`", report)
        self.assertIn("- PASS: 1", report)
        self.assertIn("- WARN: 1", report)
        self.assertIn("- FAIL: 1", report)
        self.assertIn("New implementation blocker from this local scan: `1`", report)
        self.assertIn("| S003 | FAIL | identity | missing SHA | blocker |", report)
        self.assertIn("Do not promote this baseline", report)
        self.assertIn('"residual_state_contract": "residual-v1"', report)


class RepositoryScopedHelpers(unittest.TestCase):
    def test_read_has_none_and_boot_sha_helpers_use_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_root = root / rescan.SCRIPT_ROOT
            script_root.mkdir(parents=True)
            (script_root / "native_wifi_connect_carrier_handoff_v2174.py").write_text(
                '"boot_linux_v2189_security_p0_stage_fix.img": '
                '"f54becb2b720ad198413c2a0089912626ca295c79a96f13e0921cf4f05b39f51"\n',
                encoding="utf-8",
            )
            safe = root / "safe.c"
            unsafe = root / "unsafe.c"
            safe.write_text('bind_addr = "192.168.7.2";\n', encoding="utf-8")
            unsafe.write_text("INADDR_ANY\n", encoding="utf-8")

            with mock.patch.object(rescan, "REPO_ROOT", root):
                self.assertEqual(rescan.read_rel("safe.c"), 'bind_addr = "192.168.7.2";\n')
                self.assertTrue(rescan.exists_rel("safe.c"))
                self.assertTrue(rescan.has_all("safe.c", ['"192.168.7.2"']))
                self.assertTrue(rescan.has_none(["safe.c"], r"INADDR_ANY|0\.0\.0\.0"))
                self.assertFalse(rescan.has_none(["safe.c", "unsafe.c"], r"INADDR_ANY|0\.0\.0\.0"))
                self.assertTrue(rescan.active_boot_sha_map_has_v2189())

    def test_builder_wifi_test_boot_detector_flags_active_defines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_root = root / rescan.SCRIPT_ROOT
            script_root.mkdir(parents=True)
            active = script_root / "build_native_init_boot_v9999.py"
            active.write_text("EXTRA_CFLAGS='-O2'\n", encoding="utf-8")

            with mock.patch.object(rescan, "REPO_ROOT", root):
                self.assertTrue(rescan.builders_do_not_define_wifi_test_boot())
                active.write_text("EXTRA_CFLAGS='-DA90_WIFI_TEST_BOOT'\n", encoding="utf-8")
                self.assertFalse(rescan.builders_do_not_define_wifi_test_boot())


class MainFlow(unittest.TestCase):
    def test_main_writes_report_with_phase_timers_and_returns_failure_count(self) -> None:
        checks = [
            rescan.Check("S001", "ok", "PASS", "present", "note"),
            rescan.Check("S002", "boundary", "WARN", "accepted", "note"),
            rescan.Check("S003", "missing", "FAIL", "not found", "note"),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "scan.md"
            args = SimpleNamespace(out=out, baseline="unit-baseline", title="Unit Scan")

            with (
                mock.patch.object(rescan, "parse_args", return_value=args),
                mock.patch.object(rescan, "run_checks", return_value=checks),
                mock.patch.object(rescan, "git_head", return_value="feed123"),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                rc = rescan.main()

            report = out.read_text(encoding="utf-8")

        self.assertEqual(rc, 1)
        self.assertIn(str(out), stdout.getvalue())
        self.assertIn("Baseline: `unit-baseline`", report)
        self.assertIn("- FAIL: 1", report)
        self.assertIn("## Run Metadata", report)
        self.assertIn("host_security_scan", report)
        self.assertIn("render_report", report)
        self.assertIn("artifact_write", report)
        self.assertIn("local_security_rescan_total", report)
        self.assertIn('"local_security_scan_pass": false', report)


if __name__ == "__main__":
    unittest.main()
