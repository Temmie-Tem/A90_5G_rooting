import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1_static_audit.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("s22plus_fyg8_r4w1_audit_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R4W1StaticAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def write_configs(self, stock_lines, generated_lines):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        stock = root / "stock"
        generated = root / "generated"
        stock.write_text("\n".join(stock_lines) + "\n", encoding="ascii")
        generated.write_text("\n".join(generated_lines) + "\n", encoding="ascii")
        return temporary, stock, generated

    def test_config_accepts_only_witness_delta(self):
        common = ["CONFIG_LTO_CLANG_FULL=y", "# CONFIG_LTO_CLANG_THIN is not set"]
        temporary, stock, generated = self.write_configs(
            common,
            [*common, "CONFIG_S22PLUS_FYG8_RETAINED_WITNESS=y"],
        )
        self.addCleanup(temporary.cleanup)
        result = self.module.compare_r4_configs(stock, generated)
        self.assertTrue(result["verified"])
        self.assertTrue(result["witness_exact"])

    def test_config_rejects_security_delta(self):
        common = ["CONFIG_LTO_CLANG_FULL=y", "# CONFIG_LTO_CLANG_THIN is not set"]
        temporary, stock, generated = self.write_configs(
            [*common, "CONFIG_RKP=y"],
            [
                *common,
                "# CONFIG_RKP is not set",
                "CONFIG_S22PLUS_FYG8_RETAINED_WITNESS=y",
            ],
        )
        self.addCleanup(temporary.cleanup)
        result = self.module.compare_r4_configs(stock, generated)
        self.assertFalse(result["verified"])
        self.assertEqual(result["unexpected_deltas"][0]["key"], "CONFIG_RKP")

    def test_full_symvers_requires_exact_mapping(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            baseline = root / "baseline"
            candidate = root / "candidate"
            row = "0x12345678\tfoo\tvmlinux\tEXPORT_SYMBOL\n"
            baseline.write_text(row, encoding="ascii")
            candidate.write_text(row, encoding="ascii")
            self.assertTrue(
                self.module.compare_full_symvers(baseline, candidate)["verified"]
            )
            candidate.write_text(
                row + "0x87654321\tbar\tvmlinux\tEXPORT_SYMBOL\n",
                encoding="ascii",
            )
            result = self.module.compare_full_symvers(baseline, candidate)
            self.assertFalse(result["verified"])
            self.assertEqual(result["added_count"], 1)

    def test_build_gate_rejects_wrong_patch(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "result.json"
            data = {
                "schema": self.module.r4_build.SCHEMA,
                "lto_mode": "full",
                "returncode": 0,
                "r4w1_build_pass": True,
                "provenance": {"source_overlay": {"verified": True}},
                "r4w1_patch_contract": {"verdict": self.module.patch_check.VERDICT},
                "source_delta": {"patch_sha256": "0" * 64, "verified": True},
                "output_gate": {"verified": True},
                "module_gate": {"verified": True},
                "kernel_banner_gate": {"verified": True},
                "witness_output_gate": {"verified": True},
                "timestamp_control_runtime": {
                    "applied": True,
                    "restored": True,
                    "patched_content_unchanged": True,
                    "restored_sha256": "a",
                    "original_sha256": "a",
                },
                "kmi_path_control_runtime": {
                    "applied": True,
                    "restored": True,
                    "patched_content_unchanged": True,
                    "restored_sha256": self.module.r4_build.BUILD_SH_SHA256,
                    "original_sha256": self.module.r4_build.BUILD_SH_SHA256,
                },
            }
            path.write_text(json.dumps(data), encoding="ascii")
            self.assertFalse(self.module.audit_build_result(path)["verified"])


if __name__ == "__main__":
    unittest.main()
