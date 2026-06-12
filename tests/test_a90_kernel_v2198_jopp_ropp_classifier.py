"""Regression tests for a90_kernel_v2198_jopp_ropp_classifier.

Exercises deterministic host-only parsing and scoring helpers with synthetic
kernel bytes, symbols, logs, and source snippets. No device access.
"""

import struct
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

classifier = load_revalidation("a90_kernel_v2198_jopp_ropp_classifier")


def put_u32(raw: bytearray, synthetic_base: int, address: int, value: int) -> None:
    struct.pack_into("<I", raw, address - synthetic_base, value)


class ScalarSymbolAndInstructionHelpers(unittest.TestCase):
    def test_parse_int_and_format_signed_hex(self):
        self.assertEqual(classifier.parse_int("0x10"), 16)
        self.assertEqual(classifier.parse_int(" 12 "), 12)
        self.assertEqual(classifier.format_signed_hex(0), "0x0")
        self.assertEqual(classifier.format_signed_hex(0x20), "0x20")
        self.assertEqual(classifier.format_signed_hex(-0x20), "-0x20")

    def test_nearest_symbol_and_symbol_index(self):
        symbols = [
            classifier.Symbol(0x1000, "T", "first"),
            classifier.Symbol(0x1010, "T", "second"),
            classifier.Symbol(0x1020, "T", "second"),
        ]
        addresses = [symbol.address for symbol in symbols]

        self.assertIsNone(classifier.nearest_symbol(symbols, addresses, 0x0fff))
        hit = classifier.nearest_symbol(symbols, addresses, 0x1004)
        self.assertEqual(hit["symbol"], "first")
        self.assertEqual(hit["offset"], 4)
        self.assertEqual(hit["next_delta"], 0x0c)

        index = classifier.build_symbol_index(symbols)
        self.assertEqual(index["second"], 0x1010)

    def test_arm64_call_instruction_helpers(self):
        bl_next_16 = 0x94000004
        self.assertTrue(classifier.is_bl(bl_next_16))
        self.assertFalse(classifier.is_blr(bl_next_16))
        self.assertEqual(classifier.decode_bl_target(bl_next_16, 0x1000), 0x1010)

        blr_x0 = 0xD63F0000
        blr_x16 = 0xD63F0200
        self.assertTrue(classifier.is_blr(blr_x0))
        self.assertTrue(classifier.is_blr(blr_x16))
        self.assertFalse(classifier.is_bl(blr_x0))


class KernelByteHelpers(unittest.TestCase):
    def test_magic_scans_u32_reads_and_function_entry_classification(self):
        base = 0x100000
        entry = base + 0x80
        raw = bytearray(0x200)
        put_u32(raw, base, entry - 4, classifier.JOPP_MAGIC)
        put_u32(raw, base, entry + 8, classifier.ROPP_EOR_X16_X30_X17)

        magic_addresses = classifier.find_magic_addresses(bytes(raw), base)
        self.assertEqual(magic_addresses, [entry - 4])
        self.assertEqual(classifier.read_u32(bytes(raw), base, entry - 4), classifier.JOPP_MAGIC)
        self.assertIsNone(classifier.read_u32(bytes(raw), base, base - 4))

        entry_info = classifier.classify_function_entry(bytes(raw), base, entry)
        self.assertTrue(entry_info["jopp_magic_before_entry"])
        self.assertEqual(entry_info["ropp_prologue_offsets"], [8])
        self.assertTrue(entry_info["ropp_prologue_present"])


class LogAndSourceParsers(unittest.TestCase):
    def test_parse_stack_and_timer_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stack_log = root / "stack.log"
            stack_log.write_text(
                "noise\n"
                "stack_ip index=0 value=0xffffff8000001000\n"
                "stack_ip index=1 value=0xffffff8000002000\n"
            )
            timer_log = root / "timer.log"
            timer_log.write_text(
                "value=18446744073709551617 count=2\n"
                "value=1 count=3\n"
                "value=2 count=7\n"
            )

            self.assertEqual(
                classifier.parse_stack_logs([stack_log]),
                [0xffffff8000001000, 0xffffff8000002000],
            )
            timers = classifier.parse_timer_logs([timer_log])
            self.assertEqual(timers, [
                classifier.TimerValue(2, 7),
                classifier.TimerValue(1, 5),
            ])

    def test_extract_timer_callback_candidates_and_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "driver.c"
            source.write_text(
                "DEFINE_TIMER(global_timer, high_cb);\n"
                "setup_timer(&dev->timer, setup_cb, 0);\n"
                "timer_setup(&dev->timer2, timer_setup_cb, 0);\n"
                "dev->timer.function = low_cb;\n"
                "timer.function = NULL;\n"
            )

            callbacks = classifier.extract_timer_callback_candidates([root])
            self.assertEqual(callbacks["scanned_files"], 1)
            self.assertIn("high_cb", callbacks["high_confidence"])
            self.assertIn("setup_cb", callbacks["high_confidence"])
            self.assertIn("timer_setup_cb", callbacks["high_confidence"])
            self.assertIn("low_cb", callbacks["low_confidence"])
            self.assertNotIn("NULL", callbacks["low_confidence"])
            self.assertEqual(classifier.callback_confidence("high_cb", callbacks), "high")
            self.assertEqual(classifier.callback_confidence("low_cb", callbacks), "low")
            self.assertEqual(classifier.callback_confidence("missing", callbacks), "none")


class SlideScoring(unittest.TestCase):
    def test_timer_magic_candidate_slides_bounds_and_caps(self):
        timers = [classifier.TimerValue(0x1100, 5)]
        magic_addresses = [0x1000, 0x1008]
        candidates = classifier.timer_magic_candidate_slides(
            timers,
            magic_addresses,
            deltas=[4, 8],
            slide_min=0,
            slide_max=0x200,
        )

        self.assertIn(0x0f8, candidates)
        self.assertIn(0x0f0, candidates)
        self.assertEqual(candidates[0x0f8][0]["timer_index"], 0)
        self.assertEqual(candidates[0x0f8][0]["timer_count"], 5)

    def test_score_timer_slide_weights_magic_and_callback_confidence(self):
        base = 0x100000
        slide = 0x1000
        entry = base + 0x80
        raw = bytearray(0x240)
        put_u32(raw, base, entry - 4, classifier.JOPP_MAGIC)
        put_u32(raw, base, entry + 8, classifier.ROPP_EOR_X16_X30_X17)
        symbols = [
            classifier.Symbol(entry, "T", "cb_high"),
            classifier.Symbol(base + 0x100, "T", "other"),
        ]
        addresses = [symbol.address for symbol in symbols]
        callbacks = {
            "scanned_files": 0,
            "high_confidence": {"cb_high": ["driver.c"]},
            "low_confidence": {},
        }
        timers = [
            classifier.TimerValue(entry + slide, 5),
            classifier.TimerValue(base + 0x120 + slide, 2),
        ]

        result = classifier.score_timer_slide(
            slide,
            timers,
            bytes(raw),
            base,
            symbols,
            addresses,
            callbacks,
            deltas=[4, 8],
        )

        self.assertEqual(result["slide_hex"], "0x1000")
        self.assertEqual(result["magic_distinct"], 1)
        self.assertEqual(result["magic_weight"], 5)
        self.assertEqual(result["high_callback_weight"], 5)
        self.assertEqual(result["known_callback_weight"], 5)
        self.assertTrue(result["dominant_timer_magic"])
        self.assertEqual(result["timer_rows"][0]["callback_confidence"], "high")
        self.assertEqual(result["timer_rows"][0]["entry"]["ropp_prologue_offsets"], [8])
        self.assertEqual(result["timer_rows"][1]["magic_deltas"], [])

    def test_score_stack_slide_detects_direct_springboard_callsite(self):
        base = 0x100000
        slide = 0x1000
        caller = base + 0x80
        springboard = base + 0x180
        prev_pc = caller - 4
        imm26 = (springboard - prev_pc) >> 2
        bl_to_springboard = 0x94000000 | imm26
        raw = bytearray(0x240)
        put_u32(raw, base, prev_pc, bl_to_springboard)
        symbols = [
            classifier.Symbol(caller, "T", "caller"),
            classifier.Symbol(springboard, "T", "jopp_springboard_blr_x0"),
        ]
        addresses = [symbol.address for symbol in symbols]

        result = classifier.score_stack_slide(
            slide,
            [caller + slide],
            bytes(raw),
            base,
            symbols,
            addresses,
            {springboard},
        )

        self.assertEqual(result["mapped"], 1)
        self.assertEqual(result["direct_callsite_hits"], 1)
        self.assertEqual(result["springboard_callsite_hits"], 1)
        row = result["rows"][0]
        self.assertEqual(row["symbol"], "caller")
        self.assertTrue(row["direct_callsite"])
        self.assertTrue(row["springboard_callsite"])
        self.assertEqual(row["bl_target_symbol"], "jopp_springboard_blr_x0")


if __name__ == "__main__":
    unittest.main()
