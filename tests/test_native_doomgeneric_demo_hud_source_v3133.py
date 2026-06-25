from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3133_doomgeneric_demo_hud.py")


class NativeDoomgenericDemoHudSourceV3133Tests(unittest.TestCase):
    def test_builder_contract_pins_v3133_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3133")
        self.assertEqual(runner.INIT_VERSION, "0.10.120")
        self.assertEqual(runner.INIT_BUILD, "v3133-doomgeneric-demo-hud")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3133")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3133-demo-hud")
        self.assertEqual(runner.FRAME_IPC, "shared-mmap-direct-blit-demo-hud-monotonic-input-thread")
        self.assertEqual(runner.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.NATIVE_DASHBOARD_MINIMAL, 0)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.NATIVE_DEMO_HUD, 1)
        self.assertEqual(runner.DASHBOARD_METRICS_INTERVAL_FRAMES, 30)
        self.assertIn(runner.DEMO_HUD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.profile=demo-hud-full", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.footer=physical-key-exit-and-copyright", runner.REQUIRED_STRINGS)

    def test_native_hud_source_has_demo_footer_behind_flag(self) -> None:
        source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("#define A90_DOOMGENERIC_NATIVE_DEMO_HUD 0", source)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD", source)
        self.assertIn("video.demo.doom.dashboard.profile=demo-hud-full", source)
        self.assertIn("video.demo.doom.dashboard.footer=physical-key-exit-and-copyright", source)
        self.assertIn("HOST host_doompad_keyboard_v3033.py UDP EVDEV", source)
        self.assertIn("POWER VOL EXIT   HOST KEYS VIA USB NCM", source)

    def test_base_builder_exposes_demo_hud_compile_flag(self) -> None:
        source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("NATIVE_DEMO_HUD = 0", source)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD", source)

    def test_adapter_source_keeps_v3131_input_time_stack_and_adds_demo_marker(self) -> None:
        source = runner.v3133_adapter_source()

        self.assertIn("#include <time.h>", source)
        self.assertIn("pthread_create(&ctx->thread", source)
        self.assertIn("clock_gettime(CLOCK_MONOTONIC", source)
        self.assertIn(runner.INPUT_THREAD_MARKER, source)
        self.assertIn(runner.TIME_MODEL_MARKER, source)
        self.assertIn(runner.DEMO_HUD_MARKER, source)
        self.assertIn("demo_hud_marker=", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3131", source)
        self.assertNotIn("a90.doomgeneric.v3131", source)

    def test_configure_v3133_module_repoints_v3131_and_dashboard_flags(self) -> None:
        saved = runner.configure_v3133_module()
        try:
            self.assertEqual(runner.v3131.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3131.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3131.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3131.v3131_adapter_source, runner.v3133_adapter_source)
            self.assertIs(runner.v3131.render_report, runner.render_report)
            self.assertIs(runner.v3131.v3129.v3126.apply_v3126_globals, runner.apply_v3133_dashboard_globals)

            runner.apply_v3133_dashboard_globals()
            v3033 = runner.v3131.v3129.v3126.v3123.v3120.v3118.v3116.v3033_module()
            self.assertEqual(v3033.NATIVE_DASHBOARD, 1)
            self.assertEqual(v3033.NATIVE_DASHBOARD_MINIMAL, 0)
            self.assertEqual(v3033.NATIVE_DASHBOARD_LARGE_FRAME, 0)
            self.assertEqual(v3033.NATIVE_DEMO_HUD, 1)
            self.assertEqual(v3033.DASHBOARD_METRICS_INTERVAL_FRAMES, 30)
        finally:
            runner.restore_v3131_module(saved)

    def test_report_template_records_demo_hud_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3133.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --demo-hud",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3133 DOOMGENERIC Demo HUD Source Build", report)
        self.assertIn(runner.DEMO_HUD_MARKER, report)
        self.assertIn("Caches hardware metrics every `30` frames", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
