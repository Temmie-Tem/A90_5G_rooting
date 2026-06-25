from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3141_doomgeneric_demo_hud_large_groups.py")


class NativeDoomgenericDemoHudLargeGroupsSourceV3141Tests(unittest.TestCase):
    def test_builder_contract_pins_v3141_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3141")
        self.assertEqual(runner.INIT_VERSION, "0.10.124")
        self.assertEqual(runner.INIT_BUILD, "v3141-doomgeneric-demo-hud-large-groups")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3141")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3141-demo-hud-large-groups")
        self.assertEqual(runner.NATIVE_DEMO_HUD_FAST, 1)
        self.assertEqual(runner.NATIVE_DEMO_HUD_READABLE, 1)
        self.assertEqual(runner.NATIVE_DEMO_HUD_SECTIONED, 1)
        self.assertEqual(runner.NATIVE_DEMO_HUD_LARGE_GROUPS, 1)
        self.assertIn(runner.DEMO_HUD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.SCALE_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.sectioned_info=1", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.large_groups=1", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.text_scale=group4-main4-sub3-small2", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.layout=top-frame-large-grouped-hw-doom-input-footer", runner.REQUIRED_STRINGS)
        self.assertIn(b"HW INFO", runner.REQUIRED_STRINGS)
        self.assertIn(b"DOOM INFO", runner.REQUIRED_STRINGS)
        self.assertIn(b"KEY INPUT", runner.REQUIRED_STRINGS)
        self.assertIn(b"USB-NCM UDP EVDEV keyboard", runner.REQUIRED_STRINGS)
        self.assertIn(b"MEM %s   LOAD %s", runner.REQUIRED_STRINGS)
        self.assertIn(b"BAT %s %s", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"video.demo.doom.dashboard.layout=top-frame-compact-metrics-input-footer", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"video.demo.doom.dashboard.text_scale=title5-main3-small2", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"compact cached HUD", runner.REQUIRED_STRINGS)
        self.assertNotIn(b"HOST USB-NCM UDP EVDEV keyboard", runner.REQUIRED_STRINGS)

    def test_native_hud_source_has_large_groups_layout_flag_and_strings(self) -> None:
        source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("#define A90_DOOMGENERIC_NATIVE_DEMO_HUD_LARGE_GROUPS 0", source)
        self.assertIn("video.demo.doom.dashboard.large_groups=1", source)
        self.assertIn("video.demo.doom.dashboard.text_scale=group4-main4-sub3-small2", source)
        self.assertIn("top-frame-large-grouped-hw-doom-input-footer", source)
        self.assertIn("large grouped HW / DOOM / key input HUD", source)
        self.assertIn("HW INFO", source)
        self.assertIn("DOOM INFO", source)
        self.assertIn("KEY INPUT", source)
        self.assertIn("CPU %s %s", source)
        self.assertIn("GPU %s %s", source)
        self.assertIn("MEM %s   LOAD %s", source)
        self.assertIn("BAT %s %s", source)

    def test_base_builders_expose_large_groups_compile_flag(self) -> None:
        for relative in (
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py",
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3133_doomgeneric_demo_hud.py",
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3135_doomgeneric_demo_hud_fast.py",
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3137_doomgeneric_demo_hud_readable.py",
        ):
            source = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("NATIVE_DEMO_HUD_LARGE_GROUPS", source)

        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD_LARGE_GROUPS", base_source)

    def test_adapter_source_rewrites_v3137_identity_to_v3141(self) -> None:
        source = runner.v3141_adapter_source()

        self.assertIn(runner.INPUT_THREAD_MARKER, source)
        self.assertIn(runner.TIME_MODEL_MARKER, source)
        self.assertIn(runner.DEMO_HUD_MARKER, source)
        self.assertIn(runner.SCALE_MARKER, source)
        self.assertIn("demo_hud_marker=", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3137", source)
        self.assertNotIn("a90.doomgeneric.v3137", source)
        self.assertNotIn("demo-hud-readable", source)

    def test_configure_v3141_module_repoints_v3137_and_large_groups_flag(self) -> None:
        saved = runner.configure_v3141_module()
        try:
            self.assertEqual(runner.v3137.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3137.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3137.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3137.v3137_adapter_source, runner.v3141_adapter_source)
            self.assertIs(runner.v3137.render_report, runner.render_report)
            self.assertEqual(runner.v3137.NATIVE_DEMO_HUD_SECTIONED, 1)
            self.assertEqual(runner.v3137.NATIVE_DEMO_HUD_LARGE_GROUPS, 1)
            self.assertIn(runner.DEMO_HUD_MARKER, runner.v3137.v3137_adapter_source())
        finally:
            runner.restore_v3137_module(saved)

    def test_report_template_records_large_groups_hud_delta(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3141.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3141 DOOMGENERIC Large Groups Demo HUD Source Build", report)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DEMO_HUD_LARGE_GROUPS=1", report)
        self.assertIn(runner.DEMO_HUD_MARKER, report)


if __name__ == "__main__":
    unittest.main()
