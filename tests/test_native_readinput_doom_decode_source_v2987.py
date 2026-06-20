"""Static checks for V2987 decoded readinput source build."""

from __future__ import annotations

from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
MENU_APPS = REPO / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"
BUILDER = REPO / "workspace/public/src/scripts/revalidation/build_native_init_boot_v2987_readinput_doom_decode.py"
REPORT = REPO / "docs/reports/NATIVE_INIT_V2987_READINPUT_DOOM_DECODE_SOURCE_BUILD_2026-06-20.md"


class TestNativeReadinputDoomDecodeSourceV2987(unittest.TestCase):
    def test_readinput_numeric_line_is_preserved_and_decode_line_added(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        self.assertIn('a90_console_printf("event %d: type=0x%04x code=0x%04x value=%d\\r\\n"', text)
        self.assertIn("readinput_print_decoded_event(index, &event);", text)
        self.assertIn('event.decode %d: type=%s code=%s role=%s value=%d', text)

    def test_readinput_decodes_touch_protocol_b_landmarks(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        for marker in [
            "EV_ABS",
            "ABS_MT_SLOT",
            "ABS_MT_TRACKING_ID",
            "ABS_MT_POSITION_X",
            "ABS_MT_POSITION_Y",
            "BTN_TOUCH",
            "SYN_REPORT",
            "touch_slot",
            "touch_tracking",
            "touch_x",
            "touch_y",
            "touch_contact",
            "frame",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_readinput_decodes_doom_keyboard_roles_without_writes(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        for marker in [
            "doom_forward",
            "doom_back",
            "doom_left",
            "doom_right",
            "doom_use",
            "doom_fire",
            "doom_menu",
            "doom_run",
            "KEY_W",
            "KEY_LEFTCTRL",
            "KEY_RIGHTSHIFT",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("EVIOCGRAB", text)
        self.assertNotIn("sendevent", text)
        self.assertNotIn("O_WRONLY", text)

    def test_builder_and_report_capture_v2987_contract(self) -> None:
        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn('INIT_VERSION = "0.10.64"', builder)
        self.assertIn('INIT_BUILD = "v2987-readinput-doom-decode"', builder)
        self.assertIn("boot_linux_v2987_readinput_doom_decode.img", builder)
        self.assertIn("readinput-doom-decode-candidate", builder)
        self.assertIn("pending-live-readinput-sample", builder)
        self.assertIn("event.decode %d: type=%s code=%s role=%s value=%d", builder)
        self.assertTrue(REPORT.exists())
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("Native Init V2987 Readinput DOOM Decode Source Build", report)
        self.assertIn("numeric `event N:", report)
        self.assertIn("No PMIC/backlight/GPIO/regulator/GDSC", report)


if __name__ == "__main__":
    unittest.main()
