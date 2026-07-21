import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ELF_SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1d_elf_audit.py"
)
STATIC_SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1d_static_audit.py"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R4W1DStaticAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.elf = load_module("s22plus_fyg8_r4w1d_elf_tested", ELF_SCRIPT)
        cls.static = load_module("s22plus_fyg8_r4w1d_static_tested", STATIC_SCRIPT)

    def witness_rows(self):
        base = 0x100000
        return [
            (index, base + index * 4, word)
            for index, word in enumerate(self.elf.WITNESS_WORDS)
        ]

    def test_contiguous_backfill_matcher_accepts_exact_words(self):
        rows = self.witness_rows()
        successors, _ = self.elf.engine.build_cfg(rows)
        result = self.elf.find_contiguous_backfill_chains(
            instructions=rows,
            successors=successors,
            witness_index=0,
            marker_reference={
                "index": 32,
                "consumer_index": 35,
                "register": 14,
                "pc": rows[32][1],
            },
            memstart_reference={
                "index": 0,
                "producer_pc": rows[0][1] - 4,
                "base_register": 22,
                "destination": 8,
                "width": 64,
            },
            memcpy_address=0xDEADBEEF,
            marker_size=45,
        )
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["idx_written"])
        self.assertEqual(result[0]["idx_store_candidates"], [])
        self.assertTrue(result[0]["gates"]["no_memcpy_call"])
        self.assertTrue(result[0]["gates"]["no_head_idx_store"])
        self.assertTrue(all(result[0]["gates"].values()))

    def test_contiguous_backfill_matcher_rejects_semantic_mutation(self):
        for offset in (10, 16, 36, 42, 46):
            with self.subTest(offset=offset):
                rows = self.witness_rows()
                index, pc, word = rows[offset]
                rows[offset] = (index, pc, word ^ 1)
                successors, _ = self.elf.engine.build_cfg(rows)
                self.assertEqual(
                    self.elf.find_contiguous_backfill_chains(
                        instructions=rows,
                        successors=successors,
                        witness_index=0,
                        marker_reference={
                            "index": 32,
                            "consumer_index": 35,
                            "register": 14,
                            "pc": rows[32][1],
                        },
                        memstart_reference={
                            "index": 0,
                            "producer_pc": rows[0][1] - 4,
                            "base_register": 22,
                            "destination": 8,
                            "width": 64,
                        },
                        memcpy_address=0xDEADBEEF,
                        marker_size=45,
                    ),
                    [],
                )

    def test_config_accepts_only_compact_witness_delta(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            stock = root / "stock"
            generated = root / "generated"
            common = [
                "CONFIG_LTO_CLANG_FULL=y",
                "# CONFIG_LTO_CLANG_THIN is not set",
                *(f"{key}=y" for key in self.static.CRITICAL_SECURITY_CONFIGS),
            ]
            stock.write_text("\n".join(common) + "\n", encoding="ascii")
            generated.write_text(
                "\n".join([*common, f"{self.static.contract.CONFIG}=y"]) + "\n",
                encoding="ascii",
            )
            result = self.static.compare_r4w1d_configs(stock, generated)
            self.assertTrue(result["verified"])
            self.assertTrue(result["witness_exact"])

    def test_build_gate_reads_r4w1d_contract_fields(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "result.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": self.static.r4w1d_build.SCHEMA,
                        "r4w1d_build_pass": True,
                        "r4w1d_witness_contract": {
                            "verdict": self.static.contract.VERDICT
                        },
                        "source_delta": {
                            "patch_sha256": "0" * 64,
                            "verified": True,
                        },
                    }
                ),
                encoding="ascii",
            )
            result = self.static.audit_build_result(path)
            self.assertEqual(result["r4w1d_build_pass"], True)
            self.assertEqual(
                result["patch_contract_verdict"], self.static.contract.VERDICT
            )
            self.assertFalse(result["verified"])

    def test_contract_bindings_restore_base_engine_globals(self):
        elf_expected = self.elf.engine.EXPECTED_KERNEL_INIT_SHA256
        static_schema = self.static.engine.SCHEMA
        with self.elf._bind_engine_contract():
            self.assertEqual(
                self.elf.engine.EXPECTED_KERNEL_INIT_SHA256,
                self.elf.EXPECTED_KERNEL_INIT_SHA256,
            )
        with self.static._bind_engine_contract():
            self.assertEqual(self.static.engine.SCHEMA, self.static.SCHEMA)
            self.assertEqual(
                self.static.engine.BUILD_PASS_FIELD, "r4w1d_build_pass"
            )
        self.assertEqual(
            self.elf.engine.EXPECTED_KERNEL_INIT_SHA256, elf_expected
        )
        self.assertEqual(self.static.engine.SCHEMA, static_schema)


if __name__ == "__main__":
    unittest.main()
