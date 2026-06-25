from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3276_gpu_h3_varying_ij_probe.py"
)
audit = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_h3_shader_byte_audit_v3246.py"
)


class NativeGpuH3VaryingIjSourceV3276Tests(unittest.TestCase):
    def test_v3276_identity_and_base(self) -> None:
        self.assertEqual(runner.CYCLE, "V3276")
        self.assertEqual(runner.INIT_VERSION, "0.11.64")
        self.assertEqual(runner.INIT_BUILD, "v3276-gpu-h3-varying-ij-probe")
        self.assertEqual(
            runner.BASE_BOOT.name,
            "boot_linux_v3268_gpu_h3_raster_mode_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.64", required)
        self.assertIn(b"v3276-gpu-h3-varying-ij-probe", required)
        self.assertIn(
            b"gpu.h3.draw.scope=first-triangle-h3-varying-ij-vpc-linkage-cffdump-diff",
            required,
        )
        self.assertIn(
            b"gpu.h3.draw.shader_payload=verified-ir3-vs-r0xy-to-r2-position-plus-r0-varying-and-cffdump-bary-fs",
            required,
        )
        self.assertIn(
            b"gpu.h3.draw.fragment_input_state_source=mesa-freedreno-a6xx-fd6-program-emit-fs-inputs-cffdump-varying-ij",
            required,
        )
        self.assertIn(b"gpu.h3.draw.sp_vs_fullregfootprint=%u", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_fullregfootprint=%u", required)
        self.assertIn(b"gpu.h3.draw.vpc_ps_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_vs_vpc_dest_reg0=0x%x", required)
        self.assertIn(b"gpu.h3.draw.vfd_sideband_source=mesa-freedreno-a6xx-vfd-system-values-invalid-regids", required)

    def test_dispatch_emits_cffdump_varying_ij_state(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        state_emit = source[source.index("static bool gpu_h2_append_3d_state_pm4"):]
        draw_emit = source[source.index("static bool gpu_h3_build_draw_envelope_pm4"):]

        self.assertIn("#define GPU_H3_SP_VS_CNTL_0_UNKNOWN31 (1U << 31)", source)
        self.assertIn("#define GPU_H3_SP_PS_CNTL_0_THREADSIZE (1U << 20)", source)
        self.assertIn("#define GPU_H3_SP_PS_CNTL_0_VARYING (1U << 22)", source)
        self.assertIn("#define GPU_H3_GRAS_CL_INTERP_CNTL 0x00000001U", source)
        self.assertIn("#define GPU_H3_RB_INTERP_CNTL 0x00000401U", source)
        self.assertIn("#define GPU_H3_VPC_VS_CNTL (8U | (4U << 8) | (0xffU << 16))", source)
        self.assertIn("#define GPU_H3_VPC_PS_CNTL (4U | (0xffU << 8) | (1U << 16) | (0xffU << 24))", source)
        self.assertIn("#define GPU_H3_SP_PS_INITIAL_TEX_LOAD_CNTL 0x00007fc0U", source)
        self.assertIn("#define GPU_H3_SP_PS_WAVE_CNTL 0x00000003U", source)
        self.assertIn("#define GPU_H3_SP_REG_PROG_ID_1 \\", source)
        self.assertIn("#define GPU_H3_PS_OUTPUT_REGID 2U", source)
        self.assertIn("#define GPU_H3_SP_VS_OUTPUT_CNTL 2U", source)
        self.assertIn("#define GPU_H3_SP_VS_VPC_DEST_REG0 0x00000400U", source)
        self.assertIn("#define GPU_H3_PC_MODE_CNTL 0x0000001fU", source)
        self.assertIn("#define GPU_H3_PC_VS_CNTL 0x00000008U", source)
        self.assertIn("#define GPU_H3_VFD_CNTL_1 GPU_H3_SP_REG_PROG_ID_0", source)

        self.assertIn(
            "GPU_H2_REG_VPC_PS_CNTL,\n                              GPU_H3_VPC_PS_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_PC_MODE_CNTL,\n                              GPU_H3_PC_MODE_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_PC_VS_CNTL,\n                              GPU_H3_PC_VS_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_SP_VS_OUTPUT_CNTL,\n                              GPU_H3_SP_VS_OUTPUT_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_SP_VS_VPC_DEST_REG0,\n                              GPU_H3_SP_VS_VPC_DEST_REG0",
            state_emit,
        )
        self.assertIn(
            "gpu_h3_pm4_emit_reg8(words, dwords, GPU_H2_REG_SP_PS_OUTPUT_REG0",
            state_emit,
        )
        self.assertIn(
            "gpu_h2_pm4_emit_reg6(words, dwords, GPU_H2_REG_VFD_CNTL_1",
            draw_emit,
        )
        self.assertIn("*vfd_reg_writes = 14;", draw_emit)
        self.assertIn("reg_writes += 26;", state_emit)

    def test_shader_audit_matches_varying_ij_payload(self) -> None:
        result = audit.run_audit(ir3_disasm="/missing/ir3-disasm")
        checks = result["checks"]

        self.assertTrue(result["passed"])
        self.assertTrue(checks["fs_uses_cffdump_bary_outputs"])
        self.assertTrue(checks["vs_routes_position_to_r2_and_varying_r0"])
        self.assertEqual(checks["sp_ps_output_reg0_regid"], 2)
        self.assertEqual(checks["sp_vs_output_reg0_a_regid"], 8)
        self.assertEqual(checks["sp_vs_output_reg0_b_regid"], 0)
        self.assertEqual(checks["vpc_vs_cntl_stride_in_vpc"], 8)
        self.assertEqual(checks["vpc_vs_cntl_positionloc"], 4)
        self.assertEqual(checks["vpc_ps_cntl_numnonposvar"], 4)
        self.assertTrue(checks["vpc_ps_cntl_varying"])

    def test_builder_manifest_records_varying_ij_boundary(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn(
            '"source_baseline": "v3274-clip-guardband-su-plus-v3275-live-no-pixel-and-a640-cffdump-varying-ij-diff"',
            source,
        )
        self.assertIn('"shader_payload": SHADER_PAYLOAD', source)
        self.assertIn('"varying_ij_source": VARYING_IJ_SOURCE', source)
        self.assertIn('"sp_ps_cntl0_value": SP_PS_CNTL0_VALUE', source)
        self.assertIn('"sp_vs_cntl0_value": SP_VS_CNTL0_VALUE', source)
        self.assertIn('"vpc_ps_cntl_value": VPC_PS_CNTL_VALUE', source)
        self.assertIn('"sp_ps_output_reg0_value": SP_PS_OUTPUT_REG0_VALUE', source)
        self.assertIn('"sp_vs_output_reg0_value": SP_VS_OUTPUT_REG0_VALUE', source)
        self.assertIn('"state_reg_writes_expected": 118', source)
        self.assertIn('"vfd_reg_writes_expected": 14', source)
        self.assertIn('"pm4_dwords_expected": 306', source)
        self.assertIn("gpu-h3-varying-ij-probe-candidate", source)
        self.assertIn("preserve-v3268-ramdisk-overlay-v3276-init-helper-engine", source)


if __name__ == "__main__":
    unittest.main()
