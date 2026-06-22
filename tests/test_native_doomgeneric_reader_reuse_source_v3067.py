from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3067_doomgeneric_reader_reuse.py")


class NativeDoomgenericReaderReuseSourceV3067Tests(unittest.TestCase):
    def test_builder_contract_pins_v3067_reader_reuse_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3067")
        self.assertEqual(runner.INIT_VERSION, "0.10.91")
        self.assertEqual(runner.INIT_BUILD, "v3067-doomgeneric-reader-reuse")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3067")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3067-reader-reuse")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3067-reader-reuse-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3067-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3067-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.BASELINE_REUSE_FRAME_BUFFER, 0)
        self.assertEqual(runner.REUSE_FRAME_BUFFER, 1)
        self.assertIn(b"v3067-doomgeneric-reader-reuse", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.reader=reused-loop-buffer", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.buffer_reuse=1", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.frame_scale=1:1", runner.REQUIRED_STRINGS)

    def test_native_presenter_uses_loop_owned_frame_reader(self) -> None:
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_REUSE_FRAME_BUFFER", hud_source)
        self.assertIn("struct video_demo_doom_frame_reader", hud_source)
        self.assertIn("video_demo_doom_frame_reader_source", hud_source)
        self.assertIn("video_demo_doom_frame_reader_cleanup(&frame_reader)", hud_source)
        self.assertIn("video.demo.doom.presenter.reader=reused-loop-buffer", hud_source)
        self.assertIn("video.demo.doom.loop.presenter.reader=reused-loop-buffer", hud_source)
        self.assertIn("&frame_reader);", hud_source)

    def test_base_builder_exposes_reader_reuse_compile_flag(self) -> None:
        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("REUSE_FRAME_BUFFER = 0", base_source)
        self.assertIn('numeric_define("VIDEO_DEMO_DOOMGENERIC_REUSE_FRAME_BUFFER", 1)', base_source)

    def test_v3067_mutates_v3065_build_surface_without_changing_input_or_scaling(self) -> None:
        runner.apply_v3067_globals()
        v3033 = runner.v3033_module()

        self.assertEqual(runner.v3065.CYCLE, runner.CYCLE)
        self.assertEqual(runner.v3065.INIT_VERSION, runner.INIT_VERSION)
        self.assertEqual(runner.v3065.INIT_BUILD, runner.INIT_BUILD)
        self.assertEqual(runner.v3065.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.v3065.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.v3065.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.v3065.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.v3065.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.v3065.FRAME_PATH, runner.FRAME_PATH)
        self.assertEqual(v3033.REUSE_FRAME_BUFFER, 1)
        self.assertIs(runner.v3065.render_report, runner.render_report)

    def test_report_template_records_v3068_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3067.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "input_path": "udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
                "input_udp_port": runner.INPUT_UDP_PORT,
                "input_socket_path": runner.INPUT_SOCKET_PATH,
                "input_state_path": runner.INPUT_STATE_PATH,
                "frame_path": runner.FRAME_PATH,
                "helper_loop_command": "helper --frame-ms 28 --input-udp 30570",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
                "presenter_pacing": "helper-frame-mtime",
            },
            "v3033_marker_strings": [
                "v3067-doomgeneric-reader-reuse",
                "video.demo.doom.presenter.reader=reused-loop-buffer",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3067 DOOMGENERIC Reader Reuse Source Build", report)
        self.assertIn("Baseline reader buffer reuse: `0`", report)
        self.assertIn("Candidate reader buffer reuse: `1`", report)
        self.assertIn("Reader marker: `reused-loop-buffer`", report)
        self.assertIn("Run ID: `V3068`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
