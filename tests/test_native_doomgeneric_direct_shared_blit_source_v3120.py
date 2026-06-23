from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3120_doomgeneric_direct_shared_blit.py")


class NativeDoomgenericDirectSharedBlitSourceV3120Tests(unittest.TestCase):
    def test_builder_contract_pins_v3120_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3120")
        self.assertEqual(runner.INIT_VERSION, "0.10.115")
        self.assertEqual(runner.INIT_BUILD, "v3120-doomgeneric-direct-shared-blit")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3120")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3120-direct-shared-blit")
        self.assertEqual(runner.FRAME_WIDTH, 960)
        self.assertEqual(runner.FRAME_HEIGHT, 600)
        self.assertEqual(runner.NO_FULL_CLEAR, 1)
        self.assertEqual(runner.DIRECT_SHARED_BLIT, 1)
        self.assertEqual(runner.FRAME_IPC, "shared-mmap-direct-blit")
        self.assertIn(b"video.demo.doom.loop.presenter.reader=shared-mmap-direct-blit", runner.REQUIRED_STRINGS)

    def test_native_sources_have_direct_shared_blit_path(self) -> None:
        hud = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")
        v3033 = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT", hud)
        self.assertIn("video_demo_doom_frame_reader_direct_shared_source", hud)
        self.assertIn("shared-mmap-direct-blit", hud)
        self.assertIn("DIRECT_SHARED_BLIT = 0", v3033)
        self.assertIn('numeric_define("VIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT", 1)', v3033)

    def test_adapter_source_uses_v3120_paths_and_markers(self) -> None:
        source = runner.v3120_adapter_source()

        self.assertIn(runner.SCALE_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_MARKER, source)
        self.assertIn(runner.PHASE_TELEMETRY_MARKER, source)
        self.assertIn(runner.TICK_TELEMETRY_PATH, source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3118", source)
        self.assertNotIn("a90.doomgeneric.v3118", source)

    def test_apply_globals_sets_direct_shared_blit_flag(self) -> None:
        v3033 = runner.v3118.v3116.v3033_module()
        saved_apply = runner.v3118.apply_v3118_globals
        saved_direct = getattr(v3033, "DIRECT_SHARED_BLIT", None)
        saved_v3118_adapter = runner.v3118.v3118_adapter_source
        saved_v3118_report = runner.v3118.render_report
        try:
            runner.apply_v3120_globals()

            self.assertEqual(runner.v3118.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3118.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3118.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertEqual(v3033.DIRECT_SHARED_BLIT, 1)
            self.assertIs(runner.v3118.v3118_adapter_source, runner.v3120_adapter_source)
            self.assertIs(runner.v3118.render_report, runner.render_report)
        finally:
            runner.v3118.apply_v3118_globals = saved_apply
            runner.v3118.v3118_adapter_source = saved_v3118_adapter
            runner.v3118.render_report = saved_v3118_report
            if saved_direct is not None:
                v3033.DIRECT_SHARED_BLIT = saved_direct

    def test_report_template_records_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3120.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --shared-frame --direct",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3120 DOOMGENERIC Direct Shared Blit Source Build", report)
        self.assertIn("VIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT=1", report)
        self.assertIn("shared-frame payload", report)
        self.assertIn("Run ID: `V3121`", report)
        self.assertIn("shared-mmap-direct-blit", report)


if __name__ == "__main__":
    unittest.main()
