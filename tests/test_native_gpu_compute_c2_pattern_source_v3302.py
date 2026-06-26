from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3302_gpu_compute_c2_pattern_probe.py"
)
shader_bytes = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_compute_c2_pattern_shader_bytes_v3302.py"
)


class NativeGpuComputeC2PatternSourceV3302Tests(unittest.TestCase):
    def test_v3302_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3302")
        self.assertEqual(runner.INIT_VERSION, "0.11.76")
        self.assertEqual(runner.INIT_BUILD, "v3302-gpu-compute-c2-pattern-probe")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3302_gpu_compute_c2_pattern_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.76", required)
        self.assertIn(b"v3302-gpu-compute-c2-pattern-probe", required)
        self.assertIn(
            b"gpu.c2.compute.scope=visible-compute-c2-128x128-workgroup-id-pattern",
            required,
        )
        self.assertIn(b"gpu.c2.compute.result=pattern-readback-pass", required)
        self.assertIn(
            b"gpu.c2.compute.expected_samples=0,1,2,3,31,127,128,4096,8192,16383",
            required,
        )
        self.assertIn(b"128X128 GPU COMPUTE PATTERN", required)

    def test_dispatch_contains_compute_pm4_contract(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("#define GPU_C1_PM4_CP_EXEC_CS 0x33U", source)
        self.assertIn("#define GPU_C1_CP_SET_MARKER_RM6_COMPUTE 8U", source)
        self.assertIn("#define GPU_C1_REG_SP_CS_CNTL_0 0xa9b0U", source)
        self.assertIn("#define GPU_C1_SP_CS_CNTL_0 0x80000080U", source)
        self.assertIn("#define GPU_C1_SP_CS_CONFIG 0x00400100U", source)
        self.assertIn("#define GPU_C1_SP_CS_CONST_CONFIG_0 0x00fcfcc0U", source)
        self.assertIn("#define GPU_C1_DESC0_R32_UINT_LINEAR 0x12c0a880U", source)
        self.assertIn("gpu_c2_build_compute_pm4", source)
        self.assertIn("GPU_C1_CP_LOAD_STATE6_STATE_TYPE_CONSTANTS", source)
        self.assertIn("GPU_C1_CP_LOAD_STATE6_STATE_TYPE_UAV", source)
        self.assertIn("GPU_C1_PM4_CP_EXEC_CS, 4", source)
        self.assertIn("GPU_G4_EVENT_CACHE_FLUSH_TS", source)

    def test_dispatch_embeds_verified_shader_and_readback_gate(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("0x200cc001U", source)
        self.assertIn("0xc0260000U", source)
        self.assertIn("0x03000000U", source)
        self.assertIn("gpu.c2.compute.shader_sha256=9259cd6e225aba4d1e86fb88527494404617b2aaf753c948379ade2edb18a6d1", source)
        self.assertIn("gpu.c2.compute.asm_sha256=1f7f223c66a97975e416dce96b0a960933b7fa21b7bf4c6d380b3eb63e31b0d6", source)
        self.assertIn("gpu.c2.compute.expected_samples=0,1,2,3,31,127,128,4096,8192,16383", source)
        self.assertIn("result.expected_match_count == GPU_C2_UAV_WORDS", source)
        self.assertIn("result.mismatch_count == 0U", source)
        self.assertIn("pattern-readback-pass", source)

    def test_builder_manifest_records_c2_live_validation(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"source_baseline": "v3302-compute-c2-pattern-verified-shader-bytes"', source)
        self.assertIn('"uav-readback-16384-workgroup-id-pattern"', source)
        self.assertIn("gpu-compute-c2-pattern-probe-candidate", source)
        self.assertIn("gpu c2-compute-pattern-probe --timeout-ms 5000 --materialize-devnode", source)

    def test_v3302_shader_bytes_still_match_embedded_source(self) -> None:
        result = shader_bytes.run_verification(require_disasm=False)

        self.assertTrue(result["passed"])
        self.assertEqual(result["shader"]["sizedwords"], 32)
        self.assertEqual(
            result["shader"]["binary_sha256"],
            "9259cd6e225aba4d1e86fb88527494404617b2aaf753c948379ade2edb18a6d1",
        )
        self.assertEqual(result["shader_contract"]["expected_readback_samples"]["16383"], 16383)


if __name__ == "__main__":
    unittest.main()
