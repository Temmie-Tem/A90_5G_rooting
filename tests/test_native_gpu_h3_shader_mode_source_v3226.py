from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3226_gpu_h3_shader_mode_probe.py"
)


class NativeGpuH3ShaderModeSourceV3226Tests(unittest.TestCase):
    def test_v3226_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3226")
        self.assertEqual(runner.INIT_VERSION, "0.11.40")
        self.assertEqual(runner.INIT_BUILD, "v3226-gpu-h3-shader-mode-probe")
        self.assertEqual(
            runner.BASE_BOOT.name,
            "boot_linux_v3224_gpu_h3_mrt_component_mask_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.40", required)
        self.assertIn(b"v3226-gpu-h3-shader-mode-probe", required)
        self.assertIn(
            b"gpu.h3.draw.scope=first-triangle-h3-shader-mode-mov-f32-shader",
            required,
        )
        self.assertIn(
            b"gpu.h3.draw.shader_mode_source=mesa-freedreno-a6xx-fd6-emit-shader-regs-sp-tpl1-mode",
            required,
        )
        self.assertIn(b"gpu.h3.draw.sp_mode_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.tpl1_mode_cntl=0x%x", required)
        self.assertIn(
            b"gpu.h3.draw.mrt_component_mask_source=mesa-freedreno-a6xx-mrt-components-full-rt0",
            required,
        )
        self.assertIn(b"gpu.h3.draw.color_output_mask=0x%x", required)
        self.assertIn(b"gpu.h3.draw.vpc_vs_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.vpc_vs_clip_cull_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.vpc_vs_clip_cull_cntl_v2=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_cl_vs_clip_cull_distance=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_sc_ras_msaa_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_sc_dest_msaa_cntl=0x%x", required)
        self.assertIn(b"gpu.h3.draw.gras_sc_screen_scissor_cntl=0x%x", required)
        self.assertNotIn(b"first-triangle-h3-sp-cntl0-linkage-mov-f32-shader", required)

    def test_dispatch_programs_mesa_shader_mode_registers(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        self.assertIn("#define GPU_H3_REG_SP_MODE_CNTL 0xab00U", source)
        self.assertIn("#define GPU_H3_REG_TPL1_MODE_CNTL 0xb309U", source)
        self.assertIn("#define GPU_H3_SP_MODE_CNTL 0x00000005U", source)
        self.assertIn("#define GPU_H3_TPL1_MODE_CNTL 0x000000a2U", source)
        self.assertIn("GPU_H3_REG_SP_MODE_CNTL,\n                              GPU_H3_SP_MODE_CNTL", source)
        self.assertIn("GPU_H3_REG_TPL1_MODE_CNTL,\n                              GPU_H3_TPL1_MODE_CNTL", source)
        self.assertIn(
            '"gpu.h3.draw.shader_mode_source=mesa-freedreno-a6xx-fd6-emit-shader-regs-sp-tpl1-mode',
            source,
        )
        self.assertIn('"gpu.h3.draw.sp_mode_cntl=0x%x', source)
        self.assertIn('"gpu.h3.draw.tpl1_mode_cntl=0x%x', source)
        self.assertIn("#define GPU_H3_COLOR_OUTPUT_MASK 0xfU", source)
        self.assertIn("uint32_t rb_mrt_control = (color_output_mask & 0xfU) << 7;", source)
        self.assertIn("GPU_H2_REG_RB_PS_OUTPUT_MASK,\n                              color_output_mask", source)
        self.assertIn("GPU_H2_REG_SP_PS_OUTPUT_MASK,\n                              color_output_mask", source)
        self.assertIn('"gpu.h3.draw.color_output_mask=0x%x', source)

    def test_builder_manifest_records_shader_mode_boundary(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertIn('"source_baseline": "v3224-gpu-h3-mrt-component-mask-probe"', source)
        self.assertIn('"shader_mode_source": "Mesa A6xx fd6 emit_shader_regs SP_MODE_CNTL and TPL1_MODE_CNTL"', source)
        self.assertIn('"sp_mode_cntl": "0x00000005"', source)
        self.assertIn('"tpl1_mode_cntl": "0x000000a2"', source)
        self.assertIn('"color_output_mask": "0xf"', source)
        self.assertIn('"rb_ps_output_mask": "0x0000000f"', source)
        self.assertIn('"sp_ps_output_mask": "0x0000000f"', source)
        self.assertIn('"rb_mrt0_component_enable": "0x00000780"', source)
        self.assertIn("emit_shader_regs", source)
        self.assertIn("preserve-v3224-ramdisk-overlay-v3226-init-helper-engine", source)
        self.assertIn('"bin/a90_doomgeneric_private_engine_v3226"', source)
        self.assertIn("BOOT_PARTITION_MAX_BYTES = 64 * 1024 * 1024", source)
        self.assertIn("V3226 boot image too large for boot partition", source)


if __name__ == "__main__":
    unittest.main()
