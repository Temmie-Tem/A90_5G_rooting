from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3118_doomgeneric_no_full_clear.py")


class NativeDoomgenericNoFullClearSourceV3118Tests(unittest.TestCase):
    def test_builder_contract_pins_v3118_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3118")
        self.assertEqual(runner.INIT_VERSION, "0.10.114")
        self.assertEqual(runner.INIT_BUILD, "v3118-doomgeneric-no-full-clear")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3118")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3118-no-full-clear")
        self.assertEqual(runner.FRAME_WIDTH, 960)
        self.assertEqual(runner.FRAME_HEIGHT, 600)
        self.assertEqual(runner.NO_FULL_CLEAR, 1)
        self.assertEqual(runner.CLEAR_PATH, "dirty-dashboard-regions")
        self.assertIn(b"video.demo.doom.dashboard.full_clear=0", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.clear_path=dirty-dashboard-regions", runner.REQUIRED_STRINGS)

    def test_native_sources_have_no_full_clear_path(self) -> None:
        hud = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")
        v3033 = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR", hud)
        self.assertIn("a90_kms_begin_frame_no_clear()", hud)
        self.assertIn("video_demo_doom_clear_minimal_dashboard_regions", hud)
        self.assertIn("video.demo.doom.dashboard.full_clear=0", hud)
        self.assertIn("video.demo.doom.dashboard.clear_path=dirty-dashboard-regions", hud)
        self.assertIn("NO_FULL_CLEAR = 0", v3033)
        self.assertIn('numeric_define("VIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR", 1)', v3033)

    def test_adapter_source_uses_v3118_paths_and_markers(self) -> None:
        source = runner.v3118_adapter_source()

        self.assertIn(runner.SCALE_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_MARKER, source)
        self.assertIn(runner.PHASE_TELEMETRY_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_PATH, source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3116", source)
        self.assertNotIn("a90.doomgeneric.v3116", source)

    def test_apply_globals_sets_no_full_clear_flag(self) -> None:
        v3033 = runner.v3116.v3033_module()
        saved_apply = runner.v3116.apply_v3116_globals
        saved_no_full_clear = getattr(v3033, "NO_FULL_CLEAR", None)
        saved_v3116_adapter = runner.v3116.v3116_adapter_source
        saved_v3116_report = runner.v3116.render_report
        try:
            runner.apply_v3118_globals()

            self.assertEqual(runner.v3116.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3116.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3116.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertEqual(v3033.NO_FULL_CLEAR, 1)
            self.assertIs(runner.v3116.v3116_adapter_source, runner.v3118_adapter_source)
            self.assertIs(runner.v3116.render_report, runner.render_report)
        finally:
            runner.v3116.apply_v3116_globals = saved_apply
            runner.v3116.v3116_adapter_source = saved_v3116_adapter
            runner.v3116.render_report = saved_v3116_report
            if saved_no_full_clear is not None:
                v3033.NO_FULL_CLEAR = saved_no_full_clear

    def test_report_template_records_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3118.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --shared-frame --no-full-clear",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3118 DOOMGENERIC No-Full-Clear Source Build", report)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR=1", report)
        self.assertIn("a90_kms_begin_frame_no_clear()", report)
        self.assertIn("Run ID: `V3119`", report)
        self.assertIn("dirty-dashboard-regions", report)


if __name__ == "__main__":
    unittest.main()
