"""Static checks for V2996 DOOM input physical-button proxy source build."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workspace/public/src/scripts/revalidation"
MENU_APPS = REPO / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"
RUNNER = SCRIPTS / "build_native_init_boot_v2996_doominput_button_proxy.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_native_init_boot_v2996_doominput_button_proxy as runner  # noqa: E402


class TestNativeDoominputButtonProxySourceV2996(unittest.TestCase):
    def test_build_identity_and_marker_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V2996")
        self.assertEqual(runner.INIT_VERSION, "0.10.66")
        self.assertEqual(runner.INIT_BUILD, "v2996-doominput-button-proxy")
        self.assertTrue(str(runner.BOOT_IMAGE).endswith("boot_linux_v2996_doominput_button_proxy.img"))
        markers = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"doom_button_forward", markers)
        self.assertIn(b"doom_button_back", markers)
        self.assertIn(b"doom_button_fire", markers)

    def test_source_maps_physical_buttons_to_diagnostic_doom_state(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        self.assertIn('case KEY_VOLUMEUP:\n            return "doom_button_forward";', text)
        self.assertIn('case KEY_VOLUMEDOWN:\n            return "doom_button_back";', text)
        self.assertIn('case KEY_POWER:\n            return "doom_button_fire";', text)
        self.assertIn("case KEY_VOLUMEUP:\n        state->forward = down;", text)
        self.assertIn("case KEY_VOLUMEDOWN:\n        state->back = down;", text)
        self.assertIn("case KEY_POWER:\n        state->fire = down;", text)

    def test_source_keeps_read_only_doominput_surface(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")
        self.assertIn("doominput: waiting on %s", text)
        self.assertIn("open(dev_path, O_RDONLY | O_NONBLOCK)", text)
        self.assertIn("doominput_print_state(index, &state)", text)
        self.assertNotIn("EVIOCGRAB", text)
        self.assertNotIn("O_WRONLY", text)
        self.assertNotIn("sendevent", text)

    def test_render_report_names_proxy_as_diagnostic_not_final_controls(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2996_doominput_button_proxy.img",
            "boot_sha256": "abc123",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "v2996_marker_strings": ["doom_button_forward", "doom_button_back", "doom_button_fire"],
        }
        report = runner.render_report(manifest, ("helper",), ("init",))
        self.assertIn("Native Init V2996 DOOM Input Button Proxy Source Build", report)
        self.assertIn("diagnostic physical-button proxy", report)
        self.assertIn("not promoted as the final DOOM control scheme", report)
        self.assertIn("doominput-button-proxy-candidate", report)
        self.assertIn("## Host Validation", report)


if __name__ == "__main__":
    unittest.main()
