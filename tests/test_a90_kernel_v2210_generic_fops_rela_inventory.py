"""Regression tests for a90_kernel_v2210_generic_fops_rela_inventory."""

import argparse
import json
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_revalidation

v2210 = load_revalidation("a90_kernel_v2210_generic_fops_rela_inventory")


class ScalarSymbolAndSourceHelpers(unittest.TestCase):
    def test_parse_int_and_hex_formatters(self):
        self.assertEqual(v2210.parse_int(7), 7)
        self.assertEqual(v2210.parse_int("42"), 42)
        self.assertEqual(v2210.parse_int("0x2a"), 42)
        self.assertEqual(v2210.hex64(-1), "0xffffffffffffffff")
        self.assertEqual(v2210.hex_signed(-0x20), "-0x20")
        self.assertEqual(v2210.hex_signed(0x20), "0x20")

    def test_parse_system_map_and_build_symbol_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "System.map"
            path.write_text(
                "not-hex T ignored\n"
                "0000000000003000 T beta\n"
                "0000000000001000 T alpha\n"
                "0000000000002000 W alpha\n",
                encoding="utf-8",
            )

            symbols = v2210.parse_system_map(path)
            index = v2210.build_symbol_index(symbols)

        self.assertEqual([symbol.address for symbol in symbols], [0x1000, 0x2000, 0x3000])
        self.assertEqual([symbol.name for symbol in symbols], ["alpha", "alpha", "beta"])
        self.assertEqual(index["alpha"], 0x1000)
        self.assertEqual(index["beta"], 0x3000)

    def test_config_stripping_macros_offsets_and_initializers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoconf = root / "autoconf.h"
            autoconf.write_text("#define CONFIG_MMU 1\n", encoding="utf-8")
            fs_h = root / "fs.h"
            fs_h.write_text(
                "struct file_operations {\n"
                "    struct module *owner;\n"
                "    loff_t (*llseek)(void);\n"
                "#ifdef CONFIG_MMU\n"
                "    int (*mmap)(void);\n"
                "#else\n"
                "    int (*mmap_compat)(void);\n"
                "#endif\n"
                "    ssize_t (*read)(void);\n"
                "};\n",
                encoding="utf-8",
            )
            source = root / "drivers" / "char"
            source.mkdir(parents=True)
            mem_c = source / "mem.c"
            mem_c.write_text(
                "#define redirected read_null\n"
                "static const struct file_operations null_fops = {\n"
                "    .llseek = null_lseek,\n"
                "    .read = redirected,\n"
                "};\n"
                "static const struct file_operations empty_fops = {\n"
                "};\n",
                encoding="utf-8",
            )

            config = v2210.parse_config_symbols(autoconf)
            stripped = v2210.strip_inactive_config_blocks(fs_h.read_text(), config)
            offsets = v2210.parse_file_operations_offsets(fs_h, config)
            macros = v2210.parse_macros(mem_c.read_text())
            initializers = v2210.parse_fops_initializers(root, config)

        self.assertEqual(config, {"CONFIG_MMU"})
        self.assertIn("mmap", stripped)
        self.assertNotIn("mmap_compat", stripped)
        self.assertEqual(offsets, {"owner": 0, "llseek": 8, "mmap": 16, "read": 24})
        self.assertEqual(macros, {"redirected": "read_null"})
        self.assertEqual(v2210.resolve_alias("redirected", macros), "read_null")
        self.assertEqual(v2210.resolve_alias("unknown", macros), "unknown")
        self.assertEqual(len(initializers), 1)
        self.assertEqual(initializers[0].name, "null_fops")
        self.assertEqual(initializers[0].fields, {"llseek": "null_lseek", "read": "read_null"})


class RelaHelpers(unittest.TestCase):
    def test_load_kernel_raw_accepts_wrapped_and_rejects_truncated(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "raw"
            raw_path.write_bytes(b"kernel")
            wrapped = Path(tmp) / "wrapped"
            wrapped.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 6) + b"kernel")
            truncated = Path(tmp) / "truncated"
            truncated.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 10) + b"short")

            self.assertEqual(v2210.load_kernel_raw(raw_path), b"kernel")
            self.assertEqual(v2210.load_kernel_raw(wrapped), b"kernel")
            with self.assertRaises(ValueError):
                v2210.load_kernel_raw(truncated)

    def test_load_synthetic_base_and_kernel_va_classifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "stock.json"
            meta.write_text(json.dumps({"synthetic_base": "0xffff000000000000"}), encoding="utf-8")

            self.assertEqual(v2210.load_synthetic_base(meta), 0xFFFF000000000000)
        self.assertTrue(v2210.looks_like_kernel_va(v2210.KERNEL_VA_MIN))
        self.assertTrue(v2210.looks_like_kernel_va(v2210.KERNEL_VA_MAX))
        self.assertFalse(v2210.looks_like_kernel_va(v2210.KERNEL_VA_MIN - 1))

    def test_stock_rela_detection_discovery_and_elf_parsing(self):
        synthetic_base = 0xFFFF000000000000
        raw = bytearray(4 + 2 * 24 + 4)
        for index, addend in enumerate([v2210.KERNEL_VA_MIN + 0x1000, 0]):
            struct.pack_into(
                "<QQQ",
                raw,
                4 + index * 24,
                v2210.KERNEL_VA_MIN + 0x8000 + index * 0x10,
                v2210.RELA_INFO_RELATIVE,
                addend,
            )

        self.assertFalse(v2210.is_stock_rela_record(bytes(raw), 0))
        self.assertTrue(v2210.is_stock_rela_record(bytes(raw), 4))
        rela_run = v2210.discover_stock_rela(bytes(raw), synthetic_base)
        self.assertEqual(rela_run["start_vma"], synthetic_base + 4)
        self.assertEqual(rela_run["count"], 2)
        self.assertEqual(rela_run["entries"][1].r_addend, 0)
        with self.assertRaises(RuntimeError):
            v2210.discover_stock_rela(b"\x00" * 96, synthetic_base)

        with tempfile.TemporaryDirectory() as tmp:
            vmlinux = Path(tmp) / "vmlinux"
            payload = bytearray(0x80)
            struct.pack_into("<QQq", payload, 0x40, 0x9000, v2210.RELA_INFO_RELATIVE, -1)
            vmlinux.write_bytes(payload)
            readelf = SimpleNamespace(stdout="  [ 1] .rela.dyn RELA 0000000000004000 000040 000018 18  A  0   0  8\n")
            with mock.patch.object(v2210.subprocess, "run", return_value=readelf):
                entries = v2210.parse_elf_rela_dyn(vmlinux)

        self.assertEqual(entries[0].location, 0x4000)
        self.assertEqual(entries[0].r_offset, 0x9000)
        self.assertEqual(entries[0].r_addend, 0xFFFFFFFFFFFFFFFF)

    def test_find_clone_base_ranks_unique_best_and_handles_empty(self):
        original = v2210.KERNEL_VA_MIN + 0x1000
        clone = v2210.KERNEL_VA_MIN + 0x1800
        stock_offsets = sorted([clone + 8, clone + 16, v2210.KERNEL_VA_MIN + 0x60000])
        addend_refs = Counter({clone: 3})

        result = v2210.find_clone_base(original, [8, 16], stock_offsets, addend_refs)
        empty = v2210.find_clone_base(original, [8], [], addend_refs)

        self.assertEqual(result["clone_base"], clone)
        self.assertEqual(result["best_count"], 2)
        self.assertEqual(result["base_ref_count"], 3)
        self.assertTrue(result["unique_best"])
        self.assertEqual(result["top_candidates"][0]["delta"], "0x800")
        self.assertIsNone(empty["clone_base"])
        self.assertFalse(empty["unique_best"])


class AnalyzeAndReport(unittest.TestCase):
    def write_inputs(self, root: Path) -> argparse.Namespace:
        synthetic_base = v2210.KERNEL_VA_MIN
        stock_symbols = {
            "null_fops": synthetic_base + 0x1000,
            "short_fops": synthetic_base + 0x1200,
            "null_lseek": synthetic_base + 0x2000,
            "read_null": synthetic_base + 0x2100,
            "write_null": synthetic_base + 0x2200,
        }
        rebuilt_symbols = {
            "null_fops": 0x1000,
            "short_fops": 0x1200,
            "null_lseek": 0x2000,
            "read_null": 0x2100,
            "write_null": 0x2200,
        }
        clone_base = synthetic_base + 0x1800
        landing_addends = {
            "llseek": synthetic_base + 0x3000,
            "read": synthetic_base + 0x3100,
        }
        target_by_field = {
            "llseek": "null_lseek",
            "read": "read_null",
        }
        field_offsets = {"llseek": 8, "read": 16, "write": 24}

        system_map = root / "System.map"
        system_map.write_text(
            "\n".join(f"{address:016x} T {name}" for name, address in stock_symbols.items()) + "\n",
            encoding="utf-8",
        )
        rebuilt_map = root / "rebuilt.System.map"
        rebuilt_map.write_text(
            "\n".join(f"{address:016x} T {name}" for name, address in rebuilt_symbols.items()) + "\n",
            encoding="utf-8",
        )
        autoconf = root / "autoconf.h"
        autoconf.write_text("#define CONFIG_MMU 1\n", encoding="utf-8")
        fs_h = root / "fs.h"
        fs_h.write_text(
            "struct file_operations {\n"
            "    struct module *owner;\n"
            "    loff_t (*llseek)(void);\n"
            "    ssize_t (*read)(void);\n"
            "    ssize_t (*write)(void);\n"
            "};\n",
            encoding="utf-8",
        )
        source_root = root / "source"
        source_root.mkdir()
        mem_c = source_root / "mem.c"
        mem_c.write_text(
            "static const struct file_operations null_fops = {\n"
            "    .llseek = null_lseek,\n"
            "    .read = read_null,\n"
            "};\n"
            "static const struct file_operations short_fops = {\n"
            "    .llseek = null_lseek,\n"
            "};\n",
            encoding="utf-8",
        )

        stock_entries = [
            (clone_base + field_offsets[field], addend)
            for field, addend in landing_addends.items()
        ]
        stock_entries.append((synthetic_base + 0x60000, clone_base))
        raw = bytearray(4 + len(stock_entries) * 24 + 16)
        for index, (slot, addend) in enumerate(stock_entries):
            struct.pack_into("<QQQ", raw, 4 + index * 24, slot, v2210.RELA_INFO_RELATIVE, addend)
        kernel_raw = root / "kernel.raw"
        kernel_raw.write_bytes(raw)
        stock_meta = root / "stock.json"
        stock_meta.write_text(json.dumps({"synthetic_base": synthetic_base}), encoding="utf-8")
        v2208_result = root / "v2208.json"
        v2208_result.write_text(json.dumps({"slide": {"best": 0x80000}}), encoding="utf-8")
        v2209_result = root / "v2209.json"
        v2209_result.write_text(json.dumps({"decision": "v2209-ok", "checks": {"row_count": 2}}), encoding="utf-8")

        rebuilt_entries = []
        for field, target in target_by_field.items():
            rebuilt_entries.append((rebuilt_symbols["null_fops"] + field_offsets[field], rebuilt_symbols[target]))
        vmlinux = root / "vmlinux"
        payload = bytearray(0x100)
        for index, (slot, addend) in enumerate(rebuilt_entries):
            struct.pack_into("<QQq", payload, 0x40 + index * 24, slot, v2210.RELA_INFO_RELATIVE, addend)
        vmlinux.write_bytes(payload)
        self.readelf_stdout = f"  [ 1] .rela.dyn RELA 0000000000004000 000040 {len(rebuilt_entries) * 24:06x} 18  A  0   0  8\n"
        return argparse.Namespace(
            source_root=source_root,
            system_map=system_map,
            kernel_raw=kernel_raw,
            stock_meta=stock_meta,
            v2208_result=v2208_result,
            v2209_result=v2209_result,
            rebuilt_vmlinux=vmlinux,
            rebuilt_system_map=rebuilt_map,
            source_fs_h=fs_h,
            autoconf=autoconf,
        )

    def test_analyze_builds_generic_high_confidence_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.write_inputs(Path(tmp))
            with mock.patch.object(v2210.subprocess, "run", return_value=SimpleNamespace(stdout=self.readelf_stdout)):
                result = v2210.analyze(args)

        self.assertEqual(result["decision"], "v2210-generic-fops-rela-inventory-built")
        self.assertEqual(result["counts"]["parsed_fops_initializers"], 2)
        self.assertEqual(result["counts"]["high_confidence_objects"], 1)
        self.assertEqual(result["counts"]["high_confidence_semantic_rows"], 2)
        self.assertEqual(result["counts"]["status_counts"]["high_confidence"], 1)
        self.assertEqual(result["counts"]["status_counts"]["too_few_labelled_fields"], 1)
        high = result["high_confidence_examples"][0]
        self.assertEqual(high["name"], "null_fops")
        self.assertEqual(high["clone_base"], v2210.hex64(v2210.KERNEL_VA_MIN + 0x1800))
        read_row = next(row for row in high["semantic_rows"] if row["field"] == "read")
        self.assertEqual(read_row["target"], "read_null")
        self.assertEqual(read_row["stock_slot"], v2210.hex64(v2210.KERNEL_VA_MIN + 0x1810))
        self.assertEqual(read_row["runtime_pointer"], v2210.hex64(v2210.KERNEL_VA_MIN + 0x3100 + 0x80000))
        self.assertTrue(read_row["rebuilt_matches_label"])
        self.assertTrue(result["safety"]["host_only"])

    def test_render_table_and_markdown_escape_and_summarize(self):
        table = v2210.render_table(["A"], [["x|y"]])
        self.assertIn("x\\|y", table)

        result = {
            "decision": "v2210-generic-fops-rela-inventory-built",
            "reason": "built",
            "slide": {"runtime_rela_slide_hex": "0x80000"},
            "counts": {
                "parsed_fops_initializers": 1,
                "high_confidence_objects": 1,
                "high_confidence_semantic_rows": 2,
                "status_counts": {"high_confidence": 1},
                "clone_delta_counts": {"0x800": 1},
            },
            "high_confidence_examples": [
                {
                    "name": "null_fops",
                    "clone_delta": "0x800",
                    "labelled_field_count": 2,
                    "source_path": "source/mem.c",
                    "semantic_rows": [
                        {"field": "llseek", "target": "null_lseek"},
                        {"field": "read", "target": "read_null"},
                    ],
                }
            ],
            "v2209_anchor": {"decision": "v2209-ok"},
            "stock_rela": {"start_vma": "0x1", "end_vma": "0x2", "count": 3},
            "safety": {"host_only": True, "live_device_access": False},
            "inputs": {
                "v2209_result": "v2209.json",
                "v2208_result": "v2208.json",
                "kernel_raw": "kernel.raw",
                "source_root": "source",
            },
        }
        report = v2210.render_markdown(result)

        self.assertIn("# Native Init V2210 Generic Fops RELA Inventory", report)
        self.assertIn("- Decision: `v2210-generic-fops-rela-inventory-built`", report)
        self.assertIn("| `null_fops` | `0x800` | 2 | source/mem.c | llseek→null_lseek, read→read_null |", report)
        self.assertIn("- host_only: `true`", report)


if __name__ == "__main__":
    unittest.main()
