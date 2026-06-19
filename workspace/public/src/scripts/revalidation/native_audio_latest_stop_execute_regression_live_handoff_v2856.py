#!/usr/bin/env python3
"""V2856 latest-candidate audio stop-execute regression live handoff.

This reuses the V2848 bounded `audio stop --execute` validation path but targets
latest productization candidate `0.10.17`. It flashes the candidate, lets the
bundled boot chime settle, runs one `audio stop internal-speaker-safe --execute`,
verifies bounded no-active cleanup + core route-reset markers, then rolls back to
V2321.
"""

from __future__ import annotations

import native_audio_stop_execute_live_handoff_v2848 as v2848

runner = v2848.runner

CYCLE = "V2856"
BUILD_MANIFEST = runner.ROOT / "workspace/private/builds/native-init/v2853-audio-productization-marker-refresh/manifest.json"
CANDIDATE_IMAGE = runner.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2853_audio_productization_marker_refresh.img"
CANDIDATE_VERSION = "0.10.17"
CANDIDATE_TAG = "v2853-audio-productization-marker-refresh"
REPORT_PATH = runner.ROOT / "docs/reports/NATIVE_INIT_V2856_AUDIO_LATEST_STOP_EXECUTE_REGRESSION_LIVE_2026-06-19.md"
REPORT_TRACK = "post-promotion latest-candidate audio stop-execute regression."


def configure_runner_for_v2856() -> None:
    runner.CYCLE = CYCLE
    runner.BUILD_MANIFEST = BUILD_MANIFEST
    runner.CANDIDATE_IMAGE = CANDIDATE_IMAGE
    runner.CANDIDATE_VERSION = CANDIDATE_VERSION
    runner.CANDIDATE_TAG = CANDIDATE_TAG
    runner.REPORT_PATH = REPORT_PATH
    runner.REPORT_TRACK = REPORT_TRACK
    runner.DEFAULT_REMOTE_ROOT = v2848.BUNDLED_REMOTE_ROOT
    runner.DEFAULT_REMOTE_MANIFEST = v2848.BUNDLED_REMOTE_MANIFEST
    runner.configure_base_for_v2808()


configure_runner_for_v2856()


if __name__ == "__main__":
    raise SystemExit(runner.main())
