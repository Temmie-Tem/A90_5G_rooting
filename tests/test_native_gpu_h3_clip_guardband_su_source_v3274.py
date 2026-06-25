from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3274_gpu_h3_clip_guardband_su_probe.py"
)


class NativeGpuH3ClipGuardbandSuSourceV3274Tests(unittest.TestCase):
    def test_v3274_identity_and_base(self) -> None:
        self.assertEqual(runner.CYCLE, "V3274")
        self.assertEqual(runner.INIT_VERSION, "0.11.63")
        self.assertEqual(runner.INIT_BUILD, "v3274-gpu-h3-clip-guardband-su-probe")
        self.assertEqual(
            runner.BASE_BOOT.name,
            "boot_linux_v3268_gpu_h3_raster_mode_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.63", required)
        self.assertIn(b"v3274-gpu-h3-clip-guardband-su-probe", required)
        self.assertIn(
            b"gpu.h3.draw.scope=first-triangle-h3-clip-guardband-su-rasterizer-a6xx-hlsq-negative-audit-output-routing-sp-frontend-prog-id-state-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader",
            required,
        )
        self.assertIn(b"gpu.h3.draw.sp_const_config_source=mesa-freedreno-a6xx-fd6-program-config-stateobj", required)
        self.assertIn(b"gpu.h3.draw.sp_vs_const_config=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_const_config=0x%x", required)
        self.assertIn(b"gpu.h3.draw.hlsq_round4_audit=local-a6xx-fd6-uses-sp-program-config-not-legacy-hlsq-control-regs", required)
        self.assertIn(b"gpu.h3.draw.fs_output_cntl_source=mesa-freedreno-a6xx-fd6-program-invalid-depth-sampmask-stencil-regids-and-rb-sp-mrt-count-one", required)
        self.assertIn(b"gpu.h3.draw.rb_ps_output_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.rb_ps_mrt_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_output_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_mrt_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.clip_guardband_su_source=mesa-freedreno-a6xx-fd6-rasterizer-plus-guardband-state", required)
        self.assertIn(b"gpu.h3.draw.gras_cl_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_cl_guardband_clip_adj=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_point_minmax=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_point_size=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_poly_offset_scale=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_poly_offset_offset=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_su_poly_offset_offset_clamp=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_frontend_prog_id_source=mesa-freedreno-a6xx-fd6-program-emit-fs-inputs-current-constant-fs-no-varyings", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_initial_tex_load_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_wave_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_lb_param_limit=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_reg_prog_id_0=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_reg_prog_id_1=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_reg_prog_id_2=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_reg_prog_id_3=0x%x", required)

    def test_dispatch_emits_clip_guardband_su_state(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        state_emit = source[source.index("static bool gpu_h2_append_3d_state_pm4"):]
        shader_emit = source[source.index("static bool gpu_h3_append_shader_state_pm4"):]

        self.assertIn("#define GPU_H3_SP_INVALID_REG 0xfcU", source)
        self.assertIn("#define GPU_H3_GRAS_CL_CNTL 0x000000c0U", source)
        self.assertIn("#define GPU_H3_GRAS_CL_GUARDBAND_CLIP_ADJ 0x0007fdffU", source)
        self.assertIn("#define GPU_H3_GRAS_SU_CNTL 0x00000814U", source)
        self.assertIn("#define GPU_H3_GRAS_SU_POINT_MINMAX 0xffc00001U", source)
        self.assertIn("#define GPU_H3_GRAS_SU_POINT_SIZE 0x00000010U", source)
        self.assertIn("#define GPU_H3_GRAS_SU_POLY_OFFSET_SCALE 0x00000000U", source)
        self.assertIn("#define GPU_H3_GRAS_SU_POLY_OFFSET_OFFSET 0x00000000U", source)
        self.assertIn("#define GPU_H3_GRAS_SU_POLY_OFFSET_OFFSET_CLAMP 0x00000000U", source)
        self.assertIn("#define GPU_H3_SP_PS_OUTPUT_CNTL \\", source)
        self.assertIn("#define GPU_H3_RB_PS_OUTPUT_CNTL 0x00000000U", source)
        self.assertIn("#define GPU_H3_RB_PS_MRT_CNTL 0x00000001U", source)
        self.assertIn("#define GPU_H3_SP_PS_MRT_CNTL 0x00000001U", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 8)", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 16)", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 24)", source)
        self.assertIn("#define GPU_H3_SP_REG_PROG_ID_0 \\", source)
        self.assertIn("#define GPU_H3_SP_REG_PROG_ID_1 GPU_H3_SP_REG_PROG_ID_0", source)
        self.assertIn("#define GPU_H3_SP_REG_PROG_ID_2 GPU_H3_SP_REG_PROG_ID_0", source)
        self.assertIn("#define GPU_H3_REG_GRAS_SU_POINT_MINMAX 0x8091U", source)
        self.assertIn("#define GPU_H3_REG_GRAS_SU_POINT_SIZE 0x8092U", source)
        self.assertIn("#define GPU_H3_REG_GRAS_SU_POLY_OFFSET_SCALE 0x8095U", source)
        self.assertIn("#define GPU_H3_REG_GRAS_SU_POLY_OFFSET_OFFSET 0x8096U", source)
        self.assertIn("#define GPU_H3_REG_GRAS_SU_POLY_OFFSET_OFFSET_CLAMP 0x8097U", source)
        self.assertIn("#define GPU_H3_SP_CONST_CONFIG_ENABLED 0x00000100U", source)
        self.assertIn(
            '"gpu.h3.draw.scope=first-triangle-h3-clip-guardband-su-rasterizer-a6xx-hlsq-negative-audit-output-routing-sp-frontend-prog-id-state-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader',
            source,
        )
        self.assertLess(
            shader_emit.index("GPU_H1_REG_SP_VS_INSTR_SIZE"),
            shader_emit.index("GPU_H3_REG_SP_VS_CONST_CONFIG"),
        )
        self.assertLess(
            shader_emit.index("GPU_H1_REG_SP_PS_INSTR_SIZE"),
            shader_emit.index("GPU_H3_REG_SP_PS_CONST_CONFIG"),
        )
        self.assertIn(
            "GPU_H3_REG_SP_VS_CONST_CONFIG,\n                              GPU_H3_SP_CONST_CONFIG_ENABLED",
            source,
        )
        self.assertIn(
            "GPU_H3_REG_SP_PS_CONST_CONFIG,\n                              GPU_H3_SP_CONST_CONFIG_ENABLED",
            source,
        )
        self.assertIn(
            "GPU_H2_REG_SP_PS_OUTPUT_CNTL,\n                              GPU_H3_SP_PS_OUTPUT_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_RB_PS_OUTPUT_CNTL,\n                              GPU_H3_RB_PS_OUTPUT_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_RB_PS_MRT_CNTL,\n                              GPU_H3_RB_PS_MRT_CNTL",
            state_emit,
        )
        self.assertIn(
            "GPU_H2_REG_SP_PS_MRT_CNTL,\n                              GPU_H3_SP_PS_MRT_CNTL",
            state_emit,
        )
        self.assertLess(
            state_emit.index("GPU_H2_REG_GRAS_CL_CNTL"),
            state_emit.index("GPU_H2_REG_GRAS_CL_GUARDBAND_CLIP_ADJ"),
        )
        self.assertLess(
            state_emit.index("GPU_H2_REG_GRAS_CL_GUARDBAND_CLIP_ADJ"),
            state_emit.index("GPU_H2_REG_GRAS_SU_CNTL"),
        )
        self.assertLess(
            state_emit.index("GPU_H2_REG_GRAS_SU_CNTL"),
            state_emit.index("GPU_H3_REG_GRAS_SU_POINT_MINMAX"),
        )
        self.assertLess(
            state_emit.index("GPU_H3_REG_GRAS_SU_POLY_OFFSET_OFFSET_CLAMP"),
            state_emit.index("GPU_H3_REG_GRAS_SU_CONSERVATIVE_RAS_CNTL"),
        )
        self.assertIn('"gpu.h3.draw.sp_const_config_source=mesa-freedreno-a6xx-fd6-program-config-stateobj', source)
        self.assertIn('"gpu.h3.draw.sp_vs_const_config=0x%x', source)
        self.assertIn('"gpu.h3.draw.sp_ps_const_config=0x%x', source)
        self.assertIn('"gpu.h3.draw.hlsq_round4_audit=local-a6xx-fd6-uses-sp-program-config-not-legacy-hlsq-control-regs', source)
        self.assertIn('"gpu.h3.draw.fs_output_cntl_source=mesa-freedreno-a6xx-fd6-program-invalid-depth-sampmask-stencil-regids-and-rb-sp-mrt-count-one', source)
        self.assertIn('"gpu.h3.draw.rb_ps_output_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.rb_ps_mrt_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.sp_ps_output_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.sp_ps_mrt_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.clip_guardband_su_source=mesa-freedreno-a6xx-fd6-rasterizer-plus-guardband-state', source)
        self.assertIn('"gpu.h3.draw.gras_cl_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_cl_guardband_clip_adj=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_point_minmax=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_point_size=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_poly_offset_scale=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_poly_offset_offset=0x%x', source)
        self.assertIn('"gpu.h3.draw.gras_su_poly_offset_offset_clamp=0x%x', source)

    def test_builder_manifest_records_clip_guardband_su_boundary(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn(
            '"source_baseline": "v3272-sp-frontend-prog-id-plus-v3273-live-no-pixel-and-a6xx-clip-guardband-su-diff"',
            source,
        )
        self.assertIn('"sp_const_config_source": SP_CONST_CONFIG_SOURCE', source)
        self.assertIn('"sp_const_config_value": SP_CONST_CONFIG_VALUE', source)
        self.assertIn('"hlsq_round4_audit": HLSQ_ROUND4_AUDIT', source)
        self.assertIn('"sp_ps_output_cntl_source": SP_PS_OUTPUT_CNTL_SOURCE', source)
        self.assertIn('"sp_ps_output_cntl_value": SP_PS_OUTPUT_CNTL_VALUE', source)
        self.assertIn('"rb_ps_output_cntl_value": RB_PS_OUTPUT_CNTL_VALUE', source)
        self.assertIn('"rb_ps_mrt_cntl_value": RB_PS_MRT_CNTL_VALUE', source)
        self.assertIn('"sp_ps_mrt_cntl_value": SP_PS_MRT_CNTL_VALUE', source)
        self.assertIn('"output_routing_registers": {', source)
        self.assertIn('"clip_guardband_su_source": CLIP_GUARDBAND_SU_SOURCE', source)
        self.assertIn('"gras_cl_cntl_value": GRAS_CL_CNTL_VALUE', source)
        self.assertIn('"gras_cl_guardband_clip_adj_value": GRAS_CL_GUARDBAND_CLIP_ADJ_VALUE', source)
        self.assertIn('"gras_su_cntl_value": GRAS_SU_CNTL_VALUE', source)
        self.assertIn('"gras_su_point_minmax_value": GRAS_SU_POINT_MINMAX_VALUE', source)
        self.assertIn('"gras_su_poly_offset_offset_clamp_value": GRAS_SU_POLY_OFFSET_OFFSET_CLAMP_VALUE', source)
        self.assertIn('"clip_guardband_su_registers": {', source)
        self.assertIn('"state_reg_writes_expected": 111', source)
        self.assertIn('"pm4_dwords_expected": 292', source)
        self.assertIn("preserve-v3268-ramdisk-overlay-v3274-init-helper-engine", source)
        self.assertIn("STALE_V3268_ENGINE_RAMDISK_PATH", source)


if __name__ == "__main__":
    unittest.main()
