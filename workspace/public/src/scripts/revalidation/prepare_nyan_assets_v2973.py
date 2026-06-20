#!/usr/bin/env python3
"""Prepare private Nyan Cat A/V assets for native-init playback.

This host-only wrapper turns an operator-provided private Nyan Cat MP4 into:

- `A90VSTR2` `pal8-rle` video frames for Player HUD playback.
- bounded-volume 48 kHz stereo S16LE PCM audio.

All media inputs and generated payloads stay under `workspace/private`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import prepare_nyan_pal8_rle_v2970 as pal8_encoder


ROOT = repo_root()
RUN_ID = "V2973"
DEFAULT_SOURCE = ROOT / "workspace/private/demo-assets/video/nyancat-src.mp4"
DEFAULT_OUT_ROOT = ROOT / "workspace/private/demo-assets/video/v2973-nyancat-pal8-rle-preview"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2973_NYAN_REAL_ASSET_PREP_2026-06-20.md"
PRIVATE_FFMPEG = ROOT / "workspace/private/tools/bin/ffmpeg"
PRIVATE_FFPROBE = ROOT / "workspace/private/tools/bin/ffprobe"
MAX_AUDIO_VOLUME = 0.2


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tool_path(name: str, private_path: Path) -> str | None:
    if private_path.exists() and private_path.is_file():
        return str(private_path)
    return shutil.which(name)


def ffmpeg_path() -> str | None:
    return tool_path("ffmpeg", PRIVATE_FFMPEG)


def ffprobe_path() -> str | None:
    return tool_path("ffprobe", PRIVATE_FFPROBE)


def fps_expr(fps_num: int, fps_den: int) -> str:
    return str(fps_num) if fps_den == 1 else f"{fps_num}/{fps_den}"


def duration_seconds(max_frames: int | None, fps_num: int, fps_den: int) -> float | None:
    if max_frames is None:
        return None
    return (float(max_frames) * float(fps_den)) / float(fps_num)


def video_base_filter(width: int, height: int, fps_num: int, fps_den: int) -> str:
    return (
        f"fps={fps_expr(fps_num, fps_den)},"
        f"scale=w={width}:h={height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    )


def source_probe_command(ffprobe: str, input_video: Path) -> list[str]:
    return [
        ffprobe,
        "-hide_banner",
        "-loglevel",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,duration",
        "-of",
        "json",
        str(input_video),
    ]


def palette_command(ffmpeg: str,
                    input_video: Path,
                    palette_path: Path,
                    *,
                    width: int,
                    height: int,
                    fps_num: int,
                    fps_den: int,
                    max_frames: int | None,
                    max_colors: int) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_video),
        "-an",
    ]
    duration = duration_seconds(max_frames, fps_num, fps_den)
    if duration is not None:
        command.extend(["-t", f"{duration:.6f}"])
    command.extend([
        "-vf",
        f"{video_base_filter(width, height, fps_num, fps_den)},"
        f"palettegen=max_colors={max_colors}:reserve_transparent=0",
        str(palette_path),
    ])
    return command


def frames_command(ffmpeg: str,
                   input_video: Path,
                   palette_path: Path,
                   frame_pattern: Path,
                   *,
                   width: int,
                   height: int,
                   fps_num: int,
                   fps_den: int,
                   max_frames: int | None) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_video),
        "-i",
        str(palette_path),
        "-an",
        "-lavfi",
        f"{video_base_filter(width, height, fps_num, fps_den)},format=rgb24[x];"
        "[x][1:v]paletteuse=dither=none,format=rgb24",
    ]
    if max_frames is not None:
        command.extend(["-frames:v", str(max_frames)])
    command.extend(["-f", "image2", str(frame_pattern)])
    return command


def audio_command(ffmpeg: str,
                  input_video: Path,
                  audio_path: Path,
                  *,
                  sample_rate: int,
                  channels: int,
                  volume: float,
                  max_frames: int | None,
                  fps_num: int,
                  fps_den: int) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_video),
        "-vn",
    ]
    duration = duration_seconds(max_frames, fps_num, fps_den)
    if duration is not None:
        command.extend(["-t", f"{duration:.6f}"])
    command.extend([
        "-af",
        f"volume={volume}",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        str(audio_path),
    ])
    return command


def run_command(command: list[str], *, timeout: float) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "rc": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout or "",
    }


def frame_count(frame_dir: Path) -> int:
    return len([path for path in frame_dir.glob("frame-*.ppm") if path.is_file()])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_report(payload: dict[str, Any]) -> str:
    output = payload.get("output", {})
    video = output.get("video_manifest", {}) if isinstance(output.get("video_manifest"), dict) else {}
    validation = payload.get("validation", {})
    return "\n".join([
        "# Native Init V2973 Nyan Real Asset Prep",
        "",
        "## Summary",
        "",
        f"- Cycle: `{RUN_ID}`",
        "- Track: Nyan Cat Player HUD / compact color stream enabler.",
        f"- Decision: `{payload.get('decision')}`",
        f"- Result: `{'PASS' if payload.get('ok') else 'BLOCKED'}`",
        "- Scope: host-only private asset preparation; no device flash or runtime state.",
        "- Media policy: source media, rendered frames, PCM, and A90VSTR output remain private and are not committed.",
        "",
        "## Pipeline",
        "",
        "- Video: ffmpeg `palettegen`/`paletteuse` quantizes MP4 frames to a bounded global palette before V2970 encodes `A90VSTR2` `pal8-rle`.",
        "- Audio: ffmpeg renders bounded-volume 48 kHz stereo signed 16-bit little-endian PCM.",
        f"- ffmpeg available: `{int(bool(payload.get('ffmpeg_available')))}`",
        f"- ffprobe available: `{int(bool(payload.get('ffprobe_available')))}`",
        "",
        "## Output",
        "",
        f"- Output root: `{output.get('out_dir')}`",
        f"- Source probe duration: `{payload.get('source_probe', {}).get('format', {}).get('duration', '')}`",
        f"- Frame count: `{output.get('frame_count')}`",
        f"- Video: `{video.get('width')}x{video.get('height')}` @ `{video.get('fps_num')}/{video.get('fps_den')}`",
        f"- Format: `{video.get('format')}`, stream_version=`{video.get('stream_version')}`, palette_count=`{video.get('palette_count')}`",
        f"- Stream SHA256: `{video.get('sha256')}`",
        f"- Stream bytes: `{output.get('stream_bytes')}`",
        f"- Encoded payload bytes: `{video.get('encoded_payload_bytes')}`",
        f"- Raw pal8 bytes: `{video.get('raw_pal8_bytes')}`",
        f"- Raw XBGR bytes: `{video.get('raw_xbgr_bytes')}`",
        f"- Compression ratio milli vs pal8: `{video.get('compression_ratio_milli')}`",
        f"- Audio PCM SHA256: `{output.get('audio_sha256')}`",
        f"- Audio PCM bytes: `{output.get('audio_bytes')}`",
        "",
        "## Validation",
        "",
        f"- `py_compile`: `{int(bool(validation.get('py_compile')))}`",
        f"- focused tests: `{int(bool(validation.get('unit_tests')))}`",
        f"- live host asset run: `{int(bool(validation.get('host_asset_run')))}`",
        "- Encoder roundtrip validation is covered by V2970 tests; this unit exercises it on real private Nyan content.",
        "",
        "## Next",
        "",
        "- Seed this private asset through the existing SD video cache path.",
        "- Wire a `video demo nyan` / menu handler that uses the SHA-addressed stream and bounded PCM loop.",
        "- Then run a rollbackable V2974/V2975 live Player HUD slice before attempting full looping playback.",
    ]) + "\n"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir if args.out_dir else DEFAULT_OUT_ROOT
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    input_video = args.input_video if args.input_video.is_absolute() else ROOT / args.input_video
    frame_dir = out_dir / "frames-ppm"
    palette_path = out_dir / "palette" / "palette.png"
    frame_pattern = frame_dir / "frame-%06d.ppm"
    stream_dir = out_dir / "video-stream"
    audio_path = out_dir / "audio" / "audio.s16le"
    ffmpeg = ffmpeg_path()
    ffprobe = ffprobe_path()
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "decision": "v2973-nyan-real-asset-dry-run" if args.dry_run else "v2973-nyan-real-asset-started",
        "ok": False,
        "ffmpeg_available": bool(ffmpeg),
        "ffprobe_available": bool(ffprobe),
        "input_video_private": rel(input_video) if input_video.exists() and input_video.is_relative_to(ROOT) else str(input_video),
        "output": {
            "out_dir": rel(out_dir),
            "frame_dir": rel(frame_dir),
            "palette_path": rel(palette_path),
            "stream_dir": rel(stream_dir),
            "audio_path": rel(audio_path),
        },
        "settings": {
            "width": args.width,
            "height": args.height,
            "fps_num": args.fps_num,
            "fps_den": args.fps_den,
            "max_frames": args.max_frames,
            "max_colors": args.max_colors,
            "audio_sample_rate": args.audio_sample_rate,
            "audio_channels": args.audio_channels,
            "audio_volume": args.audio_volume,
            "duration_seconds": duration_seconds(args.max_frames, args.fps_num, args.fps_den),
        },
        "commands": {},
        "validation": {
            "py_compile": bool(args.validation_py_compile),
            "unit_tests": bool(args.validation_unit_tests),
        },
    }
    command_ffmpeg = ffmpeg or "ffmpeg"
    command_ffprobe = ffprobe or "ffprobe"
    payload["commands"]["source_probe"] = source_probe_command(command_ffprobe, input_video)
    payload["commands"]["palette"] = palette_command(
        command_ffmpeg,
        input_video,
        palette_path,
        width=args.width,
        height=args.height,
        fps_num=args.fps_num,
        fps_den=args.fps_den,
        max_frames=args.max_frames,
        max_colors=args.max_colors,
    )
    payload["commands"]["frames"] = frames_command(
        command_ffmpeg,
        input_video,
        palette_path,
        frame_pattern,
        width=args.width,
        height=args.height,
        fps_num=args.fps_num,
        fps_den=args.fps_den,
        max_frames=args.max_frames,
    )
    payload["commands"]["audio"] = audio_command(
        command_ffmpeg,
        input_video,
        audio_path,
        sample_rate=args.audio_sample_rate,
        channels=args.audio_channels,
        volume=args.audio_volume,
        max_frames=args.max_frames,
        fps_num=args.fps_num,
        fps_den=args.fps_den,
    )
    return payload


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.audio_volume < 0.0 or args.audio_volume > MAX_AUDIO_VOLUME:
        raise SystemExit(f"--audio-volume must be within 0.0..{MAX_AUDIO_VOLUME}")
    if args.max_colors < 2 or args.max_colors > pal8_encoder.MAX_PALETTE_COLORS:
        raise SystemExit(f"--max-colors must be within 2..{pal8_encoder.MAX_PALETTE_COLORS}")
    payload = build_payload(args)
    if args.dry_run:
        payload["ok"] = bool(payload["commands"].get("palette") and payload["commands"].get("frames"))
        payload["validation"]["dry_run"] = payload["ok"]
        payload["decision"] = "v2973-nyan-real-asset-dry-run"
        return payload
    if not payload["ffmpeg_available"]:
        payload["decision"] = "v2973-nyan-real-asset-blocked-ffmpeg-missing"
        payload["error"] = "ffmpeg is not installed or staged under workspace/private/tools/bin"
        return payload
    input_video = args.input_video if args.input_video.is_absolute() else ROOT / args.input_video
    if not input_video.exists():
        payload["decision"] = "v2973-nyan-real-asset-blocked-input-missing"
        payload["error"] = f"input video not found: {input_video}"
        return payload
    out_dir = ROOT / payload["output"]["out_dir"]
    frame_dir = ROOT / payload["output"]["frame_dir"]
    palette_path = ROOT / payload["output"]["palette_path"]
    stream_dir = ROOT / payload["output"]["stream_dir"]
    audio_path = ROOT / payload["output"]["audio_path"]
    frame_dir.mkdir(parents=True, exist_ok=True)
    palette_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if payload["ffprobe_available"]:
        probe_step = run_command(payload["commands"]["source_probe"], timeout=args.ffmpeg_timeout)
        payload["source_probe_step"] = {key: probe_step[key] for key in ("rc", "ok", "stdout")}
        if probe_step["ok"]:
            payload["source_probe"] = json.loads(probe_step["stdout"])
    palette_step = run_command(payload["commands"]["palette"], timeout=args.ffmpeg_timeout)
    payload["palette_step"] = {key: palette_step[key] for key in ("rc", "ok", "stdout")}
    if not palette_step["ok"]:
        payload["decision"] = "v2973-nyan-real-asset-blocked-palettegen-failed"
        return payload
    frame_step = run_command(payload["commands"]["frames"], timeout=args.ffmpeg_timeout)
    payload["frame_step"] = {key: frame_step[key] for key in ("rc", "ok", "stdout")}
    if not frame_step["ok"]:
        payload["decision"] = "v2973-nyan-real-asset-blocked-frame-render-failed"
        return payload
    count = frame_count(frame_dir)
    if count <= 0:
        payload["decision"] = "v2973-nyan-real-asset-blocked-no-frames"
        payload["error"] = "ffmpeg completed but produced zero PPM frames"
        return payload
    payload["output"]["frame_count"] = count
    audio_step = run_command(payload["commands"]["audio"], timeout=args.ffmpeg_timeout)
    payload["audio_step"] = {key: audio_step[key] for key in ("rc", "ok", "stdout")}
    if not audio_step["ok"]:
        payload["decision"] = "v2973-nyan-real-asset-blocked-audio-render-failed"
        return payload
    payload["output"]["audio_sha256"] = sha256_file(audio_path)
    payload["output"]["audio_bytes"] = audio_path.stat().st_size
    stream = pal8_encoder.write_stream_from_frames(
        input_dir=frame_dir,
        out_dir=stream_dir,
        glob_pattern="frame-*.ppm",
        width=args.width,
        height=args.height,
        fps_num=args.fps_num,
        fps_den=args.fps_den,
        input_format="ppm",
        max_frames=args.max_frames,
        asset_id=args.asset_id,
    )
    stream_path = stream_dir / "frames.a90vstr2"
    cache_compatible_stream = stream_dir / "frames.a90vstr"
    cache_compatible_stream.write_bytes(stream_path.read_bytes())
    manifest_path = stream_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["video"]["path"] = "frames.a90vstr"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stream_sha = sha256_file(cache_compatible_stream)
    (stream_dir / "SHA256SUMS.txt").write_text(
        f"{stream_sha}  frames.a90vstr\n"
        f"{sha256_file(manifest_path)}  manifest.json\n",
        encoding="utf-8",
    )
    payload["stream"] = stream
    payload["output"]["stream_sha256"] = stream_sha
    payload["output"]["stream_bytes"] = cache_compatible_stream.stat().st_size
    payload["output"]["manifest_sha256"] = sha256_file(manifest_path)
    payload["output"]["video_manifest"] = manifest["video"]
    payload["validation"]["host_asset_run"] = True
    payload["decision"] = "v2973-nyan-real-asset-ready"
    payload["ok"] = True
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-video", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--fps-num", type=int, default=30)
    parser.add_argument("--fps-den", type=int, default=1)
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--max-colors", type=int, default=128)
    parser.add_argument("--audio-sample-rate", type=int, default=48000)
    parser.add_argument("--audio-channels", type=int, default=2)
    parser.add_argument("--audio-volume", type=float, default=0.12)
    parser.add_argument("--asset-id", default="nyancat-v2973-pal8-rle-preview")
    parser.add_argument("--ffmpeg-timeout", type=float, default=3600.0)
    parser.add_argument("--result-json", type=Path)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--validation-py-compile", action="store_true")
    parser.add_argument("--validation-unit-tests", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(args)
    result_path = args.result_json
    if result_path is None:
        output_dir = Path(payload["output"]["out_dir"])
        result_path = (ROOT / output_dir if not output_dir.is_absolute() else output_dir) / "v2973-result.json"
    write_json(result_path, payload)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
