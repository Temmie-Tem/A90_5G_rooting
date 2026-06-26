from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3311_gpu_2d_d2_realframe_texture_probe.py"
)
d0_reference = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_2d_d0_texture_reference_v3304.py"
)
d1_shader_bytes = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_2d_d1_textured_shader_bytes_v3305.py"
)


class NativeGpu2dD2RealframeTextureSourceV3311Tests(unittest.TestCase):
    def test_v3311_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3311")
        self.assertEqual(runner.INIT_VERSION, "0.11.83")
        self.assertEqual(runner.INIT_BUILD, "v3311-gpu-2d-d2-realframe-texture-probe")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3311_gpu_2d_d2_realframe_texture_probe.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.83", required)
        self.assertIn(b"v3311-gpu-2d-d2-realframe-texture-probe", required)
        self.assertIn(
            b"gpu.d2.realframe.scope=gpu-2d-d2-realframe-sd-cache-texture-readback",
            required,
        )
        self.assertIn(b"gpu.d2.realframe.label=GPU REALFRAME BADAPPLE", required)
        self.assertIn(b"realframe-texture-readback-pass", required)
        self.assertIn(b"gpu.d2.realframe.source_dark_count=%u", required)
        self.assertIn(b"gpu.d2.realframe.source_light_count=%u", required)
        self.assertIn(b"gpu.d2.realframe.realframe_bbox_sample_match_count=%u", required)

    def test_dispatch_contains_d2_realframe_texture_contract(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("#define GPU_D2_REALFRAME_DEFAULT_FRAME_INDEX 515U", source)
        self.assertIn("#define GPU_D2_REALFRAME_MAX_TEXTURE_BYTES", source)
        self.assertIn("#define GPU_D2_REALFRAME_BADAPPLE_MANIFEST_PATH", source)
        self.assertIn("#define GPU_D1_CHECKER_SAMPLE_GRID 8U", source)
        self.assertIn("#define GPU_D1_SP_PS_CONFIG_TEXTURED", source)
        self.assertIn("GPU_H1_SP_CONFIG_ENABLED | (1U << 9) | (1U << 17)", source)
        self.assertIn("GPU_D1_TEXTURE_SOURCE_REALFRAME_MONO1", source)
        self.assertIn("gpu_d2_parse_realframe_manifest", source)
        self.assertIn("video_parse_manifest(config->manifest_path", source)
        self.assertIn("video_validate_stream_header(manifest, &header)", source)
        self.assertIn("gpu_d2_read_realframe_mono1", source)
        self.assertIn("gpu_d2_write_realframe_texture", source)
        self.assertIn("gpu_d1_write_sampler_descriptor", source)
        self.assertIn("gpu_d1_write_texture_descriptor_ex", source)
        self.assertIn("GPU_D1_CP_LOAD_STATE6_STATE_TYPE_SHADER", source)
        self.assertIn("GPU_D1_CP_LOAD_STATE6_STATE_TYPE_CONSTANTS", source)
        self.assertIn("GPU_D1_CP_LOAD_STATE6_SB_FS_TEX", source)
        self.assertIn("gpu_d1_pm4_emit_texture_state", source)
        self.assertIn("gpu_d1_build_texture_checkerboard_pm4", source)
        self.assertIn("gpu_d2_realframe_texture_probe", source)
        self.assertIn("0xbf800000U, 0xbf800000U", source)

    def test_dispatch_routes_gpu_d2_command_and_reports_realframe_gate(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(subcommand, "d2-realframe-texture-probe") == 0', source)
        self.assertIn('strcmp(subcommand, "realframe-texture-probe") == 0', source)
        self.assertIn("gpu.d2.realframe.command=gpu d2-realframe-texture-probe", source)
        self.assertIn("gpu.d2.realframe.result=%s", source)
        self.assertIn("realframe-texture-readback-pass", source)
        self.assertIn("linear_readback_changed_count > 0U", source)
        self.assertIn("realframe_source_dark_count > 0U", source)
        self.assertIn("realframe_source_light_count > 0U", source)
        self.assertIn("realframe_bbox_sample_match_count == GPU_D1_CHECKER_SAMPLE_COUNT", source)
        self.assertIn("realframe_bbox_sample_mismatch_count == 0U", source)
        self.assertIn("texture_bbox_sample_match_count == GPU_D1_CHECKER_SAMPLE_COUNT", source)
        self.assertIn("texture_bbox_sample_mismatch_count == 0U", source)
        self.assertIn("gpu.d2.realframe.viewport_scale_mode=inherited-default-clip-space-bbox", source)
        self.assertIn("gpu.d2.realframe.linear_readback_bbox=%u,%u,%u,%u", source)
        self.assertIn("gpu.d2.realframe.realframe_bbox_sample_count=%u", source)
        self.assertIn("gpu.d2.realframe.realframe_bbox_sample_match_count=%u", source)
        self.assertIn("gpu.d2.realframe.realframe_bbox_sample_mismatch_count=%u", source)
        self.assertIn("gpu.d2.realframe.output_dark_count=%u", source)
        self.assertIn("gpu.d2.realframe.output_light_count=%u", source)
        self.assertIn("usage: gpu d2-realframe-texture-probe", source)

    def test_builder_manifest_records_d2_live_validation_and_report_gate(self) -> None:
        manifest = runner._minimal_gpu_d2_manifest()
        report = runner.render_report(
            {
                "decision": runner.DECISION,
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
                "init_version": runner.INIT_VERSION,
                "init_build": runner.INIT_BUILD,
            },
            (),
            (),
        )

        self.assertEqual(manifest["scope"], "gpu-2d-d2-realframe-sd-cache-texture-readback")
        self.assertEqual(manifest["source_preset"], "badapple")
        self.assertEqual(manifest["source_frame_index"], 515)
        self.assertEqual(manifest["source_width"], 480)
        self.assertEqual(manifest["source_height"], 360)
        self.assertEqual(manifest["expected_bbox_sample_matches"], 64)
        self.assertEqual(manifest["expected_bbox_sample_mismatches"], 0)
        self.assertEqual(manifest["expected_linear_bbox"], "non-empty, device-measured")
        self.assertEqual(manifest["expected_linear_changed_count"], "greater-than-zero")
        self.assertIn("video-cache-preset-badapple-status", manifest["next_live_validation"])
        self.assertIn("require-linear-readback-bbox-found", manifest["next_live_validation"])
        self.assertIn("require-linear-readback-changed-count-positive", manifest["next_live_validation"])
        self.assertIn("require-realframe-bbox-sample-match-count-64", manifest["next_live_validation"])
        self.assertIn("require-realframe-bbox-sample-mismatch-count-0", manifest["next_live_validation"])
        self.assertIn("realframe_bbox_sample_count=64", report)
        self.assertIn("realframe_bbox_sample_match_count=64", report)
        self.assertIn("realframe_bbox_sample_mismatch_count=0", report)
        self.assertIn("D3 owns wiring the GPU textured blit", report)

    def test_v3304_v3305_prerequisites_still_pass_host_gates(self) -> None:
        d0 = d0_reference.run_recon()
        d1 = d1_shader_bytes.run_verification(require_disasm=False)

        self.assertTrue(d0["passed"])
        self.assertTrue(d0["checks"]["d0_texture_reference_recon_passed"])
        self.assertTrue(d1["passed"])
        self.assertTrue(d1["ready_for_d1_source"])
        self.assertEqual(
            d1["shader"]["binary_sha256"],
            "4e8ad0a934d236149af999619a1fe99690e7b732d2e4ca69a2b345100d8d04a3",
        )


if __name__ == "__main__":
    unittest.main()
