"""Tests for the V2845 audio boot-chime builder."""

from __future__ import annotations

import importlib
import unittest

v2845 = importlib.import_module("build_native_init_boot_v2845_audio_boot_chime")


class BuildNativeInitBootV2845AudioBootChimeTest(unittest.TestCase):
    def test_builder_targets_fresh_boot_chime_candidate(self) -> None:
        self.assertEqual(v2845.CYCLE, "V2845")
        self.assertEqual(v2845.INIT_VERSION, "0.10.13")
        self.assertEqual(v2845.INIT_BUILD, "v2845-audio-boot-chime")
        self.assertIn("boot_linux_v2845_audio_boot_chime.img", str(v2845.BOOT_IMAGE))
        self.assertEqual(v2845.BOOT_CHIME_FLAG, "-DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1")

    def test_render_report_declares_best_effort_boot_boundary(self) -> None:
        report = v2845.render_report(
            {
                "decision": "v2845-test",
                "boot_image": "workspace/private/inputs/boot_images/test.img",
                "boot_sha256": "b" * 64,
                "init_version": "0.10.13",
                "init_build": "v2845-audio-boot-chime",
                "audio_bundled_setcal": {
                    "artifact_count": 15,
                    "replay_entry_count": 11,
                    "native_manifest_sha256": "c" * 64,
                },
                "audio_boot_chime": {
                    "enabled": True,
                    "best_effort": True,
                    "blocks_boot": False,
                    "parent_candidate": "v2843-audio-bundled-setcal",
                },
            },
            ("helper",),
            ("flag", v2845.BOOT_CHIME_FLAG),
        )

        self.assertIn("V2845", report)
        self.assertIn("AUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1", report)
        self.assertIn("best-effort", report)
        self.assertIn("does not wait for playback", report)
        self.assertIn("Boot chime blocks boot: `0`", report)


if __name__ == "__main__":
    unittest.main()
