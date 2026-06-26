from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3313_gpu_2d_d3_video_texture_present_fork_fix.py"
)


class NativeGpu2dD3VideoTexturePresentForkFixSourceV3313Tests(unittest.TestCase):
    def test_v3313_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3313")
        self.assertEqual(runner.INIT_VERSION, "0.11.85")
        self.assertEqual(runner.INIT_BUILD, "v3313-gpu-2d-d3-video-texture-present-fork-fix")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3313_gpu_2d_d3_video_texture_present_fork_fix.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.85", required)
        self.assertIn(b"v3313-gpu-2d-d3-video-texture-present-fork-fix", required)
        self.assertIn(b"d3-video-texture-present-probe", required)
        self.assertIn(b"video-texture-present-probe", required)
        self.assertIn(b"gpu.d3.video.scope=gpu-2d-d3-demo-player-texture-blit-present", required)
        self.assertIn(b"gpu.d3.video.label=GPU D3 VIDEO TEXTURE", required)
        self.assertIn(
            b"gpu.d3.video.texture_source=sd-cache-mono1-expanded-to-rgba8-texture-per-frame",
            required,
        )
        self.assertIn(
            b"gpu.d3.video.blit_mode=kgsl-textured-quad-scale-to-960x720-linear-readback-kms-copy",
            required,
        )
        self.assertIn(b"gpu.d3.video.presented=%u", required)
        self.assertIn(b"gpu.d3.video.fps_milli=%llu", required)
        self.assertIn(b"video-texture-present-pass", required)

    def test_dispatch_contains_d3_video_texture_present_contract(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("#define GPU_D3_VIDEO_DEFAULT_FRAMES 60U", source)
        self.assertIn("#define GPU_D3_VIDEO_MAX_FRAMES 300U", source)
        self.assertIn("#define GPU_D3_VIDEO_MAX_TIMEOUT_MS 120000", source)
        self.assertIn("#define GPU_D3_VIDEO_TARGET_WIDTH (480U * VIDEO_PLAYER_HUD_SCALE)", source)
        self.assertIn("#define GPU_D3_VIDEO_TARGET_HEIGHT (360U * VIDEO_PLAYER_HUD_SCALE)", source)
        self.assertIn("#define GPU_D3_VIDEO_COLOR_FLAG_ALLOC_SIZE 65536ULL", source)
        self.assertIn("struct gpu_d3_video_frame_stats", source)
        self.assertIn("struct gpu_d3_video_summary", source)
        self.assertIn("gpu_h2_append_3d_state_pm4_ex", source)
        self.assertIn("gpu_h5_append_tile6_3_to_linear_a2d_pm4_ex", source)
        self.assertIn("gpu_d3_build_texture_video_pm4", source)
        self.assertIn("gpu_d3_create_session", source)
        self.assertIn("gpu_d3_write_mono1_texture", source)
        self.assertIn("gpu_d3_render_frame_to_kms", source)
        self.assertIn("gpu_d3_video_texture_present_child", source)
        self.assertIn("gpu_d3_video_texture_present_probe", source)
        self.assertIn("kgsl-textured-quad-scale-to-960x720-linear-readback-kms-copy", source)
        self.assertIn("sd-cache-mono1-expanded-to-rgba8-texture-per-frame", source)

    def test_dispatch_routes_gpu_d3_command_and_reports_present_gate(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(subcommand, "d3-video-texture-present-probe") == 0', source)
        self.assertIn('strcmp(subcommand, "video-texture-present-probe") == 0', source)
        self.assertIn("gpu.d3.video.command=gpu d3-video-texture-present-probe", source)
        self.assertIn("gpu.d3.video.result=%s", source)
        self.assertIn("video-texture-present-pass", source)
        self.assertIn("summary.presented_frames > 0U", source)
        self.assertIn("summary.changed_total > 0ULL", source)
        self.assertIn("gpu.d3.video.presented=%u", source)
        self.assertIn("gpu.d3.video.fps_milli=%llu", source)
        self.assertIn("gpu.d3.video.timing.gpu_wait.avg_us=%llu", source)
        self.assertIn("gpu.d3.video.timing.copy.avg_us=%llu", source)
        self.assertIn("gpu.d3.video.changed_total=%llu", source)
        self.assertIn("timeout_ms > GPU_D3_VIDEO_MAX_TIMEOUT_MS", source)
        self.assertIn("child_rc = gpu_d3_video_texture_present_child", source)
        self.assertIn("_exit(child_rc == 0 ? 0 : 1)", source)
        self.assertIn("usage: gpu d3-video-texture-present-probe", source)

    def test_builder_manifest_records_d3_live_validation_and_report_gate(self) -> None:
        manifest = runner._minimal_gpu_d3_manifest()
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

        self.assertEqual(manifest["scope"], "gpu-2d-d3-demo-player-texture-blit-present")
        self.assertEqual(manifest["source_preset"], "badapple")
        self.assertEqual(manifest["source_width"], 480)
        self.assertEqual(manifest["source_height"], 360)
        self.assertEqual(manifest["source_format"], "mono1")
        self.assertEqual(manifest["target_width"], 960)
        self.assertEqual(manifest["target_height"], 720)
        self.assertEqual(manifest["expected_result"], "video-texture-present-pass")
        self.assertIn("video-cache-preset-badapple-status", manifest["next_live_validation"])
        self.assertIn("require-video-texture-present-pass", manifest["next_live_validation"])
        self.assertIn("require-presented-frames-positive", manifest["next_live_validation"])
        self.assertIn("require-changed-total-positive", manifest["next_live_validation"])
        self.assertIn("require-fps-and-stage-timings", manifest["next_live_validation"])
        self.assertIn("D3, video texture blit into present path", report)
        self.assertIn("presented>0", report)
        self.assertIn("changed_total>0", report)
        self.assertIn("timing telemetry", report)
        self.assertIn("child writes summary telemetry to the pipe and exits", report)
        self.assertIn("timeout ceiling to 120000 ms", report)
        self.assertIn("not a new default menu policy", report)


if __name__ == "__main__":
    unittest.main()
