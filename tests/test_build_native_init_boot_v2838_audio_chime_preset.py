"""Tests for the V2838 audio chime preset boot-image builder."""

from __future__ import annotations

import importlib
import unittest

v2838 = importlib.import_module("build_native_init_boot_v2838_audio_chime_preset")


class BuildNativeInitBootV2838AudioChimePresetTest(unittest.TestCase):
    def test_identity_and_paths_are_v2838(self) -> None:
        self.assertEqual(v2838.CYCLE, "V2838")
        self.assertEqual(v2838.INIT_VERSION, "0.10.10")
        self.assertEqual(v2838.INIT_BUILD, "v2838-audio-chime-preset")
        self.assertIn("boot_linux_v2838_audio_chime_preset.img", str(v2838.BOOT_IMAGE))
        self.assertIn("NATIVE_INIT_V2838_AUDIO_CHIME_PRESET_SOURCE_BUILD", str(v2838.REPORT_PATH))

    def test_report_names_chime_delta_and_safety_boundary(self) -> None:
        manifest = {
            "decision": v2838.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2838_audio_chime_preset.img",
            "boot_sha256": "a" * 64,
            "init_version": v2838.INIT_VERSION,
            "init_build": v2838.INIT_BUILD,
        }
        report = v2838.render_report(manifest, ("-DTEST=1",), ("-DINIT=1",))
        self.assertIn("V2838", report)
        self.assertIn("0.10.10", report)
        self.assertIn("manual `audio chime` preset", report)
        self.assertIn("amplitude `80` milli", report)
        self.assertIn("duration `1200` ms", report)
        self.assertIn("audio.chime.boot_autoplay_default=0", report)
        self.assertIn("Device flash: `no`", report)

    def test_metadata_rewrite_marks_productization_candidate(self) -> None:
        source = v2838.__loader__.get_source(v2838.__name__)
        self.assertIsNotNone(source)
        assert source is not None

        self.assertIn('"audio-chime-preset"', source)
        self.assertIn('"audio-chime-dry-run-default"', source)
        self.assertIn('"audio-chime-boot-autoplay-disabled"', source)
        self.assertIn('"audio-productization-candidate"', source)
        self.assertIn('"pending-live-validation"', source)


if __name__ == "__main__":
    unittest.main()
