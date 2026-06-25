from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3270_gpu_h3_sp_const_fs_output_probe.py"
)


class NativeGpuH3SpConstFsOutputSourceV3270Tests(unittest.TestCase):
    def test_v3270_identity_and_base(self) -> None:
        self.assertEqual(runner.CYCLE, "V3270")
        self.assertEqual(runner.INIT_VERSION, "0.11.61")
        self.assertEqual(runner.INIT_BUILD, "v3270-gpu-h3-sp-const-fs-output-probe")
        self.assertEqual(
            runner.BASE_BOOT.name,
            "boot_linux_v3268_gpu_h3_raster_mode_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.61", required)
        self.assertIn(b"v3270-gpu-h3-sp-const-fs-output-probe", required)
        self.assertIn(
            b"gpu.h3.draw.scope=first-triangle-h3-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader",
            required,
        )
        self.assertIn(b"gpu.h3.draw.sp_const_config_source=mesa-freedreno-a6xx-fd6-program-config-stateobj", required)
        self.assertIn(b"gpu.h3.draw.sp_vs_const_config=0x%x", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_const_config=0x%x", required)
        self.assertIn(b"gpu.h3.draw.fs_output_cntl_source=mesa-freedreno-a6xx-fd6-program-invalid-depth-sampmask-stencil-regids", required)
        self.assertIn(b"gpu.h3.draw.sp_ps_output_cntl=0x%x", required)

    def test_dispatch_emits_sp_const_enable_and_invalid_fs_output_regids(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        state_emit = source[source.index("static bool gpu_h2_append_3d_state_pm4"):]
        shader_emit = source[source.index("static bool gpu_h3_append_shader_state_pm4"):]

        self.assertIn("#define GPU_H3_SP_INVALID_REG 0xfcU", source)
        self.assertIn("#define GPU_H3_SP_PS_OUTPUT_CNTL \\", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 8)", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 16)", source)
        self.assertIn("(GPU_H3_SP_INVALID_REG << 24)", source)
        self.assertIn("#define GPU_H3_REG_SP_VS_CONST_CONFIG 0xb800U", source)
        self.assertIn("#define GPU_H3_REG_SP_PS_CONST_CONFIG 0xbb10U", source)
        self.assertIn("#define GPU_H3_SP_CONST_CONFIG_ENABLED 0x00000100U", source)
        self.assertIn(
            '"gpu.h3.draw.scope=first-triangle-h3-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader',
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
        self.assertIn('"gpu.h3.draw.sp_const_config_source=mesa-freedreno-a6xx-fd6-program-config-stateobj', source)
        self.assertIn('"gpu.h3.draw.sp_vs_const_config=0x%x', source)
        self.assertIn('"gpu.h3.draw.sp_ps_const_config=0x%x', source)
        self.assertIn('"gpu.h3.draw.fs_output_cntl_source=mesa-freedreno-a6xx-fd6-program-invalid-depth-sampmask-stencil-regids', source)
        self.assertIn('"gpu.h3.draw.sp_ps_output_cntl=0x%x', source)

    def test_builder_manifest_records_sp_const_fs_output_boundary(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn(
            '"source_baseline": "v3268-raster-mode-plus-v3269-live-no-pixel-and-round4-hlsq-audit"',
            source,
        )
        self.assertIn('"sp_const_config_source": SP_CONST_CONFIG_SOURCE', source)
        self.assertIn('"sp_const_config_value": SP_CONST_CONFIG_VALUE', source)
        self.assertIn('"sp_ps_output_cntl_source": SP_PS_OUTPUT_CNTL_SOURCE', source)
        self.assertIn('"sp_ps_output_cntl_value": SP_PS_OUTPUT_CNTL_VALUE', source)
        self.assertIn('"state_reg_writes_expected": 100', source)
        self.assertIn('"pm4_dwords_expected": 270', source)
        self.assertIn("preserve-v3268-ramdisk-overlay-v3270-init-helper-engine", source)
        self.assertIn("STALE_V3268_ENGINE_RAMDISK_PATH", source)


if __name__ == "__main__":
    unittest.main()
