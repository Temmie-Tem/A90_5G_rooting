from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3047_doomgeneric_batch_input.py")
keyboard = load_script("workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py")
dashboard = load_script("workspace/public/src/scripts/revalidation/host_doompad_dashboard_v3035.py")


class NativeDoomgenericBatchInputSourceV3047Tests(unittest.TestCase):
    def test_builder_contract_pins_v3047_batch_input_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3047")
        self.assertEqual(runner.INIT_VERSION, "0.10.82")
        self.assertEqual(runner.INIT_BUILD, "v3047-doomgeneric-batch-input")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3047")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3047-batch-input")
        self.assertEqual(runner.FRAME_PATH, "/tmp/a90-doomgeneric-v3047-batch-input-frame.xbgr8888")
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3047-input.state")
        self.assertEqual(runner.DEFAULT_LOOP_FRAMES, 300)
        self.assertEqual(runner.CONTINUOUS_LOOP_FRAMES, 0)
        self.assertEqual(runner.LOOP_FRAME_MS, 33)
        self.assertIn(b"doompad.batch=state-mask-v3047", runner.REQUIRED_STRINGS)
        self.assertIn(
            b"doompad.mask.bits=forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7",
            runner.REQUIRED_STRINGS,
        )
        self.assertIn(b"doompad.state_batch seq=", runner.REQUIRED_STRINGS)
        self.assertIn(b"doompad state <seq> <mask>", runner.REQUIRED_STRINGS)

    def test_native_doompad_state_mask_command_is_wired(self) -> None:
        source = (REPO_ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(encoding="utf-8")
        help_source = (
            (REPO_ROOT / "workspace/public/src/native-init/v319/60_shell_basic_commands.inc.c").read_text(encoding="utf-8")
            + (REPO_ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c").read_text(encoding="utf-8")
        )

        self.assertIn("#define DOOMPAD_MASK_FORWARD", source)
        self.assertIn("#define DOOMPAD_MASK_RUN", source)
        self.assertIn("doompad_parse_uint", source)
        self.assertIn('strcmp(argv[1], "state") == 0', source)
        self.assertIn("doompad_apply_serial_mask(seq, mask);", source)
        self.assertIn("doompad.state_batch seq=%u mask=0x%02x active=%d", source)
        self.assertIn("doompad.batch=state-mask-v3047", source)
        self.assertIn("doompad.mask=0x%02x", source)
        self.assertIn("doompad [status|reset|state <seq> <mask>|key <role> <0|1>|tap <role>]", help_source)

    def test_host_keyboard_and_dashboard_default_to_batch_input(self) -> None:
        self.assertEqual(keyboard.DEFAULT_HOLD_MS, 110)
        self.assertEqual(keyboard.DEFAULT_POLL_MS, 10)
        self.assertEqual(dashboard.DEFAULT_HOLD_MS, 110)
        self.assertEqual(dashboard.DEFAULT_POLL_MS, 10)
        self.assertEqual(keyboard.doompad_mask_for_roles(("forward", "fire", "run")), 0x91)
        self.assertEqual(keyboard.doompad_state_command(12, 0x91), ["doompad", "state", "12", "0x91"])
        self.assertTrue(keyboard.is_doompad_input_command(["doompad", "state", "12", "0x91"]))
        self.assertTrue(keyboard.is_doompad_input_command(["doompad", "key", "fire", "1"]))

    def test_report_template_records_v3048_next_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3047.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "ramdisk_wad_file_count": 0,
                "wad_embedded_in_boot": 0,
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "input_state_path": runner.INPUT_STATE_PATH,
                "frame_path": runner.FRAME_PATH,
                "engine_ramdisk_path": runner.ENGINE_REMOTE_PATH,
                "engine_binary": "workspace/private/builds/native-init/v3047/doom",
                "engine_binary_sha256": "engine-sha",
                "engine_binary_bytes": 123,
                "helper_bundled_in_ramdisk": True,
            },
            "v3033_marker_strings": [
                "v3047-doomgeneric-batch-input",
                "doompad.batch=state-mask-v3047",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3047 DOOMGENERIC Batch Input Source Build", report)
        self.assertIn("doompad state <seq> <mask>", report)
        self.assertIn("Default hold ms: `110`", report)
        self.assertIn("Run ID: `V3048`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
