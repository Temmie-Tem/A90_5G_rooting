"""Host-only tests for the V2366 Android AudioTrack stimulus builder."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_revalidation


v2366 = load_revalidation("build_android_audio_route_stimulus_v2366")


def args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "dry_run": True,
        "android_home": None,
        "android_jar": None,
        "javac": None,
        "java_home": None,
        "d8": None,
        "dx": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class AndroidAudioRouteStimulusBuilder(unittest.TestCase):
    def test_dry_run_reports_missing_toolchain_without_building(self) -> None:
        with mock.patch.object(v2366.shutil, "which", return_value=None):
            result = v2366.build(args(dry_run=True))

        self.assertFalse(result["built"])
        self.assertIn("javac", result["missing"])
        self.assertIn("android_jar_exists", result["missing"])
        self.assertIn("d8_or_dx", result["missing"])

    def test_can_build_when_javac_d8_and_android_jar_exist(self) -> None:
        fake_jar = Path(__file__)
        with tempfile.TemporaryDirectory() as temp_dir:
            java_home = Path(temp_dir) / "jdk"
            (java_home / "bin").mkdir(parents=True)
            (java_home / "bin/java").write_text("#!/bin/sh\n")
            (java_home / "bin/javac").write_text("#!/bin/sh\n")
            result = v2366.discover_state(args(
                dry_run=True,
                java_home=java_home,
                d8="/tool/d8",
                android_jar=fake_jar,
            ))

        self.assertTrue(result["source_exists"])
        self.assertTrue(result["android_jar_exists"])
        self.assertEqual(result["javac"], str(java_home / "bin/javac"))
        self.assertEqual(result["java"], str(java_home / "bin/java"))
        self.assertTrue(result["can_build"])

    def test_source_uses_audiotrack_and_bounded_defaults(self) -> None:
        text = v2366.SOURCE.read_text()

        self.assertIn("AudioTrack", text)
        self.assertIn("USAGE_MEDIA", text)
        self.assertIn("DEFAULT_DURATION_MS = 2000", text)
        self.assertIn("DEFAULT_AMPLITUDE = 0.05", text)
        self.assertIn("STATE_INITIALIZED", text)
        self.assertIn("write made no progress", text)
        self.assertNotIn("tinyplay", text)
        self.assertNotIn("/dev/snd", text)


if __name__ == "__main__":
    unittest.main()
