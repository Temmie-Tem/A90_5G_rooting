from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3137_doomgeneric_demo_hud_readable.py")


class NativeDoomgenericDemoHudReadableSourceV3137Tests(unittest.TestCase):
    def test_builder_contract_pins_v3137_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3137")
        self.assertEqual(runner.INIT_VERSION, "0.10.122")
        self.assertEqual(runner.INIT_BUILD, "v3137-doomgeneric-demo-hud-readable")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3137")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3137-demo-hud-readable")
        self.assertEqual(runner.NATIVE_DEMO_HUD_FAST, 1)
        self.assertEqual(runner.NATIVE_DEMO_HUD_READABLE, 1)
        self.assertIn(runner.DEMO_HUD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.SCALE_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.readable_spacing=1", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.text_scale=title5-main3-small2", runner.REQUIRED_STRINGS)
        self.assertIn(b"HOST USB-NCM UDP EVDEV keyboard", runner.REQUIRED_STRINGS)
        self.assertIn(b"POWER / VOL = EXIT", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"HOST host_doompad_keyboard_v3033.py UDP EVDEV", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"POWER VOL EXIT   HOST KEYS VIA USB NCM", runner.REQUIRED_STRINGS)

    def test_native_hud_source_has_readable_layout_flag_and_strings(self) -> None:
        source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("#define A90_DOOMGENERIC_NATIVE_DEMO_HUD_READABLE 0", source)
        self.assertIn("video.demo.doom.dashboard.readable_spacing=1", source)
        self.assertIn("video.demo.doom.dashboard.text_scale=title5-main3-small2", source)
        self.assertIn("HOST USB-NCM UDP EVDEV keyboard", source)
        self.assertIn("POWER / VOL = EXIT", source)

    def test_base_builders_expose_readable_compile_flag(self) -> None:
        for relative in (
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py",
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3133_doomgeneric_demo_hud.py",
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3135_doomgeneric_demo_hud_fast.py",
        ):
            source = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("NATIVE_DEMO_HUD_READABLE", source)

        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD_READABLE", base_source)

    def test_adapter_source_rewrites_v3135_identity_to_v3137(self) -> None:
        source = runner.v3137_adapter_source()

        self.assertIn(runner.INPUT_THREAD_MARKER, source)
        self.assertIn(runner.TIME_MODEL_MARKER, source)
        self.assertIn(runner.DEMO_HUD_MARKER, source)
        self.assertIn(runner.SCALE_MARKER, source)
        self.assertIn("demo_hud_marker=", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3135", source)
        self.assertNotIn("a90.doomgeneric.v3135", source)
        self.assertNotIn("producer-960x600-1to1-smooth-demo-direct-shared-blit", source)

    def test_configure_v3137_module_repoints_v3135_and_readable_flag(self) -> None:
        saved = runner.configure_v3137_module()
        try:
            self.assertEqual(runner.v3135.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3135.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3135.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3135.v3135_adapter_source, runner.v3137_adapter_source)
            self.assertIs(runner.v3135.render_report, runner.render_report)
            self.assertEqual(runner.v3135.NATIVE_DEMO_HUD_READABLE, 1)
            self.assertIn(runner.DEMO_HUD_MARKER, runner.v3135.v3135_adapter_source())
        finally:
            runner.restore_v3135_module(saved)

    def test_report_template_records_readable_hud_delta(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3137.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3137 DOOMGENERIC Readable Demo HUD Source Build", report)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD_READABLE=1", report)
        self.assertIn(runner.DEMO_HUD_MARKER, report)


if __name__ == "__main__":
    unittest.main()
