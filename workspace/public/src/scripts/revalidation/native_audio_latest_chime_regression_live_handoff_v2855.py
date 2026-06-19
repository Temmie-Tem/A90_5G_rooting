#!/usr/bin/env python3
"""V2855 live playback regression for latest V2853 audio productization candidate.

This reuses the V2844 standalone bundled-SET-cal chime path but targets the
latest device-validated productization candidate (`0.10.17`). It performs one
bounded low-amplitude `audio chime --execute`, verifies SET-cal/route/PCM
markers, then rolls back to V2321.
"""

from __future__ import annotations

import native_audio_chime_bundled_setcal_live_handoff_v2844 as v2844

runner = v2844.runner

CYCLE = "V2855"
BUILD_MANIFEST = runner.ROOT / "workspace/private/builds/native-init/v2853-audio-productization-marker-refresh/manifest.json"
CANDIDATE_IMAGE = runner.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2853_audio_productization_marker_refresh.img"
CANDIDATE_VERSION = "0.10.17"
CANDIDATE_TAG = "v2853-audio-productization-marker-refresh"
REPORT_PATH = runner.ROOT / "docs/reports/NATIVE_INIT_V2855_AUDIO_LATEST_CHIME_REGRESSION_LIVE_2026-06-19.md"
REPORT_TRACK = "post-promotion latest-candidate audio chime playback regression."


def configure_runner_for_v2855() -> None:
    runner.CYCLE = CYCLE
    runner.BUILD_MANIFEST = BUILD_MANIFEST
    runner.CANDIDATE_IMAGE = CANDIDATE_IMAGE
    runner.CANDIDATE_VERSION = CANDIDATE_VERSION
    runner.CANDIDATE_TAG = CANDIDATE_TAG
    runner.REPORT_PATH = REPORT_PATH
    runner.REPORT_TRACK = REPORT_TRACK
    runner.DEFAULT_REMOTE_ROOT = v2844.BUNDLED_REMOTE_ROOT
    runner.DEFAULT_REMOTE_MANIFEST = v2844.BUNDLED_REMOTE_MANIFEST
    runner.configure_base_for_v2808()


configure_runner_for_v2855()


if __name__ == "__main__":
    raise SystemExit(runner.main())
