#!/usr/bin/env python3
"""V2837 live playback regression for the V2835 audio help-surface candidate."""

from __future__ import annotations

import native_audio_late_manifest_wait_live_handoff_v2808 as runner

runner.CYCLE = "V2837"
runner.REPORT_PATH = (
    runner.ROOT
    / "docs/reports/NATIVE_INIT_V2837_AUDIO_HELP_SURFACE_PLAY_LIVE_2026-06-19.md"
)
runner.BUILD_MANIFEST = (
    runner.ROOT / "workspace/private/builds/native-init/v2835-audio-help-surface/manifest.json"
)
runner.CANDIDATE_IMAGE = (
    runner.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2835_audio_help_surface.img"
)
runner.CANDIDATE_VERSION = "0.10.9"
runner.CANDIDATE_TAG = "v2835-audio-help-surface"
runner.REPORT_TRACK = "post-promotion audio 0.10.9 playback regression."
runner.configure_base_for_v2808()


if __name__ == "__main__":
    raise SystemExit(runner.main())
