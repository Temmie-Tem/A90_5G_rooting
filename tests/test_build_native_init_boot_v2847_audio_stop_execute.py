"""Tests for the V2847 audio stop-execute build wrapper."""

from __future__ import annotations

import importlib
import unittest

v2847 = importlib.import_module("build_native_init_boot_v2847_audio_stop_execute")


class BuildNativeInitBootV2847AudioStopExecuteTest(unittest.TestCase):
    def test_version_axes_are_distinct(self) -> None:
        self.assertEqual(v2847.CYCLE, "V2847")
        self.assertEqual(v2847.INIT_VERSION, "0.10.14")
        self.assertEqual(v2847.INIT_BUILD, "v2847-audio-stop-execute")
        self.assertIn("boot_linux_v2847_audio_stop_execute.img", str(v2847.BOOT_IMAGE))

    def test_configure_retargets_base_builder(self) -> None:
        v2847.configure_base_for_v2847()

        self.assertEqual(v2847.v2845.CYCLE, "V2847")
        self.assertEqual(v2847.v2845.INIT_VERSION, "0.10.14")
        self.assertEqual(v2847.v2845.INIT_BUILD, "v2847-audio-stop-execute")
        self.assertEqual(v2847.v2845.BOOT_IMAGE, v2847.BOOT_IMAGE)

    def test_report_declares_bounded_stop_execute_contract(self) -> None:
        manifest = {
            "decision": v2847.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2847_audio_stop_execute.img",
            "boot_sha256": "a" * 64,
            "init_version": v2847.INIT_VERSION,
            "init_build": v2847.INIT_BUILD,
            "audio_bundled_setcal": {
                "artifact_count": 15,
                "replay_entry_count": 11,
                "native_manifest_sha256": "b" * 64,
            },
            "audio_boot_chime": {
                "enabled": True,
                "best_effort": True,
                "blocks_boot": False,
            },
            "audio_stop_execute": {
                "execute_supported": True,
                "route_reset_layer": "core",
                "playback_stop_mode": "no-active-pcm-handle",
                "setcal_deallocate_mode": "no-active-setcal-session",
                "live_validation": "pending",
            },
        }
        report = v2847.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("audio stop --execute", report)
        self.assertIn("bounded cleanup", report)
        self.assertIn("Route reset layer: `core`", report)
        self.assertIn("no-active-pcm-handle", report)
        self.assertIn("no-active-setcal-session", report)
        self.assertIn("audio-productization-stop-execute-candidate", report)


if __name__ == "__main__":
    unittest.main()
