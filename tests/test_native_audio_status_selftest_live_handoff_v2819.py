"""Tests for the V2819 audio status/selftest live-validation runner."""

from __future__ import annotations

import importlib
import json
import unittest

v2819 = importlib.import_module("native_audio_status_selftest_live_handoff_v2819")


class NativeAudioStatusSelftestLiveV2819Test(unittest.TestCase):
    def test_constants_pin_candidate_and_rollback(self) -> None:
        self.assertEqual(v2819.CYCLE, "V2819")
        self.assertEqual(v2819.CANDIDATE_VERSION, "0.10.1")
        self.assertEqual(v2819.CANDIDATE_TAG, "v2818-audio-status-selftest")
        self.assertIn("boot_linux_v2818_audio_status_selftest.img", str(v2819.CANDIDATE_IMAGE))
        self.assertIn("boot_linux_v2321_usb_clean_identity_rodata.img", str(v2819.ROLLBACK_IMAGE))
        self.assertEqual(v2819.ROLLBACK_SHA256, "ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb")

    def test_required_markers_cover_core_promotion_and_safety(self) -> None:
        markers = "\n".join(v2819.REQUIRED_AUDIO_STATUS_MARKERS)
        for required in [
            "audio.status.core.promoted=1",
            "audio.status.core.promotion_run=V2815",
            "audio.status.core.version=0.10.0",
            "audio.status.core.build_tag=v2812-audio-core-promotion-candidate",
            "audio.status.core.validation_run=V2814",
            "audio.status.core.native_play_gate=closed",
            "audio.status.profile.route_control_count=13",
            "audio.status.profile.speaker_count=6",
            "audio.status.safety.amplitude_cap_milli=200",
            "audio.status.safety.smart_amp_boost_write_allowed=0",
            "audio.status.safety.wsa_speaker_protection_verified=0",
        ]:
            self.assertIn(required, markers)

    def test_selftest_markers_cover_audio_row(self) -> None:
        markers = "\n".join(v2819.REQUIRED_SELFTEST_MARKERS)
        for required in ["selftest audio:", "core=0.10.0", "route=13", "speakers=6", "boost=blocked", "sp=unverified"]:
            self.assertIn(required, markers)

    def test_dry_run_is_read_only_after_flash(self) -> None:
        state = {
            "candidate": {"sha256": "6" * 64},
        }
        dry = v2819.dry_run(state)
        rendered = json.dumps(dry["commands"], sort_keys=True)
        self.assertIn("audio", rendered)
        self.assertIn("status", rendered)
        self.assertIn("selftest", rendered)
        for forbidden in ["play", "route", "setcal", "pcm", "tinymix", "tinyplay"]:
            self.assertNotIn(forbidden, rendered)

    def test_marker_helper_reports_missing_values(self) -> None:
        result = v2819.markers_present("a\nb", ["a", "c"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["missing"], ["c"])
        self.assertEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
