"""Regression tests for native_kernel_file_ops_anchor_v2204 host helpers."""

import tempfile
import unittest
from pathlib import Path

from _loader import REVAL_DIR, load_revalidation

import sys

if str(REVAL_DIR) not in sys.path:
    sys.path.insert(0, str(REVAL_DIR))

v2204 = load_revalidation("native_kernel_file_ops_anchor_v2204")


class ScalarHelpers(unittest.TestCase):
    def test_step_result_ok_tracks_return_code(self):
        ok = v2204.StepResult("ok", ["true"], 0, 0.1, "out", "err")
        failed = v2204.StepResult("failed", ["false"], 1, 0.1, "out", "err")

        self.assertTrue(ok.ok)
        self.assertFalse(failed.ok)

    def test_sha256_file_and_format_signed_hex(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.bin"
            path.write_bytes(b"abc")

            self.assertEqual(
                v2204.sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
        self.assertEqual(v2204.format_signed_hex(0), "0x0")
        self.assertEqual(v2204.format_signed_hex(0x123), "0x123")
        self.assertEqual(v2204.format_signed_hex(-0x123), "-0x123")

    def test_parse_key_values_and_parse_int(self):
        self.assertEqual(
            v2204.parse_key_values("count=7 fd0_fop=0xffffff8000001000 stray fd1_fop=42"),
            {"count": "7", "fd0_fop": "0xffffff8000001000", "fd1_fop": "42"},
        )
        self.assertEqual(v2204.parse_int("42"), 42)
        self.assertEqual(v2204.parse_int("0x2a"), 42)


class ProbeAndMapParsing(unittest.TestCase):
    def test_parse_probe_stdout_extracts_summary_anchors_and_offsets(self):
        parsed = v2204.parse_probe_stdout(
            "noise\n"
            "summary count=3 read_errors=0 task=0x100 files=0x200 fdt=0x300 fd0_fop=0x1100 fd1_fop=0x2200\n"
            "anchor fd0_name=/dev/null fd1_name=/dev/zero\n"
            "offsets task_files=0x8 files_fdt=24\n"
        )

        self.assertEqual(
            parsed["summary"],
            {
                "count": 3,
                "read_errors": 0,
                "task": 0x100,
                "files": 0x200,
                "fdt": 0x300,
                "fd0_fop": 0x1100,
                "fd1_fop": 0x2200,
            },
        )
        self.assertEqual(parsed["anchors"], {"fd0_name": "/dev/null", "fd1_name": "/dev/zero"})
        self.assertEqual(parsed["offsets"], {"task_files": 0x8, "files_fdt": 24})

    def test_parse_probe_stdout_without_summary_is_empty(self):
        self.assertEqual(v2204.parse_probe_stdout("anchor fd0=1\n"), {"summary": {}, "anchors": {}, "offsets": {}})

    def test_parse_system_map_skips_invalid_rows_and_keeps_first_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "System.map"
            path.write_text(
                "not-an-address T ignored\n"
                "0000000000001000 T null_fops\n"
                "0000000000002000 T null_fops\n"
                "0000000000003000 T zero_fops\n",
                encoding="utf-8",
            )

            symbols = v2204.parse_system_map(path)

            self.assertEqual(symbols["null_fops"], 0x1000)
            self.assertEqual(symbols["zero_fops"], 0x3000)
            self.assertNotIn("ignored", symbols)


class FileOpsAnalysis(unittest.TestCase):
    def test_analyze_fops_marks_exact_when_two_independent_anchors_agree(self):
        probe = {
            "summary": {
                "fd0_fop": 0xFFFF000000001000,
                "fd1_fop": 0xFFFF000000002000,
                "fd2_fop": 0xFFFF000000003000,
            }
        }
        symbols = {
            "null_fops": 0x1000,
            "zero_fops": 0x2000,
            "version_proc_fops": 0x4444,
            "proc_reg_file_ops": 0x3000,
        }

        analysis = v2204.analyze_fops(probe, symbols)

        self.assertTrue(analysis["exact_slide"])
        self.assertEqual(analysis["best_slide"], 0xFFFF000000000000)
        self.assertEqual(analysis["best_slide_hex"], "0xffff000000000000")
        self.assertEqual(
            analysis["best_sources"],
            ["fd0_fop:null_fops", "fd1_fop:zero_fops", "fd2_fop:proc_reg_file_ops"],
        )
        self.assertEqual(analysis["unique_slides"][0]["count"], 3)
        fd2 = next(item for item in analysis["observations"] if item["field"] == "fd2_fop")
        self.assertEqual([candidate["symbol"] for candidate in fd2["candidates"]], ["version_proc_fops", "proc_reg_file_ops"])

    def test_analyze_fops_requires_at_least_two_matching_anchors(self):
        analysis = v2204.analyze_fops(
            {"summary": {"fd0_fop": 0x2000, "fd1_fop": 0, "fd2_fop": 0}},
            {"null_fops": 0x1000},
        )

        self.assertFalse(analysis["exact_slide"])
        self.assertEqual(analysis["best_slide"], 0x1000)
        self.assertEqual(analysis["reason"], "fewer than two independent file_operations anchors agreed")


class ResidualAndReport(unittest.TestCase):
    def test_residual_state_tracks_touch_and_selftest_cleanup_risk(self):
        clean = v2204.residual_state({"selftest_fail0": True, "steps": [{"name": "version"}]})
        self.assertTrue(clean["device_touched"])
        self.assertTrue(clean["selftest_ok"])
        self.assertFalse(clean["cleanup_required"])
        self.assertEqual(clean["residual_risk"], "none")
        self.assertTrue(clean["read_only_bpf"])
        self.assertFalse(clean["credentials_used"])

        dirty = v2204.residual_state({"selftest_fail0": False, "steps": [{"name": "probe"}]})
        self.assertTrue(dirty["cleanup_required"])
        self.assertEqual(dirty["residual_risk"], "post-selftest-incomplete")

        untouched = v2204.residual_state({"selftest_fail0": False, "steps": []})
        self.assertFalse(untouched["device_touched"])
        self.assertFalse(untouched["cleanup_required"])

    def test_render_report_includes_decision_analysis_safety_and_evidence(self):
        report = v2204.render_report(
            {
                "decision": "v2204-file-ops-anchor-exact",
                "pass": True,
                "phase_timer_contract": "recorded",
                "residual_state_contract": "recorded",
                "analysis": {
                    "exact_slide": True,
                    "best_slide_hex": "0x1000",
                    "reason": "anchors agree",
                    "observations": [
                        {
                            "field": "fd0_fop",
                            "runtime": "0x0000000000002000",
                            "candidates": [{"symbol": "null_fops", "slide_hex": "0x1000"}],
                        }
                    ],
                },
                "probe": {"summary": {"count": 4, "read_errors": 0, "task": 1, "files": 2, "fdt": 3}},
                "safety": {"read_only_bpf": True, "credentials_used": False},
                "out_dir": "workspace/private/runs/kernel/v2204",
                "system_map": "System.map",
                "build": {"anchor_sha256": "abc123"},
                "selftest_fail0": True,
            }
        )

        self.assertIn("# Native Init V2204 File-Operations Slide Anchor", report)
        self.assertIn("- Decision: `v2204-file-ops-anchor-exact`", report)
        self.assertIn("- Exact slide: `true`", report)
        self.assertIn("| `fd0_fop` | `0x0000000000002000` | `null_fops` 0x1000 |", report)
        self.assertIn("- read_only_bpf: `true`", report)
        self.assertIn("- credentials_used: `false`", report)
        self.assertIn("- Helper SHA-256: `abc123`", report)


if __name__ == "__main__":
    unittest.main()
