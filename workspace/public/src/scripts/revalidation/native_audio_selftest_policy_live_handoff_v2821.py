#!/usr/bin/env python3
"""V2821 live validation for the V2820 audio selftest policy image."""

from __future__ import annotations

import native_audio_status_selftest_live_handoff_v2819 as runner

CYCLE = "V2821"
BUILD_MANIFEST = runner.ROOT / "workspace/private/builds/native-init/v2820-audio-selftest-policy/manifest.json"
CANDIDATE_IMAGE = runner.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2820_audio_selftest_policy.img"
CANDIDATE_VERSION = "0.10.2"
CANDIDATE_TAG = "v2820-audio-selftest-policy"
REPORT_PATH = runner.ROOT / "docs/reports/NATIVE_INIT_V2821_AUDIO_SELFTEST_POLICY_LIVE_2026-06-19.md"
REQUIRED_SELFTEST_MARKERS = [
    "PASS      audio",
    "core=0.10.0",
    "profile=internal-speaker-safe",
    "route=13",
    "speakers=6",
    "cap=200",
    "boost=blocked",
    "sp=unverified",
]


def render_report(result: dict[str, object]) -> str:
    audio = result.get("audio_status_markers", {}) if isinstance(result.get("audio_status_markers"), dict) else {}
    selftest = result.get("selftest_markers", {}) if isinstance(result.get("selftest_markers"), dict) else {}
    return "\n".join([
        "# Native Init V2821 Audio Selftest Policy Live Validation",
        "",
        "## Summary",
        "",
        "- Cycle: `V2821`",
        "- Track: post-promotion audio Tier C device observability.",
        f"- Decision: `{result.get('decision')}`",
        f"- Result directory: `{result.get('out_dir')}`",
        f"- Candidate image: `{runner.rel(CANDIDATE_IMAGE)}`",
        f"- Candidate SHA256: `{result.get('candidate_sha256')}`",
        f"- Candidate version/tag observed: `{int(bool(result.get('candidate_version_ok')))}`",
        f"- `audio status` marker pass: `{int(bool(audio.get('ok')))}` ({audio.get('count', 0)}/{audio.get('required', 0)})",
        f"- `selftest verbose` audio marker pass: `{int(bool(selftest.get('ok')))}` ({selftest.get('count', 0)}/{selftest.get('required', 0)})",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback recovery fallback used: `{int(bool(result.get('rollback_recovery_fallback_used')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Finding",
        "",
        "- V2821 flashes the V2820 `0.10.2` audio selftest policy image and validates the read-only `audio status` plus `selftest verbose` surfaces on hardware.",
        "- Expected pass: `audio status` retains the promoted `0.10.0` core metadata, and `selftest verbose` emits a PASS `audio` row with `boost=blocked` and `sp=unverified`.",
        "- This validation intentionally performs no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, mixer write, speaker write, or playback.",
        "",
        "## Missing Markers",
        "",
        f"- `audio status`: `{audio.get('missing', [])}`",
        f"- `selftest verbose`: `{selftest.get('missing', [])}`",
        "",
        "## Safety",
        "",
        "- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.",
        "- Only the boot partition is written.",
        "- No forbidden partitions are touched.",
        "- Public report contains metadata only; full serial transcripts stay under `workspace/private/runs/audio/`.",
        "",
    ])


def configure_runner() -> None:
    runner.CYCLE = CYCLE
    runner.BUILD_MANIFEST = BUILD_MANIFEST
    runner.CANDIDATE_IMAGE = CANDIDATE_IMAGE
    runner.CANDIDATE_VERSION = CANDIDATE_VERSION
    runner.CANDIDATE_TAG = CANDIDATE_TAG
    runner.REPORT_PATH = REPORT_PATH
    runner.REQUIRED_SELFTEST_MARKERS = list(REQUIRED_SELFTEST_MARKERS)
    runner.render_report = render_report


def main() -> int:
    configure_runner()
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
