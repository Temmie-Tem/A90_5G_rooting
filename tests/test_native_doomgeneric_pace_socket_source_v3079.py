from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3079_doomgeneric_pace_socket.py")


class NativeDoomgenericPaceSocketSourceV3079Tests(unittest.TestCase):
    def test_builder_contract_pins_v3079_pace_socket_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3079")
        self.assertEqual(runner.INIT_VERSION, "0.10.96")
        self.assertEqual(runner.INIT_BUILD, "v3079-doomgeneric-pace-socket")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3079")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3079-pace-socket")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3079-pace-socket-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3079-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3079-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.PACE_SOCKET_PATH, "/tmp/a90-doomgeneric-v3079-pace.sock")
        self.assertEqual(runner.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS, 18)
        self.assertEqual(runner.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.NATIVE_DASHBOARD_MINIMAL, 1)
        self.assertEqual(runner.NATIVE_DOOM_PRESENT_PAGEFLIP, 1)
        self.assertEqual(runner.REUSE_FRAME_BUFFER, 1)
        self.assertEqual(runner.FRAME_TIMING_PROBE, 1)
        self.assertIn(b"v3079-doomgeneric-pace-socket", runner.REQUIRED_STRINGS)
        self.assertIn(b"a90.doomgeneric.v3079.pace=presenter-pageflip-token", runner.REQUIRED_STRINGS)
        self.assertIn(b"--pace-socket", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.pacing=presenter-pageflip-pace-socket", runner.REQUIRED_STRINGS)
        self.assertIn(b"pace_socket.tokens_sent=", runner.REQUIRED_STRINGS)

    def test_native_hud_adds_presenter_pace_sender_and_markers(self) -> None:
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS", hud_source)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PACE_PACKET_MAGIC", hud_source)
        self.assertIn("struct video_demo_doom_pace_sender", hud_source)
        self.assertIn("video_demo_doom_send_pace_token", hud_source)
        self.assertIn("presenter-pageflip-pace-socket", hud_source)
        self.assertIn("video.demo.doom.presenter.pace_socket_path=%s", hud_source)
        self.assertIn("video.demo.doom.presenter.pageflip_min_submit_interval_ms=%d", hud_source)
        self.assertIn("present_not_before_ns", hud_source)
        self.assertIn("video.demo.doom.loop.pace_socket.wait_timeouts=%u", hud_source)

    def test_base_builder_exposes_disabled_pace_compile_flags(self) -> None:
        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn('PACE_SOCKET_PATH = ""', base_source)
        self.assertIn("PAGEFLIP_MIN_SUBMIT_INTERVAL_MS = 0", base_source)
        self.assertIn("A90_DOOMGENERIC_BRIDGE_PACE_SOCKET_PATH", base_source)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS", base_source)

    def test_helper_adapter_adds_blocking_pace_socket_loop(self) -> None:
        source = runner.v3079_adapter_source()

        self.assertIn("a90.doomgeneric.v3079.pace=presenter-pageflip-token", source)
        self.assertIn("A90_DG_PACE_PACKET_MAGIC", source)
        self.assertIn("a90_doomgeneric_open_pace_socket", source)
        self.assertIn("a90_doomgeneric_wait_pace_fd", source)
        self.assertIn("a90_doomgeneric_close_pace_socket", source)
        self.assertIn("const char *pace_socket_path", source)
        self.assertIn("pace_fd = a90_doomgeneric_open_pace_socket(pace_socket_path);", source)
        self.assertIn("rc = a90_doomgeneric_wait_pace_fd(pace_fd);", source)
        self.assertIn("if (pace_fd < 0) {\n            usleep((useconds_t)frame_ms * 1000U);", source)
        self.assertIn("argc == 11 || argc == 13 || argc == 15 || argc == 17", source)
        self.assertIn("strcmp(argv[arg_index], \"--pace-socket\") == 0", source)
        self.assertIn(
            "a90_doomgeneric_run_wad_frame_loop(argv[2], frames, argv[6], argv[8], "
            "input_socket_path, input_udp_port, pace_socket_path, frame_ms)",
            source,
        )

    def test_v3079_mutates_v3077_build_surface_without_changing_input_stack(self) -> None:
        runner.apply_v3079_globals()
        v3033 = runner.v3033_module()
        v3059 = runner.V3059

        self.assertEqual(runner.v3077.v3074.v3071.CYCLE, runner.CYCLE)
        self.assertEqual(runner.v3077.v3074.v3071.INIT_VERSION, runner.INIT_VERSION)
        self.assertEqual(runner.v3077.v3074.v3071.INIT_BUILD, runner.INIT_BUILD)
        self.assertEqual(runner.v3077.v3074.v3071.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.v3077.v3074.v3071.INPUT_UDP_PORT, 30570)
        self.assertEqual(v3033.PACE_SOCKET_PATH, runner.PACE_SOCKET_PATH)
        self.assertEqual(v3033.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS, runner.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS)
        self.assertEqual(v3033.NATIVE_DOOM_PRESENT_PAGEFLIP, 1)
        self.assertIs(v3059.v3059_adapter_source, runner.v3079_adapter_source)

    def test_report_template_records_v3080_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3079.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --pace-socket /tmp/a90-doomgeneric-v3079-pace.sock",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
            },
            "v3033_marker_strings": [
                "v3079-doomgeneric-pace-socket",
                "video.demo.doom.presenter.pacing=presenter-pageflip-pace-socket",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3079 DOOMGENERIC Pace Socket Source Build", report)
        self.assertIn("Baseline pacing: `helper-frame-mtime`", report)
        self.assertIn("Candidate pacing: `presenter-pageflip-pace-socket`", report)
        self.assertIn("Run ID: `V3080`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
