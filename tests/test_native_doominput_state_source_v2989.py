"""Static checks for V2989 DOOM input state source build."""

from __future__ import annotations

from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
MENU_APPS = REPO / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"
DISPATCH = REPO / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"
HELP = REPO / "workspace/public/src/native-init/v319/60_shell_basic_commands.inc.c"
BUILDER = REPO / "workspace/public/src/scripts/revalidation/build_native_init_boot_v2989_doominput_state.py"
REPORT = REPO / "docs/reports/NATIVE_INIT_V2989_DOOMINPUT_STATE_SOURCE_BUILD_2026-06-20.md"


class TestNativeDoominputStateSourceV2989(unittest.TestCase):
    def test_doominput_command_surface_is_registered(self) -> None:
        dispatch = DISPATCH.read_text(encoding="utf-8")
        help_text = HELP.read_text(encoding="utf-8")
        self.assertIn("static int handle_doominput", dispatch)
        self.assertIn("return cmd_doominput(argv, argc);", dispatch)
        self.assertIn('"doominput", handle_doominput', dispatch)
        self.assertIn("doominput <eventX> [count] [timeout_ms]", dispatch)
        self.assertIn("doominput <eventX> [count] [timeout_ms]", help_text)

    def test_doominput_maps_keyboard_and_touch_state(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        for marker in [
            "struct doominput_state",
            "doominput_apply_key",
            "doominput_apply_abs",
            "doominput_print_state",
            "doominput.event %d: type=%s code=%s role=%s value=%d",
            "doominput.state %d: forward=%d back=%d left=%d right=%d fire=%d use=%d menu=%d run=%d touch=%d",
            "has_x=%d has_y=%d tracking=%d slot=%d pressure=%d has_pressure=%d active=%d frame=%u",
            "KEY_W",
            "KEY_LEFTCTRL",
            "ABS_MT_POSITION_X",
            "ABS_MT_TRACKING_ID",
            "BTN_TOUCH",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_doominput_remains_read_only(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        self.assertIn("fd = open(dev_path, O_RDONLY | O_NONBLOCK);", text)
        self.assertIn("poll(fds, 2, poll_timeout)", text)
        self.assertNotIn("EVIOCGRAB", text)
        self.assertNotIn("sendevent", text)
        self.assertNotIn("O_WRONLY", text)
        self.assertNotIn("write_text_file", text)

    def test_builder_and_report_capture_v2989_contract(self) -> None:
        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn('CYCLE = "V2989"', builder)
        self.assertIn('INIT_VERSION = "0.10.65"', builder)
        self.assertIn('INIT_BUILD = "v2989-doominput-state"', builder)
        self.assertIn("boot_linux_v2989_doominput_state.img", builder)
        self.assertIn("doominput-state-candidate", builder)
        self.assertIn("pending-doominput-live-sample", builder)
        self.assertIn("doominput.state %d: forward=%d", builder)
        self.assertTrue(REPORT.exists())
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("Native Init V2989 DOOM Input State Source Build", report)
        self.assertIn("read-only evdev sampler", report)
        self.assertIn("No PMIC/backlight/GPIO/regulator/GDSC", report)


if __name__ == "__main__":
    unittest.main()
