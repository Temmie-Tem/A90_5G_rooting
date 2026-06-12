"""Regression tests for a90_kernel_v2215_perf_regs_ropp_jopp_classifier."""

import json
import struct
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2215 = load_revalidation("a90_kernel_v2215_perf_regs_ropp_jopp_classifier")

BASE = 0xFFFFFF8008000000


def encode_bl(pc: int, target: int) -> int:
    imm26 = ((target - pc) >> 2) & 0x03FFFFFF
    return 0x94000000 | imm26


class ScalarMapAndImageHelpers(unittest.TestCase):
    def test_parse_int_and_hex_formatters(self):
        self.assertEqual(v2215.parse_int(7), 7)
        self.assertEqual(v2215.parse_int("42"), 42)
        self.assertEqual(v2215.parse_int("0x2a"), 42)
        self.assertEqual(v2215.hex64(-1), "0xffffffffffffffff")
        self.assertEqual(v2215.hex_signed(-0x20), "-0x20")
        self.assertEqual(v2215.hex_signed(0x20), "0x20")

    def test_parse_system_map_index_and_nearest_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "System.map"
            path.write_text(
                "nothex T ignored\n"
                f"{BASE + 0x3000:016x} T beta\n"
                f"{BASE + 0x1000:016x} T alpha\n"
                f"{BASE + 0x2000:016x} W alpha\n",
                encoding="utf-8",
            )

            symbols = v2215.parse_system_map(path)
            index = v2215.build_symbol_index(symbols)
            addresses = [symbol.address for symbol in symbols]
            nearest = v2215.nearest_symbol(symbols, addresses, BASE + 0x2100)

        self.assertEqual([symbol.address for symbol in symbols], [BASE + 0x1000, BASE + 0x2000, BASE + 0x3000])
        self.assertEqual(index["alpha"], BASE + 0x1000)
        self.assertEqual(nearest["symbol"], "alpha")
        self.assertEqual(nearest["kind"], "W")
        self.assertEqual(nearest["offset"], 0x100)
        self.assertEqual(nearest["offset_hex"], "0x100")
        self.assertIsNone(v2215.nearest_symbol(symbols, addresses, BASE + 0x0FFF))

    def test_load_kernel_raw_synthetic_base_read_and_bl_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "kernel.raw"
            raw_path.write_bytes(b"\x00\x01\x02\x03payload")
            wrapped = root / "wrapped.raw"
            wrapped.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 7) + b"payload")
            truncated = root / "truncated.raw"
            truncated.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 9) + b"short")
            meta = root / "stock.json"
            meta.write_text(json.dumps({"synthetic_base": hex(BASE)}), encoding="utf-8")

            self.assertEqual(v2215.load_kernel_raw(raw_path), b"\x00\x01\x02\x03payload")
            self.assertEqual(v2215.load_kernel_raw(wrapped), b"payload")
            with self.assertRaises(ValueError):
                v2215.load_kernel_raw(truncated)
            self.assertEqual(v2215.load_synthetic_base(meta), BASE)
            self.assertEqual(v2215.read_u32(raw_path.read_bytes(), BASE, BASE), 0x03020100)
            self.assertIsNone(v2215.read_u32(raw_path.read_bytes(), BASE, BASE - 4))

        pc = BASE + 0x1000
        forward = encode_bl(pc, pc + 0x40)
        backward = encode_bl(pc, pc - 0x40)
        self.assertTrue(v2215.is_bl(forward))
        self.assertFalse(v2215.is_bl(0xD65F03C0))
        self.assertEqual(v2215.decode_bl_target(forward, pc), pc + 0x40)
        self.assertEqual(v2215.decode_bl_target(backward, pc), pc - 0x40)


class RangeSlideAndCallsiteHelpers(unittest.TestCase):
    def build_fixture(self):
        raw = bytearray(0x2000)
        direct_call = BASE + 0x100
        spring_call = BASE + 0x180
        direct_target = BASE + 0x900
        spring_target = BASE + 0xA00
        struct.pack_into("<I", raw, direct_call - BASE, encode_bl(direct_call, direct_target))
        struct.pack_into("<I", raw, spring_call - BASE, encode_bl(spring_call, spring_target))
        symbols = [
            v2215.Symbol(BASE, "T", "_text"),
            v2215.Symbol(BASE, "T", "_stext"),
            v2215.Symbol(BASE + 0x500, "D", "data_ignored"),
            v2215.Symbol(direct_target, "T", "target_func"),
            v2215.Symbol(spring_target, "T", "jopp_springboard_blr_x0"),
            v2215.Symbol(BASE + 0x1000, "T", "_etext"),
        ]
        symbols.sort(key=lambda symbol: symbol.address)
        addresses = [symbol.address for symbol in symbols]
        index = v2215.build_symbol_index(symbols)
        ranges = v2215.build_function_ranges(symbols, BASE, BASE + 0x1000)
        starts = [item.start for item in ranges]
        callsites = v2215.build_callsite_map(bytes(raw), BASE, symbols, addresses, index)
        return symbols, addresses, ranges, starts, callsites, direct_call + 4, spring_call + 4

    def test_function_ranges_lookup_union_and_slide_intervals(self):
        _symbols, _addresses, ranges, starts, _callsites, direct_return, spring_return = self.build_fixture()
        slide = 0x80000
        intervals = v2215.top_slide_intervals([direct_return + slide, spring_return + slide], ranges, slide - 4, slide + 4, limit=4)
        candidates = v2215.candidate_slides_from_intervals(intervals)

        target = v2215.function_lookup(ranges, starts, BASE + 0x920)
        self.assertEqual(target.name, "target_func")
        self.assertIsNone(v2215.function_lookup(ranges, starts, BASE + 0x2000))
        self.assertEqual(v2215.union_intervals([(5, 7), (1, 3), (4, 4), (10, 11)]), [(1, 7), (10, 11)])
        self.assertGreaterEqual(intervals[0]["coverage_unique"], 1)
        self.assertIn(slide, candidates)

    def test_callsite_map_score_and_slide_classifiers(self):
        symbols, addresses, ranges, starts, callsites, direct_return, spring_return = self.build_fixture()
        slide = 0x80000
        pc_values = [BASE + 0x920 + slide, BASE + 0xA20 + slide]
        lr_values = [direct_return + slide, spring_return + slide, BASE + 0x920 + slide]
        score = v2215.score_slide(slide, pc_values, lr_values, ranges, starts, callsites)
        no_slide = v2215.classify_no_slide([BASE - 1, BASE + 1, BASE + 0x2000], symbols, addresses, BASE, BASE + 0x1000)
        under_slide = v2215.classify_under_slide(lr_values, slide, ranges, starts, callsites)

        self.assertEqual(callsites[direct_return][0].kind, "direct")
        self.assertEqual(callsites[spring_return][0].kind, "springboard")
        self.assertEqual(score["pc_func"], 2)
        self.assertEqual(score["lr_func"], 3)
        self.assertEqual(score["lr_callsite"], 2)
        self.assertEqual(score["lr_direct_callsite"], 1)
        self.assertEqual(score["lr_springboard_callsite"], 1)
        self.assertEqual(score["weighted_score"], 9)
        self.assertEqual(no_slide["categories"], {"pre_text_no_slide": 1, "core_text_no_slide": 1, "post_etext_no_slide": 1})
        self.assertEqual(under_slide["categories"], {"function_and_callsite": 2, "function_range": 1})
        self.assertEqual(under_slide["preview"][0]["callsite_kind"], ["direct"])

    def test_ropp_decode_audit_tracks_unique_and_no_match_pairs(self):
        callsites = {
            BASE + 0x1004: [v2215.Callsite(BASE + 0x1004, BASE + 0x1000, "direct", BASE + 0x1800, "target")]
        }
        slide = 0x80000
        runtime_return = BASE + 0x1004 + slide
        key = 0x123456789ABCDEF0
        samples = [
            {"pid": 1, "comm": "one", "fp_slot_raw_lr": runtime_return ^ key, "fp2_slot_raw_lr": runtime_return ^ key},
            {"pid": 2, "comm": "miss", "fp_slot_raw_lr": (runtime_return ^ key), "fp2_slot_raw_lr": (runtime_return ^ key) ^ 0x40},
            {"pid": 3, "comm": "skip", "fp_slot_raw_lr": 0, "fp2_slot_raw_lr": runtime_return ^ key},
        ]

        audit = v2215.ropp_decode_audit(samples, slide, callsites)

        self.assertEqual(audit["tested_samples"], 2)
        self.assertEqual(audit["unique_samples"], 1)
        self.assertEqual(audit["no_match_samples"], 1)
        self.assertEqual(audit["ambiguous_samples"], 0)
        self.assertFalse(audit["accepted_exact_unwind"])
        self.assertEqual(audit["candidate_count_min"], 0)
        self.assertEqual(audit["candidate_count_max"], 1)
        self.assertEqual(audit["preview"][0]["examples"][0]["key"], v2215.hex64(key))


class ReportRendering(unittest.TestCase):
    def test_render_report_includes_decisions_rankings_discriminators_and_safety(self):
        result = {
            "decision": "v2215-test",
            "out_dir": "workspace/private/runs/kernel/v2215-test",
            "inputs": {
                "v2214_summary": "summary.json",
                "system_map": "System.map",
                "kernel_raw": "kernel.raw",
            },
            "p0_slide": {
                "pc_count": 2,
                "lr_count": 2,
                "text_start": v2215.hex64(BASE),
                "text_end": v2215.hex64(BASE + 0x1000),
                "exact_threshold": 1,
                "exact_slide_accepted": False,
                "exact_reason": "ranked only",
                "best": {"slide_hex": "0x80000", "weighted_score": 7, "pc_func": 2, "lr_func": 2, "lr_callsite": 1},
                "top_candidates": [
                    {
                        "slide_hex": "0x80000",
                        "weighted_score": 7,
                        "pc_func": 2,
                        "lr_func": 2,
                        "lr_callsite": 1,
                        "lr_direct_callsite": 1,
                        "lr_springboard_callsite": 0,
                        "top_symbols": [("target", 2)],
                    }
                ],
            },
            "p1_generated_text": {
                "pc_no_slide": {"categories": {"core_text_no_slide": 1}, "top_nearest_symbols": [("_text", 1)]},
                "lr_no_slide": {"categories": {"post_etext_no_slide": 1}, "top_nearest_symbols": [("_etext", 1)]},
                "pc_under_slide": {"categories": {"function_range": 2}},
                "lr_under_slide": {"categories": {"function_and_callsite": 1}},
            },
            "p2_ropp_decode": {
                "accepted_exact_unwind": False,
                "tested_samples": 1,
                "unique_samples": 0,
                "ambiguous_samples": 1,
                "no_match_samples": 0,
                "candidate_count_min": 2,
                "candidate_count_median": 2,
                "candidate_count_max": 2,
                "reason": "ambiguous",
                "preview": [
                    {
                        "sample_index": 0,
                        "pid": 42,
                        "comm": "worker",
                        "candidate_count": 2,
                        "encoded_1": "0x1",
                        "encoded_2": "0x2",
                    }
                ],
            },
            "safety": {
                "host_only": True,
                "live_device_access": False,
                "flash_reboot": False,
            },
        }

        report = v2215.render_report(result)

        self.assertIn("# Native Init V2215 Perf Regs ROPP/JOPP Classifier", report)
        self.assertIn("- Decision: `v2215-test`", report)
        self.assertIn("| 1 | `0x80000` | 7 | 2 | 2 | 1 | 1 | 0 | target:2 |", report)
        self.assertIn("- No-slide LR categories: `{'post_etext_no_slide': 1}`", report)
        self.assertIn("| 0 | 42 | `worker` | 2 | `0x1` | `0x2` |", report)
        self.assertIn("- host_only: `true`", report)


if __name__ == "__main__":
    unittest.main()
