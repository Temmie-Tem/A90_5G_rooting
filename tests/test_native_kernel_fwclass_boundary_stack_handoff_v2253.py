"""Regression tests for native_kernel_fwclass_boundary_stack_handoff_v2253."""

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2253 = load_revalidation("native_kernel_fwclass_boundary_stack_handoff_v2253")


def kv_lines(request_index=0, *, before_symbols=None, after_symbols=None, include_boundary=True):
    before_symbols = before_symbols or []
    after_symbols = after_symbols or []
    lines = [
        "A90P1 END rc=0 ignored=1",
        "helper_exit_code=1",
        "helper_exit_code=0",
        "helper_timed_out=0",
        "supervisor_result=wlan0-ready",
        "wlan0_present=1",
        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.seen_count=1",
        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.fed_count=1",
        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.timed_out=1",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.label=req{request_index}",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.firmware={v2253.REQUESTS[request_index]}",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.seen=1",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.fed=1",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.source_bytes=13343",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.data_rc=0",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.loading_done_rc=0",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.final_seen=1",
        f"qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_{request_index}.final_fed=1",
    ]
    if include_boundary:
        for point, symbols in (("before_feed", before_symbols), ("after_feed", after_symbols)):
            boundary_prefix = (
                "qcacld_fwclass_boundary_stack_sampler.after_boot_wlan_trigger."
                f"request_{request_index}.{point}"
            )
            phase = f"fwclass_req{request_index}_{point}"
            lines.extend([
                f"{boundary_prefix}.begin=1",
                f"{boundary_prefix}.end=1",
                f"{boundary_prefix}.label=req{request_index}-{point}",
                f"{boundary_prefix}.firmware={v2253.REQUESTS[request_index]}",
                f"icnss_register_probe_stack_sampler.{phase}.begin=1",
                f"icnss_register_probe_stack_sampler.{phase}.end=1",
                f"icnss_register_probe_stack_sampler.{phase}.scanned=7",
                f"icnss_register_probe_stack_sampler.{phase}.target_hits={1 if symbols else 0}",
                f"icnss_register_probe_stack_sampler.{phase}.samples=5",
                f"icnss_register_probe_stack_sampler.{phase}.stack_open_ok=5",
                f"icnss_register_probe_stack_sampler.{phase}.stack_open_fail=0",
                f"icnss_register_probe_stack_sampler.{phase}.sample_0.target={1 if symbols else 0}",
                f"icnss_register_probe_stack_sampler.{phase}.sample_0.comm=kworker/u16:1",
                f"icnss_register_probe_stack_sampler.{phase}.sample_0.wchan=worker_thread",
            ])
            lines.extend(
                f"icnss_register_probe_stack_sampler.{phase}.sample_0.stack_{index}="
                f"[<0xffffff800810{index:04x}>] {symbol}+0x10/0x80"
                for index, symbol in enumerate(symbols)
            )
    return lines


def write_artifacts(root: Path, lines):
    root.mkdir(parents=True, exist_ok=True)
    helper = root / "helper_result.cmdv1.txt"
    summary = root / "summary.cmdv1.txt"
    log = root / "log.cmdv1.txt"
    helper.write_text("\n".join(lines[: len(lines) // 2]) + "\n", encoding="utf-8")
    summary.write_text("\n".join(lines[len(lines) // 2:]) + "\n", encoding="utf-8")
    log.write_text("ordinary log\n", encoding="utf-8")
    return {"helper_result": helper, "summary": summary, "log": log}


class KeyValueAndPhaseParsing(unittest.TestCase):
    def test_parse_key_values_preserves_multiple_values_and_ignores_protocol_lines(self):
        values = v2253.parse_key_values(
            "A90P1 BEGIN ignored=1\n"
            " helper_exit_code=20 \n"
            "helper_exit_code=0\n"
            "no equals\n"
            "=bad\n"
        )

        self.assertEqual(values["helper_exit_code"], ["20", "0"])
        self.assertEqual(v2253.last_value(values, "helper_exit_code"), "0")
        self.assertEqual(v2253.int_value(values, "helper_exit_code"), 0)
        self.assertIsNone(v2253.last_value(values, "missing"))
        self.assertNotIn("ignored", values)

    def test_summarize_phase_extracts_full_target_stack_and_sample_preview(self):
        text = "\n".join(kv_lines(before_symbols=v2253.TARGET_SYMBOLS, after_symbols=[]))
        values = v2253.parse_key_values(text)

        before = v2253.summarize_phase(values, "fwclass_req0_before_feed")
        after = v2253.summarize_phase(values, "fwclass_req0_after_feed")

        self.assertEqual(before["begin"], "1")
        self.assertEqual(before["target_hits"], 1)
        self.assertEqual(before["samples"], 5)
        self.assertEqual(before["symbols_present"], v2253.TARGET_SYMBOLS)
        self.assertTrue(before["full_target_stack"])
        self.assertEqual(before["target_samples"][0]["comm"], "kworker/u16:1")
        self.assertEqual(before["target_samples"][0]["symbol_count"], len(v2253.TARGET_SYMBOLS))
        self.assertFalse(after["full_target_stack"])
        self.assertEqual(after["symbol_count"], 0)


class BoundaryArtifactClassification(unittest.TestCase):
    def test_classify_boundary_artifacts_marks_before_feed_full_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_artifacts(Path(tmp), kv_lines(before_symbols=v2253.TARGET_SYMBOLS, after_symbols=[]))

            classification = v2253.classify_boundary_artifacts(paths)

        self.assertEqual(classification["ordering_class"], "target-stack-visible-before-feed")
        self.assertEqual(classification["boundary_phase_count"], 2)
        self.assertEqual(classification["before_full_requests"], [0])
        self.assertEqual(classification["after_full_requests"], [])
        self.assertEqual(classification["feeder_seen_count"], 1)
        self.assertEqual(classification["feeder_fed_count"], 1)
        self.assertEqual(classification["feeder_timed_out"], 1)
        self.assertEqual(classification["helper_exit_code"], "0")
        self.assertEqual(classification["requests"]["0"]["source_bytes"], 13343)
        self.assertTrue(classification["requests"]["0"]["before_feed"]["full_target_stack"])
        self.assertFalse(classification["requests"]["0"]["after_feed"]["full_target_stack"])

    def test_classify_boundary_artifacts_distinguishes_after_partial_and_missing_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            partial_paths = write_artifacts(
                Path(tmp) / "partial",
                kv_lines(before_symbols=[], after_symbols=v2253.TARGET_SYMBOLS[:2]),
            )
            missing_paths = write_artifacts(
                Path(tmp) / "missing",
                kv_lines(before_symbols=[], after_symbols=[], include_boundary=False),
            )

            partial = v2253.classify_boundary_artifacts(partial_paths)
            missing = v2253.classify_boundary_artifacts(missing_paths)

        self.assertEqual(partial["ordering_class"], "partial-target-stack-after-feed")
        self.assertEqual(partial["after_partial_requests"], [0])
        self.assertEqual(missing["ordering_class"], "boundary-markers-missing")
        self.assertEqual(missing["boundary_phase_count"], 0)


class ManifestClassificationAndRendering(unittest.TestCase):
    def test_dry_run_commands_include_verify_flash_collect_and_rollback_steps(self):
        plan = v2253.dry_run_commands({
            "test_image_sha256": "test-sha",
            "rollback_image_sha256": "rollback-sha",
        })

        self.assertIn("--verify-only", plan["current_verify"])
        self.assertEqual(len(plan["collect"]), len(v2253.REMOTE_ARTIFACTS))
        self.assertIn("test-sha", plan["flash_test_boot"])
        self.assertIn("rollback-sha", plan["rollback"])
        self.assertEqual(len(plan["post_rollback"]), 3)

    def test_classify_manifest_covers_dry_run_and_live_failure_branches(self):
        ready = v2253.classify_manifest({
            "execute": False,
            "preflight": {
                "build_manifest_exists": True,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": True,
                "rollback_image_exists": True,
            },
        })
        blocked = v2253.classify_manifest({
            "execute": False,
            "preflight": {
                "build_manifest_exists": False,
                "test_image_exists": True,
                "test_image_sha_matches_manifest": True,
                "rollback_image_exists": True,
            },
        })

        self.assertEqual(ready["decision"], "v2253-fwclass-boundary-stack-dry-run-ready")
        self.assertTrue(ready["pass"])
        self.assertEqual(blocked["decision"], "v2253-fwclass-boundary-stack-dry-run-blocked")
        self.assertFalse(blocked["pass"])

        cases = [
            (
                {"execute": True, "rollback": {"selftest_ok": False}},
                "v2253-fwclass-boundary-stack-rollback-selftest-failed",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "live_block": "preflight-current-baseline-failed"},
                "v2253-fwclass-boundary-stack-preflight-failed-no-flash",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "live_block": "test-flash-failed"},
                "v2253-fwclass-boundary-stack-test-flash-failed-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "collect": {"classification": {"ordering_class": "boundary-markers-missing"}}},
                "v2253-fwclass-boundary-stack-live-boundary-missing-rollback-pass",
                False,
            ),
            (
                {"execute": True, "rollback": {"selftest_ok": True}, "collect": {"classification": {"ordering_class": "target-stack-visible-before-feed"}}},
                "v2253-fwclass-boundary-stack-live-pass-target-stack-visible-before-feed",
                True,
            ),
        ]
        for manifest, decision, passed in cases:
            with self.subTest(decision=decision):
                result = v2253.classify_manifest(manifest)
                self.assertEqual(result["decision"], decision)
                self.assertEqual(result["pass"], passed)

    def test_render_report_includes_boundary_classification_and_safety_scope(self):
        classification = {
            "boundary_phase_count": 2,
            "ordering_class": "target-stack-visible-before-feed",
            "feeder_seen_count": 1,
            "feeder_fed_count": 1,
            "feeder_timed_out": 1,
            "supervisor_result": "wlan0-ready",
            "helper_exit_code": "0",
            "helper_timed_out": "0",
            "wlan0_present": "1",
            "requests": {
                "0": {
                    "request": "WCNSS_qcom_cfg.ini",
                    "seen": 1,
                    "fed": 1,
                    "final_seen": 1,
                    "final_fed": 1,
                    "source_bytes": 13343,
                    "before_feed": {"boundary_begin": "1", "target_hits": 1, "samples": 5, "symbol_count": 7, "full_target_stack": True},
                    "after_feed": {"boundary_begin": "1", "target_hits": 0, "samples": 5, "symbol_count": 0, "full_target_stack": False},
                }
            },
        }
        manifest = {
            "execute": True,
            "out_dir": "workspace/private/runs/kernel/unit",
            "result": {"decision": "v2253-fwclass-boundary-stack-live-pass-target-stack-visible-before-feed", "pass": True, "reason": "unit"},
            "preflight": {
                "test_image": "test.img",
                "test_image_sha256": "test-sha",
                "test_expect_version": v2253.TEST_EXPECT_VERSION,
                "rollback_image": "rollback.img",
                "rollback_image_sha256": "rollback-sha",
                "rollback_expect_version": v2253.ROLLBACK_EXPECT_VERSION,
            },
            "current_preflight": {"verify_ok": True, "selftest_ok": True},
            "test_flash": {"ok": True},
            "test_health": {"version_ok": True, "status_ok": True, "selftest_ok": True},
            "rollback": {"ok": True, "attempt": "from-native", "version_ok": True, "status_ok": True, "selftest_ok": True},
            "collect": {"classification": classification},
        }

        report = v2253.render_report(manifest)

        self.assertIn("# Native Init V2253 Firmware Class Boundary Stack Live", report)
        self.assertIn("Decision: `v2253-fwclass-boundary-stack-live-pass-target-stack-visible-before-feed`", report)
        self.assertIn("Ordering class: `target-stack-visible-before-feed`", report)
        self.assertIn("Request `0` `WCNSS_qcom_cfg.ini`", report)
        self.assertIn("full=`True`", report)
        self.assertIn("sampler-miss artifact", report)
        self.assertIn("Rollback target is V2237", report)


class ResidualState(unittest.TestCase):
    def test_residual_state_tracks_flash_and_rollback_cleanup_requirements(self):
        dry = v2253.residual_state({"execute": False, "steps": []})
        ok = v2253.residual_state({
            "execute": True,
            "steps": [{"name": "flash"}],
            "test_flash": {"ok": True},
            "rollback": {"ok": True, "selftest_ok": True, "attempt": "from-native"},
        })
        bad = v2253.residual_state({
            "execute": True,
            "steps": [{"name": "flash"}],
            "test_flash": {"ok": True},
            "rollback": {"ok": False, "selftest_ok": False, "attempt": "from-recovery"},
        })

        self.assertFalse(dry["device_touched"])
        self.assertTrue(dry["rollback_ok"])
        self.assertTrue(ok["device_touched"])
        self.assertTrue(ok["rollback_ok"])
        self.assertFalse(ok["cleanup_required"])
        self.assertFalse(bad["rollback_ok"])
        self.assertTrue(bad["cleanup_required"])
        self.assertEqual(bad["residual_risk"], "rollback-or-selftest-incomplete")


if __name__ == "__main__":
    unittest.main()
