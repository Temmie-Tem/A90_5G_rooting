"""Regression tests for native_kernel_raw_frame_slots_v2212."""

import unittest

from _loader import load_revalidation

v2212 = load_revalidation("native_kernel_raw_frame_slots_v2212")


class ParseHelperStdout(unittest.TestCase):
    def test_parse_int_accepts_decimal_and_hex(self):
        self.assertEqual(v2212.parse_int("42"), 42)
        self.assertEqual(v2212.parse_int("0x2a"), 42)
        self.assertEqual(v2212.parse_int("0X2A"), 42)

    def test_parse_helper_stdout_extracts_summary_offsets_and_keeps_raw(self):
        stdout = (
            "noise\n"
            "result=v2212-raw-frame-slots-complete\n"
            "offsets thread_fp=0x100 thread_sp=0x108 thread_pc=264\n"
            "summary comm=rawslots count=0x3 "
            "read_errors=0 task=0xffffff8001234000 thread_fp=0xffffff8008001000 "
            "thread_sp=0xffffffc000001000 thread_pc=0xffffff8008010000 "
            "fp_slot_next=0 fp_slot_raw_lr=0xffffff8008020000 "
            "fp2_slot_next=0x44 fp2_slot_raw_lr=0xffffff8009000002 "
            "sp_slot0=0xffffffc000002000 sp_slot8=0xffffff8008030000 "
            "last_pid=123 last_tgid=123\n"
        )

        parsed = v2212.parse_helper_stdout(stdout)

        self.assertEqual(parsed["offsets"], {"thread_fp": 0x100, "thread_sp": 0x108, "thread_pc": 264})
        self.assertEqual(parsed["summary"]["comm"], "rawslots")
        self.assertEqual(parsed["summary"]["count"], 3)
        self.assertEqual(parsed["summary"]["read_errors"], 0)
        self.assertEqual(parsed["summary"]["thread_pc"], 0xFFFFFF8008010000)
        self.assertEqual(parsed["summary"]["fp2_slot_raw_lr"], 0xFFFFFF8009000002)
        self.assertIs(parsed["raw_stdout"], stdout)

    def test_parse_helper_stdout_handles_missing_sections(self):
        parsed = v2212.parse_helper_stdout("result=check-only\n")

        self.assertEqual(parsed["summary"], {})
        self.assertEqual(parsed["offsets"], {})
        self.assertEqual(parsed["raw_stdout"], "result=check-only\n")


class ProbeAnalysis(unittest.TestCase):
    def test_classify_addr_marks_kernel_text_alignment_and_zero(self):
        zero = v2212.classify_addr(0)
        text = v2212.classify_addr(v2212.KERNEL_TEXT_MIN + 0x20)
        misaligned = v2212.classify_addr(v2212.KERNEL_TEXT_MIN + 2)
        kernel_nontext = v2212.classify_addr(0xFFFFFFC000001000)

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

    def test_analyze_probe_classifies_lr_fields_and_raw_slot_presence(self):
        probe = {
            "summary": {
                "task": 0xFFFFFF8001234000,
                "thread_fp": 0xFFFFFFC000001000,
                "thread_sp": 0xFFFFFFC000002000,
                "thread_pc": v2212.KERNEL_TEXT_MIN + 0x100,
                "fp_slot_next": 0,
                "fp_slot_raw_lr": v2212.KERNEL_TEXT_MIN + 2,
                "fp2_slot_next": 0xFFFFFFC000003000,
                "fp2_slot_raw_lr": v2212.KERNEL_TEXT_MIN + 0x200,
                "sp_slot0": 0,
                "sp_slot8": 0xFFFFFFC000004000,
            }
        }

        analysis = v2212.analyze_probe(probe)

        self.assertEqual(
            analysis["canonical_aligned_lr_fields"],
            ["thread_pc", "fp2_slot_raw_lr"],
        )
        self.assertEqual(analysis["canonical_misaligned_lr_fields"], ["fp_slot_raw_lr"])
        self.assertEqual(
            analysis["nonzero_frame_slots"],
            ["fp_slot_raw_lr", "fp2_slot_next", "fp2_slot_raw_lr", "sp_slot8"],
        )
        self.assertTrue(analysis["has_raw_frame_slot"])
        self.assertIn("sched_switch fires before", analysis["sched_switch_timing_note"])

    def test_analyze_probe_defaults_missing_values_to_zero(self):
        analysis = v2212.analyze_probe({"summary": {}})

        self.assertFalse(analysis["has_raw_frame_slot"])
        self.assertEqual(analysis["canonical_aligned_lr_fields"], [])
        self.assertEqual(analysis["classified"]["thread_pc"]["hex"], "0x0000000000000000")


class ReportRendering(unittest.TestCase):
    def test_render_report_includes_decision_classification_safety_and_evidence(self):
        summary = {
            "decision": "v2212-raw-frame-slots-captured",
            "pass": True,
            "selftest_fail0": True,
            "phase_timer_contract": "phase-v1",
            "residual_state_contract": "clean",
            "out_dir": "workspace/private/runs/kernel/v2212-test",
            "build": {"helper_sha256": "abc123"},
            "probe": {
                "summary": {
                    "count": 1,
                    "read_errors": 0,
                    "comm": "rawslots",
                    "last_pid": 123,
                    "last_tgid": 123,
                }
            },
            "analysis": {
                "classified": {
                    "task": v2212.classify_addr(0xFFFFFF8001234000),
                    "thread_fp": v2212.classify_addr(0xFFFFFFC000001000),
                    "thread_sp": v2212.classify_addr(0xFFFFFFC000002000),
                    "thread_pc": v2212.classify_addr(v2212.KERNEL_TEXT_MIN + 0x100),
                    "fp_slot_next": v2212.classify_addr(0),
                    "fp_slot_raw_lr": v2212.classify_addr(0xFFFFFFC000003000),
                    "fp2_slot_next": v2212.classify_addr(0),
                    "fp2_slot_raw_lr": v2212.classify_addr(0),
                    "sp_slot0": v2212.classify_addr(0),
                    "sp_slot8": v2212.classify_addr(v2212.KERNEL_TEXT_MIN + 0x200),
                },
                "canonical_aligned_lr_fields": ["thread_pc", "sp_slot8"],
                "canonical_misaligned_lr_fields": [],
                "nonzero_frame_slots": ["fp_slot_raw_lr", "sp_slot8"],
            },
            "safety": {
                "read_only_bpf": True,
                "probe_write_user_executed": False,
                "flash_reboot": False,
            },
        }

        report = v2212.render_report(summary)

        self.assertIn("# Native Init V2212 Raw Frame Slots Live Capture", report)
        self.assertIn("- Decision: `v2212-raw-frame-slots-captured`", report)
        self.assertIn("- Helper comm: `rawslots`", report)
        self.assertIn("- Canonical aligned LR-like fields: `thread_pc, sp_slot8`", report)
        self.assertIn("- Nonzero raw frame slots: `fp_slot_raw_lr, sp_slot8`", report)
        self.assertIn("- read_only_bpf: `true`", report)
        self.assertIn("- probe_write_user_executed: `false`", report)
        self.assertIn("- Helper SHA-256: `abc123`", report)


if __name__ == "__main__":
    unittest.main()
