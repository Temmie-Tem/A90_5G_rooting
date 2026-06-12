"""Regression tests for a90_kernel_v2246_post_fwready_tail_symbol_source_map."""

import argparse
import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from _loader import load_revalidation

v2246 = load_revalidation("a90_kernel_v2246_post_fwready_tail_symbol_source_map")


DEFINITION_LINES = {
    "_request_firmware": "_request_firmware(",
    "request_firmware": "request_firmware(",
    "qdf_file_read": "QDF_STATUS qdf_file_read(",
    "qdf_ini_parse": "QDF_STATUS qdf_ini_parse(",
    "cfg_parse": "QDF_STATUS cfg_parse(",
    "hdd_context_create": "struct hdd_context *hdd_context_create(",
    "wlan_hdd_pld_probe": "static int wlan_hdd_pld_probe(",
}


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_stock_map(path: Path, missing: set[str] | None = None):
    missing = missing or set()
    lines = [
        "not-an-address T ignored",
        "ffffff80080fff00 D non_text_data",
    ]
    base = 0xFFFFFF8008100000
    for index, symbol in enumerate(v2246.TARGET_SYMBOLS):
        if symbol in missing:
            continue
        symbol_type = "t" if index % 2 else "T"
        lines.append(f"{base + index * 0x100:016x} {symbol_type} {symbol}")
    write_text(path, "\n".join(lines) + "\n")


def write_sources(source_root: Path, missing: set[str] | None = None):
    missing = missing or set()
    grouped: dict[Path, list[str]] = defaultdict(list)
    for symbol, (rel_path, _) in v2246.SOURCE_HINTS.items():
        if symbol in missing:
            continue
        grouped[Path(rel_path)].append("// filler")
        grouped[Path(rel_path)].append(DEFINITION_LINES[symbol])
    for rel_path, lines in grouped.items():
        write_text(source_root / rel_path, "\n".join(lines) + "\n")


def v2245_summary(symbols: list[str] | None = None):
    symbols = symbols or list(v2246.TARGET_SYMBOLS)
    stack_functions = [
        "noise_without_bracket",
        "[<0>] unrelated_symbol+0x0/0x10",
    ]
    for index, symbol in enumerate(symbols):
        stack_functions.append(f"[<{index}>] {symbol}+0x{index + 1:x}/0x40")
    return {
        "runs": {
            "v2233": {
                "target_stack_samples": [
                    {
                        "stack_functions": stack_functions,
                    }
                ]
            }
        }
    }


class BasicParsers(unittest.TestCase):
    def test_parse_int_hex_accepts_none_and_hex_only(self):
        self.assertIsNone(v2246.parse_int_hex(None))
        self.assertEqual(v2246.parse_int_hex("10"), 16)
        self.assertEqual(v2246.parse_int_hex("0x10"), 16)
        with self.assertRaises(ValueError):
            v2246.parse_int_hex("not-hex")

    def test_load_text_symbols_filters_non_text_and_adds_next_symbol_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "System.map"
            write_text(
                path,
                "\n".join([
                    "nothex T invalid",
                    "0000000000001000 D data_symbol",
                    "0000000000001100 T first_text",
                    "0000000000001200 w weak_text",
                    "0000000000001400 t local_text",
                ])
                + "\n",
            )

            symbols = v2246.load_text_symbols(path)

        self.assertEqual([row["name"] for row in symbols], ["first_text", "weak_text", "local_text"])
        self.assertEqual(symbols[0]["next_symbol"], "weak_text")
        self.assertEqual(symbols[0]["next_delta"], 0x100)
        self.assertEqual(symbols[0]["next_delta_hex"], "0x100")
        self.assertIsNone(symbols[-1]["next_symbol"])

    def test_symbol_index_keeps_first_duplicate(self):
        rows = [
            {"name": "dup", "address_hex": "0x1"},
            {"name": "dup", "address_hex": "0x2"},
        ]

        index = v2246.symbol_index(rows)

        self.assertEqual(index["dup"]["address_hex"], "0x1")


class StackAndSourceMapping(unittest.TestCase):
    def test_extract_observed_stack_keeps_target_symbols_with_offsets(self):
        payload = v2245_summary(["request_firmware", "qdf_file_read"])

        observed = v2246.extract_observed_stack(payload)

        self.assertEqual([row["symbol"] for row in observed], ["request_firmware", "qdf_file_read"])
        self.assertEqual(observed[0]["ordinal"], 2)
        self.assertEqual(observed[0]["offset"], 1)
        self.assertEqual(observed[0]["offset_hex"], "0x1")
        self.assertEqual(observed[0]["stack_reported_size"], 0x40)

    def test_extract_observed_stack_tolerates_missing_runs(self):
        self.assertEqual(v2246.extract_observed_stack({}), [])

    def test_find_source_definition_reports_found_missing_file_missing_pattern_and_no_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            rel_path, _ = v2246.SOURCE_HINTS["cfg_parse"]
            write_text(source_root / rel_path, "int not_the_target(void)\nQDF_STATUS cfg_parse(\n")

            found = v2246.find_source_definition(source_root, "cfg_parse")
            no_hint = v2246.find_source_definition(source_root, "not_a_target")
            missing_file = v2246.find_source_definition(source_root, "qdf_file_read")
            write_text(source_root / v2246.SOURCE_HINTS["qdf_file_read"][0], "int other(void)\n")
            missing_pattern = v2246.find_source_definition(source_root, "qdf_file_read")

        self.assertTrue(found["found"])
        self.assertEqual(found["line"], 2)
        self.assertEqual(no_hint["reason"], "no-source-hint")
        self.assertEqual(missing_file["reason"], "source-file-missing")
        self.assertEqual(missing_pattern["reason"], "definition-pattern-missing")

    def test_build_rows_marks_observed_map_source_and_offset_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            write_sources(source_root)
            symbols = {
                "request_firmware": {
                    "address_hex": "0xffffff8008100100",
                    "type": "T",
                    "next_symbol": "next",
                    "next_delta_hex": "0x20",
                }
            }
            observed = [
                {
                    "symbol": "request_firmware",
                    "ordinal": 3,
                    "offset": 0x10,
                    "stack_reported_size": 0x40,
                },
                {
                    "symbol": "qdf_file_read",
                    "ordinal": 4,
                    "offset": 0x80,
                    "stack_reported_size": 0x40,
                },
            ]

            rows = v2246.build_rows(observed, symbols, source_root)

        by_symbol = {row["symbol"]: row for row in rows}
        self.assertTrue(by_symbol["request_firmware"]["observed_in_v2245_stack"])
        self.assertTrue(by_symbol["request_firmware"]["stock_map_found"])
        self.assertTrue(by_symbol["request_firmware"]["source_found"])
        self.assertTrue(by_symbol["request_firmware"]["offset_within_stack_reported_size"])
        self.assertFalse(by_symbol["qdf_file_read"]["stock_map_found"])
        self.assertFalse(by_symbol["qdf_file_read"]["offset_within_stack_reported_size"])
        self.assertIn("per-boot exact-slide", by_symbol["request_firmware"]["next_live_sampler_use"])


class SummaryBuilder(unittest.TestCase):
    def make_args(self, root: Path, missing_map=None, missing_source=None, symbols=None):
        v2245_path = root / "v2245.json"
        stock_map = root / "System.map"
        source_root = root / "source"
        write_json(v2245_path, v2245_summary(symbols))
        write_stock_map(stock_map, set(missing_map or []))
        write_sources(source_root, set(missing_source or []))
        return argparse.Namespace(
            label="unit",
            v2245_summary=v2245_path,
            stock_map=stock_map,
            source_root=source_root,
        )

    def test_build_summary_passes_when_stack_map_and_source_cover_all_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.make_args(root)
            out_dir = root / "out"
            out_dir.mkdir()

            summary = v2246.build_summary(args, out_dir)
            inventory = json.loads(Path(summary["inventory"]["path"]).read_text(encoding="utf-8"))

        self.assertTrue(summary["pass"])
        self.assertEqual(summary["decision"], "v2246-post-fwready-tail-symbol-source-map-pass")
        self.assertEqual(summary["target_symbol_count"], len(v2246.TARGET_SYMBOLS))
        self.assertEqual(summary["observed_stack_symbol_count"], len(v2246.TARGET_SYMBOLS))
        self.assertEqual(summary["missing_or_unmapped_symbols"], [])
        self.assertEqual(summary["offset_mismatches"], [])
        self.assertFalse(summary["inventory"]["raw_helper_result_published"])
        self.assertEqual(len(inventory["rows"]), len(v2246.TARGET_SYMBOLS))
        self.assertIn("Public-safe derived inventory", inventory["warning"])

    def test_build_summary_requests_review_for_missing_source_or_bad_stack_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.make_args(root, missing_source={"cfg_parse"})
            payload = v2245_summary()
            payload["runs"]["v2233"]["target_stack_samples"][0]["stack_functions"][-1] = (
                "[<x>] wlan_hdd_pld_probe+0x80/0x40"
            )
            write_json(args.v2245_summary, payload)
            out_dir = root / "out"
            out_dir.mkdir()

            summary = v2246.build_summary(args, out_dir)

        self.assertFalse(summary["pass"])
        self.assertEqual(summary["decision"], "v2246-post-fwready-tail-symbol-source-map-review-needed")
        self.assertIn("cfg_parse", summary["missing_or_unmapped_symbols"])
        self.assertIn("wlan_hdd_pld_probe", summary["offset_mismatches"])


if __name__ == "__main__":
    unittest.main()
