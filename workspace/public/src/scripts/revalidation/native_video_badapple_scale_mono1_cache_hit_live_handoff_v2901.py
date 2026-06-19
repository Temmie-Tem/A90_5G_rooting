#!/usr/bin/env python3
"""V2901 live handoff for Bad Apple-scale mono1 SD-cache video streams.

V2900 proved the 6501-frame mono1 stream and populated the SHA-addressed SD
cache. This runner proves the fast repeat path: it requires that cache entry,
does not upload, and does not regenerate the 2.1 GiB local frame stream.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import native_video_gray8_stream_live_handoff_v2893 as video_live

video_live.RUN_ID = "V2901"
video_live.BUILD_TAG = "v2901-video-badapple-scale-mono1-cache-hit-live"
video_live.REPORT_TITLE = "Native Init V2901 Video Bad Apple Scale Mono1 Cache Hit Live Validation"
video_live.DECISION_PREFIX = "v2901-video-badapple-scale-mono1-cache-hit"
video_live.CANDIDATE_IMAGE = (
    video_live.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2897_video_long_mono1_stream.img"
)
video_live.CANDIDATE_VERSION = "0.10.33"
video_live.CANDIDATE_TAG = "v2897-video-long-mono1-stream"
video_live.CANDIDATE_SHA256 = "1d93aa70bf01f9785ab63656cd45d456ec7e180f7510934fbe280082bb31ba32"
video_live.REPORT_PATH = (
    video_live.ROOT / "docs/reports/NATIVE_INIT_V2901_VIDEO_BADAPPLE_SCALE_MONO1_CACHE_HIT_LIVE_2026-06-20.md"
)
video_live.REMOTE_DIR = "/mnt/sdext/a90/runtime/video/v2901"
video_live.REMOTE_MANIFEST = f"{video_live.REMOTE_DIR}/manifest.json"
video_live.REMOTE_STREAM = f"{video_live.REMOTE_DIR}/frames.a90vstr"

FIXTURE_SHA256 = "878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890"
FIXTURE_MANIFEST_SHA256 = "4d437373995d54d26f294571b3e49ea5ae476e7531f007652ff2e80a6732faa6"
FIXTURE_STREAM_BYTES = 2106428092
FIXTURE_FRAME_BYTES = 324000


def badapple_manifest() -> dict[str, Any]:
    return {
        "version": 1,
        "asset_id": "v2874-synthetic-mono1-checker-6501f",
        "video": {
            "path": "frames.a90vstr",
            "format": "mono1",
            "width": 1080,
            "height": 2400,
            "stride": 135,
            "frame_bytes": FIXTURE_FRAME_BYTES,
            "visible_row_bytes": 135,
            "fps_num": 30,
            "fps_den": 1,
            "frame_count": 6501,
            "sha256": FIXTURE_SHA256,
        },
    }


def generate_cached_fixture(args: Any, out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    fixture_dir = out_dir / "fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = fixture_dir / "manifest.json"
    manifest_path.write_text(json.dumps(badapple_manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha = video_live.sha256_file(manifest_path)
    if manifest_sha != FIXTURE_MANIFEST_SHA256:
        raise RuntimeError(f"unexpected fixed manifest sha256: {manifest_sha}")
    return {
        "manifest_path": video_live.rel(manifest_path),
        "stream_path": video_live.rel(fixture_dir / "frames.a90vstr.cache-hit-only-not-generated"),
        "sha256": FIXTURE_SHA256,
        "frame_bytes": FIXTURE_FRAME_BYTES,
        "stream_bytes": FIXTURE_STREAM_BYTES,
        "cache_hit_only": True,
        "local_stream_generated": False,
    }


def configure_args(args: Any) -> Any:
    args.stream_format = "mono1"
    args.pattern = "checker"
    args.stride = (args.width + 7) // 8
    if args.frames == 30:
        args.frames = 6501
    args.require_cache_hit = True
    args.stream_timeout = max(args.stream_timeout, 540.0)
    return args


def main() -> int:
    args = configure_args(video_live.parse_args())
    video_live.generate_fixture = generate_cached_fixture
    out_dir = video_live.ROOT / f"workspace/private/runs/video/{video_live.BUILD_TAG}-{video_live.now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = video_live.preflight_state(args)
    if not args.live:
        payload = video_live.dry_run_payload(args, state)
        payload["fixed_cache"] = {
            "stream_sha256": FIXTURE_SHA256,
            "manifest_sha256": FIXTURE_MANIFEST_SHA256,
            "stream_bytes": FIXTURE_STREAM_BYTES,
            "local_stream_generated": False,
        }
        video_live.write_json(out_dir / "dry_run.json", payload)
        print(video_live.json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if not video_live.preflight_ok(state):
        payload = {
            "decision": f"{video_live.DECISION_PREFIX}-live-preflight-failed-no-flash",
            "pass": False,
            "preflight": state,
        }
        video_live.write_json(out_dir / "result.json", payload)
        video_live.REPORT_PATH.write_text(video_live.render_report(payload), encoding="utf-8")
        print(video_live.json.dumps({
            "decision": payload["decision"],
            "pass": False,
            "out_dir": video_live.rel(out_dir),
        }, indent=2, sort_keys=True))
        return 1
    result = video_live.run_live(args, out_dir, state)
    print(video_live.json.dumps({
        "decision": result.get("decision"),
        "pass": bool(result.get("pass")) and bool(result.get("rollback_version_ok")) and bool(result.get("rollback_selftest_fail0")),
        "out_dir": video_live.rel(out_dir),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
    }, indent=2, sort_keys=True))
    return 0 if result.get("pass") and result.get("rollback_version_ok") and result.get("rollback_selftest_fail0") else 1


if __name__ == "__main__":
    raise SystemExit(main())
