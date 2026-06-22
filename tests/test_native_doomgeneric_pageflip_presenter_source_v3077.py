from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3077_doomgeneric_pageflip_presenter.py")


class NativeDoomgenericPageflipPresenterSourceV3077Tests(unittest.TestCase):
    def test_builder_contract_pins_v3077_pageflip_presenter_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3077")
        self.assertEqual(runner.INIT_VERSION, "0.10.95")
        self.assertEqual(runner.INIT_BUILD, "v3077-doomgeneric-pageflip-presenter")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3077")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3077-pageflip-presenter")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3077-pageflip-presenter-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3077-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3077-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.NATIVE_DASHBOARD_MINIMAL, 1)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.NATIVE_DOOM_PRESENT_PAGEFLIP, 1)
        self.assertEqual(runner.BASELINE_NATIVE_DOOM_PRESENT_PAGEFLIP, 0)
        self.assertEqual(runner.REUSE_FRAME_BUFFER, 1)
        self.assertEqual(runner.FRAME_TIMING_PROBE, 1)
        self.assertIn(b"v3077-doomgeneric-pageflip-presenter", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.present_mode=pageflip", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.present_path=kms-dumb-buffer-pageflip", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us", runner.REQUIRED_STRINGS)
        self.assertIn(b"flip_delta_avg_us=", runner.REQUIRED_STRINGS)

    def test_native_hud_adds_pageflip_presenter_and_telemetry(self) -> None:
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PRESENT_PAGEFLIP", hud_source)
        self.assertIn("video_demo_doom_present_kms_frame", hud_source)
        self.assertIn("a90_kms_present_pageflip(label,", hud_source)
        self.assertIn("video_demo_doom_prime_pageflip_presenter", hud_source)
        self.assertIn("doomdashprime", hud_source)
        self.assertIn("video_demo_doom_flip_stats", hud_source)
        self.assertIn("video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us", hud_source)
        self.assertIn("flip_delta_avg_us", hud_source)
        self.assertIn("video.demo.doom.presenter.present_mode=pageflip", hud_source)
        self.assertIn("video.demo.doom.loop.present_path=%s", hud_source)

    def test_base_builder_exposes_disabled_pageflip_compile_flag(self) -> None:
        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("NATIVE_DOOM_PRESENT_PAGEFLIP = 0", base_source)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PRESENT_PAGEFLIP", base_source)

    def test_v3077_mutates_v3074_build_surface_without_changing_input_or_dashboard(self) -> None:
        runner.apply_v3077_globals()
        v3033 = runner.v3033_module()

        self.assertEqual(runner.v3074.v3071.CYCLE, runner.CYCLE)
        self.assertEqual(runner.v3074.v3071.INIT_VERSION, runner.INIT_VERSION)
        self.assertEqual(runner.v3074.v3071.INIT_BUILD, runner.INIT_BUILD)
        self.assertEqual(runner.v3074.v3071.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.v3074.v3071.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.v3074.v3071.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.v3074.v3071.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.v3074.v3071.FRAME_TIMING_PROBE, 1)
        self.assertEqual(runner.v3074.v3071.FRAME_PATH, runner.FRAME_PATH)
        self.assertEqual(v3033.NATIVE_DASHBOARD_MINIMAL, 1)
        self.assertEqual(v3033.NATIVE_DOOM_PRESENT_PAGEFLIP, 1)
        self.assertEqual(v3033.REUSE_FRAME_BUFFER, 1)
        self.assertEqual(v3033.FRAME_TIMING_PROBE, 1)

    def test_report_template_records_v3078_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3077.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --frame-ms 28 --input-udp 30570",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
                "dashboard_profile": "minimal-fastdraw",
            },
            "v3033_marker_strings": [
                "v3077-doomgeneric-pageflip-presenter",
                "video.demo.doom.presenter.present_mode=pageflip",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3077 DOOMGENERIC Pageflip Presenter Source Build", report)
        self.assertIn("Baseline pageflip presenter: `0`", report)
        self.assertIn("Candidate pageflip presenter: `1`", report)
        self.assertIn("Run ID: `V3078`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
