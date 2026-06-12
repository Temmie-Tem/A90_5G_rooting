"""Regression tests for native_kernel_raw_frame_sample_ring_v2213."""

import unittest

from _loader import load_revalidation

v2213 = load_revalidation("native_kernel_raw_frame_sample_ring_v2213")


class ParseHelperStdout(unittest.TestCase):
    def test_parse_int_accepts_decimal_and_hex(self):
        self.assertEqual(v2213.parse_int("42"), 42)
        self.assertEqual(v2213.parse_int("0x2a"), 42)
        self.assertEqual(v2213.parse_int("0X2A"), 42)

    def test_parse_helper_stdout_extracts_stats_meta_offsets_and_samples(self):
        stdout = (
            "result=v2213-raw-frame-sample-ring-complete\n"
            "offsets thread_fp=0x100 thread_sp=0x108 thread_pc=264\n"
            "stats count=0x4 read_errors=1 sample_capacity=4\n"
            "samples occupied=0x2 capacity=4 printed=2\n"
            "sample idx=0 pid=100 tgid=100 comm=worker thread_pc=0xffffff8008010000 "
            "fp_slot_next=0xffffffc000001000 fp_slot_raw_lr=0xffffff8008020000 "
            "fp2_slot_next=0 fp2_slot_raw_lr=0 sp_slot8=0xffffffc000002000\n"
            "sample idx=1 pid=101 tgid=101 comm=idle thread_pc=0xffffffc000003000 "
            "fp_slot_next=0 fp_slot_raw_lr=0xffffffc000004000 "
            "fp2_slot_next=0xffffffc000005000 fp2_slot_raw_lr=0xffffff8008030000 sp_slot8=0\n"
        )

        parsed = v2213.parse_helper_stdout(stdout)

        self.assertEqual(parsed["offsets"], {"thread_fp": 0x100, "thread_sp": 0x108, "thread_pc": 264})
        self.assertEqual(parsed["stats"], {"count": 4, "read_errors": 1, "sample_capacity": 4})
        self.assertEqual(parsed["sample_meta"], {"occupied": 2, "capacity": 4, "printed": 2})
        self.assertEqual(len(parsed["samples"]), 2)
        self.assertEqual(parsed["samples"][0]["comm"], "worker")
        self.assertEqual(parsed["samples"][0]["thread_pc"], 0xFFFFFF8008010000)
        self.assertEqual(parsed["samples"][1]["fp2_slot_raw_lr"], 0xFFFFFF8008030000)
        self.assertIs(parsed["raw_stdout"], stdout)

    def test_parse_helper_stdout_handles_missing_sections(self):
        parsed = v2213.parse_helper_stdout("result=check-only\n")

        self.assertEqual(parsed["stats"], {})
        self.assertEqual(parsed["offsets"], {})
        self.assertEqual(parsed["sample_meta"], {})
        self.assertEqual(parsed["samples"], [])


class ProbeAnalysis(unittest.TestCase):
    def test_classify_addr_marks_kernel_text_alignment_and_zero(self):
        zero = v2213.classify_addr(0)
        text = v2213.classify_addr(v2213.KERNEL_TEXT_MIN + 0x20)
        misaligned = v2213.classify_addr(v2213.KERNEL_TEXT_MIN + 2)
        kernel_nontext = v2213.classify_addr(0xFFFFFFC000001000)

        self.assertFalse(zero["nonzero"])
        self.assertFalse(zero["kernel_va"])
        self.assertTrue(text["kernel_va"])
        self.assertTrue(text["kernel_text"])
        self.assertTrue(text["aligned_4"])
        self.assertTrue(text["aligned_16"])
        self.assertTrue(misaligned["kernel_text"])
        self.assertFalse(misaligned["aligned_4"])
        self.assertTrue(kernel_nontext["kernel_va"])
        self.assertFalse(kernel_nontext["kernel_text"])

    def test_analyze_probe_counts_uniques_and_ring_saturation(self):
        probe = {
            "stats": {"count": 4, "sample_capacity": 4},
            "sample_meta": {"occupied": 4},
            "samples": [
                {
                    "pid": 100,
                    "comm": "worker",
                    "thread_pc": v2213.KERNEL_TEXT_MIN + 0x100,
                    "fp_slot_next": 0xFFFFFFC000001000,
                    "fp_slot_raw_lr": v2213.KERNEL_TEXT_MIN + 0x200,
                    "fp2_slot_next": 0,
                    "fp2_slot_raw_lr": 0,
                    "sp_slot8": 0xFFFFFFC000002000,
                },
                {
                    "pid": 101,
                    "comm": "idle",
                    "thread_pc": 0xFFFFFFC000003000,
                    "fp_slot_next": 0,
                    "fp_slot_raw_lr": 0xFFFFFFC000004000,
                    "fp2_slot_next": 0xFFFFFFC000005000,
                    "fp2_slot_raw_lr": v2213.KERNEL_TEXT_MIN + 0x300,
                    "sp_slot8": 0,
                },
                {
                    "pid": 100,
                    "comm": "worker",
                    "thread_pc": v2213.KERNEL_TEXT_MIN + 0x100,
                    "fp_slot_next": 0,
                    "fp_slot_raw_lr": 0,
                    "fp2_slot_next": 0,
                    "fp2_slot_raw_lr": 0,
                    "sp_slot8": 0,
                },
            ],
        }

        analysis = v2213.analyze_probe(probe)

        self.assertEqual(analysis["counts"]["printed_samples"], 3)
        self.assertEqual(analysis["counts"]["walkable_fp_next"], 1)
        self.assertEqual(analysis["counts"]["walkable_fp2_next"], 1)
        self.assertEqual(analysis["counts"]["raw_lr_nonzero"], 2)
        self.assertEqual(analysis["counts"]["raw_lr_kernel_text"], 1)
        self.assertEqual(analysis["counts"]["raw_lr_kernel_va_nontext"], 1)
        self.assertEqual(analysis["counts"]["thread_pc_kernel_text"], 2)
        self.assertEqual(analysis["unique_counts"]["thread_pc"], 2)
        self.assertEqual(analysis["unique_counts"]["fp_slot_raw_lr"], 2)
        self.assertEqual(analysis["unique_comms"], ["idle", "worker"])
        self.assertEqual(analysis["unique_comm_count"], 2)
        self.assertEqual(analysis["unique_pid_count"], 2)
        self.assertTrue(analysis["sample_ring_saturated"])
        self.assertIn("ring saturated", analysis["convergence_hint"])

    def test_analyze_probe_not_saturated_when_capacity_exceeds_occupied(self):
        analysis = v2213.analyze_probe({
            "stats": {"sample_capacity": 8},
            "sample_meta": {"occupied": 2},
            "samples": [],
        })

        self.assertFalse(analysis["sample_ring_saturated"])
        self.assertEqual(analysis["capacity"], 8)
        self.assertEqual(analysis["occupied_samples"], 2)
        self.assertIn("longer duration", analysis["convergence_hint"])


class ReportRendering(unittest.TestCase):
    def test_render_report_includes_metrics_safety_and_evidence(self):
        summary = {
            "decision": "v2213-raw-frame-sample-ring-captured",
            "pass": True,
            "selftest_fail0": True,
            "phase_timer_contract": "phase-v1",
            "residual_state_contract": "clean",
            "out_dir": "workspace/private/runs/kernel/v2213-test",
            "build": {"helper_sha256": "def456"},
            "probe": {"stats": {"count": 4}},
            "analysis": {
                "counts": {
                    "printed_samples": 2,
                    "walkable_fp_next": 1,
                    "walkable_fp2_next": 0,
                    "raw_lr_nonzero": 2,
                    "raw_lr_kernel_text": 1,
                    "raw_lr_kernel_va_nontext": 1,
                    "thread_pc_kernel_text": 2,
                },
                "unique_counts": {
                    "thread_pc": 2,
                    "fp_slot_raw_lr": 2,
                    "fp_slot_next": 1,
                    "fp2_slot_raw_lr": 1,
                    "sp_slot8": 1,
                },
                "unique_preview": {
                    "thread_pc": ["0xffffff8008010000"],
                    "fp_slot_raw_lr": ["0xffffff8008020000"],
                    "fp_slot_next": [],
                    "fp2_slot_raw_lr": [],
                    "sp_slot8": ["0xffffffc000002000"],
                },
                "unique_comm_count": 2,
                "unique_pid_count": 2,
                "occupied_samples": 2,
                "capacity": 4,
                "sample_ring_saturated": False,
                "convergence_hint": "ring not saturated; longer duration can still add information",
            },
            "safety": {
                "read_only_bpf": True,
                "probe_write_user_executed": False,
                "flash_reboot": False,
            },
        }

        report = v2213.render_report(summary)

        self.assertIn("# Native Init V2213 Raw Frame Sample Ring", report)
        self.assertIn("- Decision: `v2213-raw-frame-sample-ring-captured`", report)
        self.assertIn("- Total samples observed: `4`", report)
        self.assertIn("- Raw LR in kernel text: `1`", report)
        self.assertIn("| `thread_pc` | 2 | 0xffffff8008010000 |", report)
        self.assertIn("- Ring saturated: `false`", report)
        self.assertIn("- read_only_bpf: `true`", report)
        self.assertIn("- Helper SHA-256: `def456`", report)


if __name__ == "__main__":
    unittest.main()
