from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3135_doomgeneric_demo_hud_fast.py")


class NativeDoomgenericDemoHudFastSourceV3135Tests(unittest.TestCase):
    def test_builder_contract_pins_v3135_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3135")
        self.assertEqual(runner.INIT_VERSION, "0.10.121")
        self.assertEqual(runner.INIT_BUILD, "v3135-doomgeneric-demo-hud-fast")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3135")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3135-demo-hud-fast")
        self.assertEqual(runner.FRAME_IPC, "shared-mmap-direct-blit-demo-hud-fast-monotonic-input-thread")
        self.assertEqual(runner.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.NATIVE_DASHBOARD_MINIMAL, 0)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.NATIVE_DEMO_HUD, 1)
        self.assertEqual(runner.NATIVE_DEMO_HUD_FAST, 1)
        self.assertEqual(runner.DASHBOARD_METRICS_INTERVAL_FRAMES, 1800)
        self.assertEqual(runner.DASHBOARD_STATUS_INTERVAL_FRAMES, 300)
        self.assertIn(runner.DEMO_HUD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.profile=demo-hud-fast", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.frame_mode=demo-hud-fast-1to1", runner.REQUIRED_STRINGS)

    def test_native_hud_source_has_fast_demo_path_behind_flag(self) -> None:
        source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("#define A90_DOOMGENERIC_NATIVE_DEMO_HUD_FAST 0", source)
        self.assertIn("video_demo_doom_draw_fast_demo_hud", source)
        self.assertIn("video.demo.doom.dashboard.profile=demo-hud-fast", source)
        self.assertIn("video.demo.doom.dashboard.clear_path=targeted-demo-hud-regions", source)
        self.assertIn("compact cached HUD", source)

    def test_base_and_v3133_builders_expose_fast_hud_flags(self) -> None:
        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")
        v3133_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3133_doomgeneric_demo_hud.py"
        ).read_text(encoding="utf-8")

        self.assertIn("NATIVE_DEMO_HUD_FAST = 0", base_source)
        self.assertIn("DASHBOARD_STATUS_INTERVAL_FRAMES = 1", base_source)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD_FAST", base_source)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_DASHBOARD_STATUS_INTERVAL_FRAMES", base_source)
        self.assertIn("NATIVE_DEMO_HUD_FAST = 0", v3133_source)
        self.assertIn("DASHBOARD_STATUS_INTERVAL_FRAMES = 1", v3133_source)

    def test_adapter_source_renames_v3131_stack_to_v3135_and_adds_fast_marker(self) -> None:
        source = runner.v3135_adapter_source()

        self.assertIn("#include <time.h>", source)
        self.assertIn("pthread_create(&ctx->thread", source)
        self.assertIn("clock_gettime(CLOCK_MONOTONIC", source)
        self.assertIn(runner.INPUT_THREAD_MARKER, source)
        self.assertIn(runner.TIME_MODEL_MARKER, source)
        self.assertIn(runner.DEMO_HUD_MARKER, source)
        self.assertIn("demo_hud_marker=", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3131", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3133", source)
        self.assertNotIn("a90.doomgeneric.v3131", source)
        self.assertNotIn("a90.doomgeneric.v3133", source)

    def test_configure_v3135_module_repoints_v3133_and_dashboard_flags(self) -> None:
        saved = runner.configure_v3135_module()
        try:
            self.assertEqual(runner.v3133.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3133.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3133.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3133.v3133_adapter_source, runner.v3135_adapter_source)
            self.assertIs(runner.v3133.render_report, runner.render_report)

            saved_inner = runner.v3133.configure_v3133_module()
            try:
                runner.v3133.apply_v3133_dashboard_globals()
                v3033 = runner.v3133.v3131.v3129.v3126.v3123.v3120.v3118.v3116.v3033_module()
                self.assertEqual(v3033.NATIVE_DASHBOARD, 1)
                self.assertEqual(v3033.NATIVE_DASHBOARD_MINIMAL, 0)
                self.assertEqual(v3033.NATIVE_DASHBOARD_LARGE_FRAME, 0)
                self.assertEqual(v3033.NATIVE_DEMO_HUD, 1)
                self.assertEqual(v3033.NATIVE_DEMO_HUD_FAST, 1)
                self.assertEqual(v3033.DASHBOARD_METRICS_INTERVAL_FRAMES, 1800)
                self.assertEqual(v3033.DASHBOARD_STATUS_INTERVAL_FRAMES, 300)
            finally:
                runner.v3133.restore_v3131_module(saved_inner)
        finally:
            runner.restore_v3133_module(saved)

    def test_report_template_records_fast_hud_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3135.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --demo-hud-fast",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3135 DOOMGENERIC Fast Demo HUD Source Build", report)
        self.assertIn(runner.DEMO_HUD_MARKER, report)
        self.assertIn("every `1800` frames", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
