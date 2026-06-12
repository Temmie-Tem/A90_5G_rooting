"""Regression tests for a90_kernel_v2208_rela_fops_discriminator."""

import argparse
import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_revalidation

v2208 = load_revalidation("a90_kernel_v2208_rela_fops_discriminator")


class ScalarSymbolAndRawHelpers(unittest.TestCase):
    def test_parse_int_and_hex_formatters(self):
        self.assertEqual(v2208.parse_int(7), 7)
        self.assertEqual(v2208.parse_int("42"), 42)
        self.assertEqual(v2208.parse_int("0x2a"), 42)
        self.assertEqual(v2208.hex64(-1), "0xffffffffffffffff")
        self.assertEqual(v2208.hex_signed(-0x20), "-0x20")
        self.assertEqual(v2208.hex_signed(0x20), "0x20")

    def test_parse_system_map_build_index_and_nearest_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "System.map"
            path.write_text(
                "not-hex T ignored\n"
                "0000000000003000 T beta\n"
                "0000000000001000 T alpha\n"
                "0000000000002000 W alpha\n",
                encoding="utf-8",
            )

            symbols = v2208.parse_system_map(path)
            index = v2208.build_symbol_index(symbols)
            addresses = [symbol.address for symbol in symbols]
            nearest = v2208.nearest_symbol(symbols, addresses, 0x2100)

        self.assertEqual([symbol.address for symbol in symbols], [0x1000, 0x2000, 0x3000])
        self.assertEqual(index["alpha"], 0x1000)
        self.assertEqual(nearest["symbol"], "alpha")
        self.assertEqual(nearest["kind"], "W")
        self.assertEqual(nearest["offset"], 0x100)
        self.assertEqual(nearest["offset_hex"], "0x100")
        self.assertIsNone(v2208.nearest_symbol(symbols, addresses, 0x0FFF))

    def test_load_kernel_raw_accepts_wrapped_and_rejects_truncated(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "raw"
            raw_path.write_bytes(b"kernel")
            wrapped = Path(tmp) / "wrapped"
            wrapped.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 6) + b"kernel")
            truncated = Path(tmp) / "truncated"
            truncated.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 10) + b"short")

            self.assertEqual(v2208.load_kernel_raw(raw_path), b"kernel")
            self.assertEqual(v2208.load_kernel_raw(wrapped), b"kernel")
            with self.assertRaises(ValueError):
                v2208.load_kernel_raw(truncated)

    def test_load_synthetic_base_and_kernel_va_classifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "stock.json"
            meta.write_text(json.dumps({"synthetic_base": "0xffff000000000000"}), encoding="utf-8")

            self.assertEqual(v2208.load_synthetic_base(meta), 0xFFFF000000000000)
        self.assertTrue(v2208.looks_like_kernel_va(v2208.KERNEL_VA_MIN))
        self.assertTrue(v2208.looks_like_kernel_va(v2208.KERNEL_VA_MAX))
        self.assertFalse(v2208.looks_like_kernel_va(v2208.KERNEL_VA_MIN - 1))


class RelaHelpers(unittest.TestCase):
    def test_stock_rela_record_detection_and_discovery_accepts_4_byte_alignment(self):
        synthetic_base = 0xFFFF000000000000
        raw = bytearray(4 + 3 * 24 + 4)
        addends = [v2208.KERNEL_VA_MIN + 0x1000, v2208.KERNEL_VA_MIN + 0x2000, 0]
        for index, addend in enumerate(addends):
            struct.pack_into(
                "<QQQ",
                raw,
                4 + index * 24,
                v2208.KERNEL_VA_MIN + 0x8000 + index * 0x10,
                v2208.RELA_INFO_RELATIVE,
                addend,
            )

        self.assertFalse(v2208.is_stock_rela_record(bytes(raw), 0))
        self.assertTrue(v2208.is_stock_rela_record(bytes(raw), 4))
        rela_run = v2208.discover_stock_rela(bytes(raw), synthetic_base)

        self.assertEqual(rela_run["start_offset"], 4)
        self.assertEqual(rela_run["count"], 3)
        self.assertEqual(rela_run["entries"][0].location, synthetic_base + 4)
        self.assertEqual(rela_run["entries"][2].r_addend, 0)

    def test_discover_stock_rela_raises_without_records(self):
        with self.assertRaises(RuntimeError):
            v2208.discover_stock_rela(b"\x00" * 96, 0xFFFF000000000000)

    def test_build_rela_addend_index_and_score_slides(self):
        entries = [
            v2208.RelaEntry(0x10, 0x20, v2208.RELA_INFO_RELATIVE, 0x1000),
            v2208.RelaEntry(0x30, 0x40, v2208.RELA_INFO_RELATIVE, 0x1000),
            v2208.RelaEntry(0x50, 0x60, v2208.RELA_INFO_RELATIVE, 0x2000),
        ]

        index = v2208.build_rela_addend_index(entries)
        scored = v2208.score_slides([0x81000, 0x82000, 0x123456], [entry.r_addend for entry in entries])

        self.assertEqual(len(index[0x1000]), 2)
        self.assertEqual(scored[0], {"slide": 0x80000, "slide_hex": "0x80000", "matched_fields": 2})

    def test_live_value_reads_probe_summary_decimal_or_hex(self):
        self.assertEqual(v2208.live_value({"probe": {"summary": {"fd0": "0x20"}}}, "fd0"), 0x20)
        self.assertEqual(v2208.live_value({"probe": {"summary": {"fd0": "32"}}}, "fd0"), 32)

    def test_parse_elf_rela_dyn_uses_readelf_section_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            vmlinux = Path(tmp) / "vmlinux"
            payload = bytearray(0x80)
            struct.pack_into("<QQq", payload, 0x40, 0x9000, v2208.RELA_INFO_RELATIVE, -1)
            vmlinux.write_bytes(payload)
            readelf = SimpleNamespace(stdout="  [ 1] .rela.dyn RELA 0000000000004000 000040 000018 18  A  0   0  8\n")

            with mock.patch.object(v2208.subprocess, "run", return_value=readelf):
                entries = v2208.parse_elf_rela_dyn(vmlinux)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].location, 0x4000)
        self.assertEqual(entries[0].r_offset, 0x9000)
        self.assertEqual(entries[0].r_addend, 0xFFFFFFFFFFFFFFFF)


class RebuiltAndSourceHelpers(unittest.TestCase):
    def test_rebuilt_rela_comparison_missing_inputs_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = v2208.rebuilt_rela_comparison(Path(tmp) / "missing-vmlinux", Path(tmp) / "missing-map")

        self.assertFalse(result["available"])
        self.assertEqual(result["rows"], [])

    def test_rebuilt_rela_comparison_maps_member_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vmlinux = root / "vmlinux"
            payload = bytearray(0x80)
            struct.pack_into("<QQq", payload, 0x40, 0x1000 + v2208.FOPS_MEMBER_OFFSETS["llseek"], v2208.RELA_INFO_RELATIVE, 0x2000)
            vmlinux.write_bytes(payload)
            system_map = root / "System.map"
            system_map.write_text(
                "0000000000001000 D null_fops\n"
                "0000000000001100 D zero_fops\n"
                "0000000000002000 T null_lseek\n",
                encoding="utf-8",
            )
            readelf = SimpleNamespace(stdout="  [ 1] .rela.dyn RELA 0000000000004000 000040 000018 18  A  0   0  8\n")

            with mock.patch.object(v2208.subprocess, "run", return_value=readelf):
                result = v2208.rebuilt_rela_comparison(vmlinux, system_map)

        self.assertTrue(result["available"])
        self.assertEqual(result["rela_entry_count"], 1)
        first = result["rows"][0]
        self.assertEqual(first["field"], "fd0_llseek")
        self.assertTrue(first["matches_expected_label"])
        self.assertEqual(result["matched_expected_labels"], 1)

    def test_source_initializer_evidence_extracts_symbol_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mem.c"
            path.write_text(
                "static const struct file_operations null_fops = { .llseek = null_lseek };\n"
                "ssize_t read_null(...) { return 0; }\n",
                encoding="utf-8",
            )
            result = v2208.source_initializer_evidence(path)
            missing = v2208.source_initializer_evidence(Path(tmp) / "missing.c")

        self.assertTrue(result["available"])
        self.assertEqual(result["symbols"]["null_fops"]["line"], 1)
        self.assertEqual(result["symbols"]["read_null"]["line"], 2)
        self.assertIsNone(result["symbols"]["write_null"])
        self.assertFalse(missing["available"])


class AnalyzeAndReport(unittest.TestCase):
    def write_inputs(self, root: Path) -> argparse.Namespace:
        synthetic_base = 0xFFFF000000000000
        system_map = root / "System.map"
        system_map.write_text(
            "\n".join(
                [
                    f"{v2208.KERNEL_VA_MIN + 0x1000:016x} D null_fops",
                    f"{v2208.KERNEL_VA_MIN + 0x1100:016x} D zero_fops",
                    f"{v2208.KERNEL_VA_MIN + 0x2000:016x} T null_lseek",
                    f"{v2208.KERNEL_VA_MIN + 0x2100:016x} T read_null",
                    f"{v2208.KERNEL_VA_MIN + 0x2200:016x} T write_null",
                    f"{v2208.KERNEL_VA_MIN + 0x2300:016x} T read_iter_null",
                    f"{v2208.KERNEL_VA_MIN + 0x2400:016x} T write_iter_null",
                    f"{v2208.KERNEL_VA_MIN + 0x2500:016x} T splice_write_null",
                    f"{v2208.KERNEL_VA_MIN + 0x2600:016x} T read_iter_zero",
                    f"{v2208.KERNEL_VA_MIN + 0x2700:016x} T mmap_zero",
                    f"{v2208.KERNEL_VA_MIN + 0x2800:016x} T get_unmapped_area_zero",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        addends = [v2208.KERNEL_VA_MIN + 0x1000 + index * 0x100 for index, _target in enumerate(v2208.TARGETS)]
        raw = bytearray(4 + len(addends) * 24 + 16)
        for index, addend in enumerate(addends):
            struct.pack_into(
                "<QQQ",
                raw,
                4 + index * 24,
                v2208.KERNEL_VA_MIN + 0x9000 + index * 0x10,
                v2208.RELA_INFO_RELATIVE,
                addend,
            )
        kernel_raw = root / "kernel.raw"
        kernel_raw.write_bytes(raw)
        stock_meta = root / "stock.json"
        stock_meta.write_text(json.dumps({"synthetic_base": synthetic_base}), encoding="utf-8")
        probe_summary = {
            target["field"]: v2208.hex64(addend + 0x80000)
            for target, addend in zip(v2208.TARGETS, addends, strict=True)
        }
        v2206_summary = root / "summary.json"
        v2206_summary.write_text(json.dumps({"probe": {"summary": probe_summary}}), encoding="utf-8")
        source_mem_c = root / "mem.c"
        source_mem_c.write_text("static const struct file_operations null_fops = { .llseek = null_lseek };\n", encoding="utf-8")
        return argparse.Namespace(
            system_map=system_map,
            kernel_raw=kernel_raw,
            stock_meta=stock_meta,
            v2206_summary=v2206_summary,
            rebuilt_vmlinux=root / "missing-vmlinux",
            rebuilt_system_map=root / "missing-map",
            source_mem_c=source_mem_c,
        )

    def test_analyze_resolves_all_targets_with_rela_slide(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.write_inputs(Path(tmp))
            result = v2208.analyze(args)

        self.assertEqual(result["decision"], "v2208-stock-rela-clone-slide-resolves-v2206-members")
        self.assertEqual(result["slide"]["best"], 0x80000)
        self.assertEqual(result["slide"]["matched_targets"], len(v2208.TARGETS))
        self.assertEqual(result["rela_run"]["start_offset"], "0x4")
        self.assertEqual(len(result["object_rows"]), 2)
        self.assertEqual(len(result["member_rows"]), len(v2208.TARGETS) - 2)
        self.assertTrue(result["safety"]["host_only"])
        self.assertFalse(result["safety"]["live_device_access"])

    def test_render_table_escapes_pipes_and_markdown_includes_rela_sections(self):
        table = v2208.render_table(["A", "B"], [["x|y", "z"]])
        self.assertIn("x\\|y", table)

        result = {
            "decision": "v2208-stock-rela-clone-slide-resolves-v2206-members",
            "reason": "resolved",
            "inputs": {
                "system_map": "System.map",
                "kernel_raw": "kernel.raw",
                "v2206_summary": "summary.json",
                "rebuilt_vmlinux": "vmlinux",
            },
            "kernel": {"synthetic_base": "0xffff000000000000"},
            "rela_run": {
                "start_offset": "0x4",
                "start_vma": "0xffff000000000004",
                "end_vma": "0xffff000000000064",
                "count": 5,
                "record_size": 24,
                "alignment_note": "note",
            },
            "slide": {"best_hex": "0x80000", "matched_targets": 1, "total_targets": 1},
            "object_rows": [
                {
                    "field": "fd0_fop",
                    "runtime": "0xffff",
                    "static_addend": "0x1000",
                    "rela_location": "0x10",
                    "rela_r_offset": "0x20",
                    "expected_symbol": "null_fops",
                    "delta_from_expected_hex": "0x0",
                }
            ],
            "member_rows": [
                {
                    "field": "fd0_read",
                    "runtime": "0xffff",
                    "static_addend": "0x2100",
                    "rela_location": "0x30",
                    "expected_symbol": "read_null",
                    "delta_from_expected_hex": "0x0",
                    "addend_nearest": {"symbol": "read_null", "offset_hex": "0x0"},
                }
            ],
            "rebuilt_rela_comparison": {
                "available": True,
                "rela_entry_count": 7,
                "matched_expected_labels": 3,
                "member_row_count": 12,
            },
            "safety": {"host_only": True, "live_device_access": False},
        }
        report = v2208.render_markdown(result)

        self.assertIn("# Native Init V2208 RELA Fops Discriminator", report)
        self.assertIn("- Decision: `v2208-stock-rela-clone-slide-resolves-v2206-members`", report)
        self.assertIn("| `fd0_fop` | `0xffff` | `0x1000` | `0x10` | `0x20` | `null_fops` | `0x0` |", report)
        self.assertIn("| `fd0_read` | `0xffff` | `0x2100` | `0x30` | `read_null` | `0x0` | `read_null`0x0 |", report)
        self.assertIn("- host_only: `true`", report)


if __name__ == "__main__":
    unittest.main()
