from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3126_doomgeneric_smooth_demo_direct_blit.py")


class NativeDoomgenericSmoothDemoDirectBlitSourceV3126Tests(unittest.TestCase):
    def test_builder_contract_pins_v3126_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3126")
        self.assertEqual(runner.INIT_VERSION, "0.10.117")
        self.assertEqual(runner.INIT_BUILD, "v3126-doomgeneric-smooth-demo-direct-blit")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3126")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3126-smooth-demo-direct-blit")
        self.assertEqual(runner.FRAME_WIDTH, 960)
        self.assertEqual(runner.FRAME_HEIGHT, 600)
        self.assertEqual(runner.NO_FULL_CLEAR, 1)
        self.assertEqual(runner.DIRECT_SHARED_BLIT, 1)
        self.assertEqual(runner.FOREGROUND_FRAME_LOG, 0)
        self.assertEqual(runner.TICK_QUANTUM_US, 28571)
        self.assertEqual(runner.FRAME_IPC, "shared-mmap-direct-blit-summary-only-smooth-demo")
        self.assertIn(runner.PACED_TIME_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"paced_time_model=presenter-token-doom-tic-quantum", runner.REQUIRED_STRINGS)
        self.assertIn(b"paced_time.quantum_us=%u", runner.REQUIRED_STRINGS)
        self.assertIn(b"fake_time_model=DG_SleepMs-request-telemetry-only", runner.REQUIRED_STRINGS)
        self.assertIn(b"non-original-smooth-demo", runner.REQUIRED_STRINGS)
        self.assertIn(b"%s.tick_telemetry.summary=1", runner.REQUIRED_STRINGS)
        self.assertIn(b"%s.tick_telemetry.%s", runner.REQUIRED_STRINGS)

    def test_adapter_source_combines_direct_blit_summary_and_paced_time(self) -> None:
        source = runner.v3126_adapter_source()

        self.assertIn(runner.PACED_TIME_MARKER, source)
        self.assertIn("a90_doomgeneric_v3126_paced_time_policy", source)
        self.assertIn("non-original-smooth-demo", source)
        self.assertIn("#define A90_DG_PACED_TICK_QUANTUM_US 28571U", source)
        self.assertIn("static void a90_doomgeneric_advance_paced_time(void)", source)
        self.assertIn("return paced_time_active ? paced_ticks_ms : fake_ticks_ms;", source)
        self.assertIn("paced_time_model=presenter-token-doom-tic-quantum", source)
        self.assertIn("smooth_demo_mode=non-original-smooth-demo", source)
        self.assertIn("fake_time_model=DG_SleepMs-request-telemetry-only", source)
        self.assertIn(runner.SCALE_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_MARKER, source)
        self.assertIn(runner.PHASE_TELEMETRY_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_PATH, source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3123", source)
        self.assertNotIn("a90.doomgeneric.v3123", source)
        self.assertEqual(source.count("a90_doomgeneric_advance_paced_time();"), 1)

    def test_apply_globals_sets_smooth_demo_without_sparse_gametic_presenter(self) -> None:
        v3033 = runner.v3123.v3120.v3118.v3116.v3033_module()
        saved_apply = runner.v3123.apply_v3123_globals
        saved_adapter = runner.v3123.v3123_adapter_source
        saved_report = runner.v3123.render_report
        saved_foreground_log = getattr(v3033, "FOREGROUND_FRAME_LOG", None)
        saved_gametic = getattr(v3033, "GAMETIC_PRESENT_ONLY", None)
        saved_interval = getattr(v3033, "TICK_PACE_INTERVAL_US", None)
        saved_tick_telemetry_path = getattr(v3033, "TICK_TELEMETRY_PATH", None)
        saved_tick_telemetry_summary = getattr(v3033, "TICK_TELEMETRY_SUMMARY", None)
        try:
            runner.apply_v3126_globals()

            self.assertEqual(runner.v3123.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3123.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3123.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertEqual(v3033.FOREGROUND_FRAME_LOG, 0)
            self.assertEqual(v3033.DIRECT_SHARED_BLIT, 1)
            self.assertEqual(v3033.GAMETIC_PRESENT_ONLY, 0)
            self.assertEqual(v3033.TICK_PACE_INTERVAL_US, 0)
            self.assertEqual(v3033.TICK_TELEMETRY_PATH, runner.TICK_TELEMETRY_PATH)
            self.assertEqual(v3033.TICK_TELEMETRY_SUMMARY, 1)
            self.assertIs(runner.v3123.v3123_adapter_source, runner.v3126_adapter_source)
            self.assertIs(runner.v3123.render_report, runner.render_report)
        finally:
            runner.v3123.apply_v3123_globals = saved_apply
            runner.v3123.v3123_adapter_source = saved_adapter
            runner.v3123.render_report = saved_report
            if saved_foreground_log is not None:
                v3033.FOREGROUND_FRAME_LOG = saved_foreground_log
            if saved_gametic is not None:
                v3033.GAMETIC_PRESENT_ONLY = saved_gametic
            if saved_interval is not None:
                v3033.TICK_PACE_INTERVAL_US = saved_interval
            if saved_tick_telemetry_path is not None:
                v3033.TICK_TELEMETRY_PATH = saved_tick_telemetry_path
            if saved_tick_telemetry_summary is not None:
                v3033.TICK_TELEMETRY_SUMMARY = saved_tick_telemetry_summary

    def test_native_status_hud_keeps_summary_only_loop_markers(self) -> None:
        hud = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("video.demo.doom.loop.foreground_frame_log=%d", hud)
        self.assertIn("video.demo.doom.dashboard.presenter_log=%s", hud)
        self.assertIn("video.demo.doom.loop.presenter.tick_pace_interval_us=%u", hud)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_TICK_TELEMETRY_SUMMARY", hud)
        self.assertIn("video_demo_doom_tick_telemetry_summary_print", hud)
        self.assertIn("%s.tick_telemetry.summary=1", hud)
        self.assertIn("%s.tick_telemetry.%s", hud)

    def test_report_template_records_v3127_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3126.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --smooth-demo --direct",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3126 DOOMGENERIC Smooth Demo Direct Blit Source Build", report)
        self.assertIn("non-original-smooth-demo", report)
        self.assertIn(runner.PACED_TIME_MARKER, report)
        self.assertIn("tick_telemetry.*", report)
        self.assertIn("Run ID: `V3127`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
