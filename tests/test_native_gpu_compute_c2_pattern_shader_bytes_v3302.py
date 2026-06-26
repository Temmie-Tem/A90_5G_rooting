from __future__ import annotations

import unittest

from _loader import load_script


shader_bytes = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_compute_c2_pattern_shader_bytes_v3302.py"
)


class NativeGpuComputeC2PatternShaderBytesV3302Tests(unittest.TestCase):
    def test_shader_byte_verification_passes_and_is_c2_ready(self) -> None:
        result = shader_bytes.run_verification(require_disasm=True)

        self.assertEqual(result["cycle"], "V3302")
        self.assertEqual(result["scope"], "gpu-compute-c2-pattern-shader-byte-materialization")
        self.assertTrue(result["passed"])
        self.assertTrue(result["ready_for_c2_live"])
        self.assertTrue(result["checks"]["shader_binary_sha256_matches"])
        self.assertTrue(result["checks"]["ir3_disasm_contains_expected_ops"])

    def test_materialized_shader_metadata_matches_fd640_assembler_output(self) -> None:
        result = shader_bytes.run_verification(require_disasm=True)
        shader = result["shader"]

        self.assertEqual(shader["gpu_name"], "FD640")
        self.assertEqual(shader["local_size"], [1, 1, 1])
        self.assertEqual(shader["num_bufs"], 1)
        self.assertEqual(shader["buf_sizes"], [16384])
        self.assertEqual(shader["buf_addr_regs"], [252])
        self.assertEqual(shader["instrlen"], 1)
        self.assertEqual(shader["sizedwords"], 32)
        self.assertEqual(shader["size_bytes"], 128)
        self.assertEqual(shader["max_reg"], 0)
        self.assertEqual(shader["max_half_reg"], -1)
        self.assertEqual(shader["constlen"], 4)
        self.assertTrue(shader["mergedregs"])
        self.assertEqual(
            shader["binary_sha256"],
            "9259cd6e225aba4d1e86fb88527494404617b2aaf753c948379ade2edb18a6d1",
        )

    def test_dwords_decode_to_workgroup_id_pattern_store_kernel(self) -> None:
        result = shader_bytes.run_verification(require_disasm=True)
        dwords = result["shader"]["dwords_hex"]
        disasm = "\n".join(result["disasm"]["lines"])

        self.assertEqual(dwords[:10], [
            "0x000000c0",
            "0x200cc000",
            "0x000000c0",
            "0x200cc001",
            "0x00000000",
            "0x00000500",
            "0x01674000",
            "0xc0260000",
            "0x00000000",
            "0x03000000",
        ])
        self.assertIn("mov.u32u32 r0.x, r48.x", disasm)
        self.assertIn("mov.u32u32 r0.y, r48.x", disasm)
        self.assertIn("stib.b.untyped.1d.u32.1.imm r0.x, r0.y, 0", disasm)
        self.assertIn("end", disasm)

    def test_shader_contract_matches_128x128_pattern_samples(self) -> None:
        result = shader_bytes.run_verification(require_disasm=False)
        contract = result["shader_contract"]

        self.assertEqual(
            contract["source_sha256"],
            "1f7f223c66a97975e416dce96b0a960933b7fa21b7bf4c6d380b3eb63e31b0d6",
        )
        self.assertTrue(contract["has_localsize_1_1_1"])
        self.assertTrue(contract["has_one_16384_word_uav"])
        self.assertTrue(contract["has_wgid_r48x"])
        self.assertTrue(contract["moves_wgid_to_store_offset"])
        self.assertTrue(contract["moves_wgid_to_store_value"])
        self.assertEqual(contract["expected_readback_samples"]["16383"], 16383)


if __name__ == "__main__":
    unittest.main()
