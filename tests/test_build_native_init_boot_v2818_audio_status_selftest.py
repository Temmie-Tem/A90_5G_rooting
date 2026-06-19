"""Tests for the V2818 audio status/selftest boot build wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "workspace/public/src/scripts/revalidation/build_native_init_boot_v2818_audio_status_selftest.py"


class NativeAudioStatusSelftestBuildV2818(unittest.TestCase):
    def test_builder_rolls_patch_to_0101(self) -> None:
        text = BUILD_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('CYCLE = "V2818"', text)
        self.assertIn('INIT_VERSION = "0.10.1"', text)
        self.assertIn('INIT_BUILD = "v2818-audio-status-selftest"', text)
        self.assertIn('boot_linux_v2818_audio_status_selftest.img', text)
        self.assertIn('NATIVE_INIT_V2818_AUDIO_STATUS_SELFTEST_SOURCE_BUILD_2026-06-19.md', text)

    def test_builder_documents_observability_scope_and_pending_live_validation(self) -> None:
        text = BUILD_SCRIPT.read_text(encoding="utf-8")

        self.assertIn('audio status', text)
        self.assertIn('selftest verbose', text)
        self.assertIn('audio-observability-candidate', text)
        self.assertIn('pending-live-validation', text)
        self.assertIn('Rollback target remains `v2321-usb-clean-identity-rodata`', text)


if __name__ == "__main__":
    unittest.main()
