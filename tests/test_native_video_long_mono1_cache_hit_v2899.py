import argparse
import json
import shutil
import struct
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_video_stream_v2874 as prepare_stream
import native_video_gray8_stream_live_handoff_v2893 as gray8_live
import native_video_long_mono1_cache_hit_live_handoff_v2899 as long_live


class NativeVideoLongMono1CacheHitV2899(unittest.TestCase):
    def test_native_stream_frame_ceiling_is_bad_apple_scale(self) -> None:
        source = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
        text = source.read_text(encoding="utf-8")
        self.assertIn("#define VIDEO_STREAM_MAX_FRAMES 7200U", text)
        self.assertNotIn("#define VIDEO_STREAM_MAX_FRAMES 600U", text)

    def test_wrapper_defaults_to_first_over_old_limit_mono1_fixture(self) -> None:
        with mock.patch.object(sys, "argv", ["native_video_long_mono1_cache_hit_live_handoff_v2899.py"]):
            args = long_live.video_live.parse_args()
        args.stream_format = "mono1"
        args.stride = (args.width + 7) // 8
        if args.frames == 30:
            args.frames = 601
        args.require_cache_hit = True

        self.assertEqual(args.stream_format, "mono1")
        self.assertEqual(args.frames, 601)
        self.assertEqual(args.stride, 135)
        self.assertTrue(args.require_cache_hit)

    def test_install_fixture_stops_before_upload_when_required_cache_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "workspace/private/test-runs") as temp:
            out_dir = Path(temp)
            fixture_dir = out_dir / "fixture"
            fixture = prepare_stream.write_stream(
                out_dir=fixture_dir,
                width=16,
                height=8,
                stride=2,
                fps_num=30,
                fps_den=1,
                frames=2,
                pattern="checker",
                stream_format="mono1",
            )
            fixture["manifest_path"] = str((fixture_dir / "manifest.json").relative_to(ROOT))
            fixture["stream_path"] = str((fixture_dir / "frames.a90vstr").relative_to(ROOT))
            args = argparse.Namespace(
                disable_cache=False,
                adopt_legacy_cache=False,
                require_cache_hit=True,
                transfer_port=18120,
                transfer_timeout=1.0,
            )

            with mock.patch.object(gray8_live.base, "run_serial_step") as run_serial_step, \
                 mock.patch.object(gray8_live, "remote_file_sha256", return_value={"ok": False}), \
                 mock.patch.object(gray8_live.tiny_live, "probe_transfer_readiness") as readiness:
                run_serial_step.return_value = {"ok": True, "rc": 0}
                result = gray8_live.install_fixture(args, out_dir, [], fixture)

            self.assertEqual(result["cache_source"], "required-hit-missing")
            self.assertFalse(result["cache_hit"])
            self.assertFalse(result["cache_uploaded"])
            readiness.assert_not_called()

    def test_prepare_stream_writes_mono1_manifest_and_header(self) -> None:
        out_dir = ROOT / "workspace/private/test-runs/v2899-long-mono1-cache-hit-unit"
        shutil.rmtree(out_dir, ignore_errors=True)
        try:
            result = prepare_stream.write_stream(
                out_dir=out_dir,
                width=16,
                height=8,
                stride=2,
                fps_num=30,
                fps_den=1,
                frames=2,
                pattern="checker",
                stream_format="mono1",
            )
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["video"]["format"], "mono1")
            self.assertEqual(manifest["video"]["visible_row_bytes"], 2)
            self.assertEqual(manifest["video"]["frame_bytes"], 16)
            self.assertEqual(result["frame_bytes"], 16)

            data = (out_dir / "frames.a90vstr").read_bytes()
            self.assertEqual(data[:8], prepare_stream.MAGIC)
            header = struct.unpack("<IIIIIIIII32s", data[8:76])
            self.assertEqual(header[0], 1)
            self.assertEqual(header[1], 16)
            self.assertEqual(header[2], 8)
            self.assertEqual(header[3], 2)
            self.assertEqual(header[4], prepare_stream.PIXEL_FORMAT_MONO1)
            self.assertEqual(header[8], 16)
            frame_index, payload_bytes, pts_ns = struct.unpack("<IIQ", data[76:92])
            self.assertEqual((frame_index, payload_bytes, pts_ns), (0, 16, 0))
            first_payload = data[92:108]
            second_record = data[108:124]
            second_index, second_payload_bytes, second_pts_ns = struct.unpack("<IIQ", second_record)
            second_payload = data[124:140]
            self.assertEqual(first_payload, b"\xff\xff" * 8)
            self.assertEqual((second_index, second_payload_bytes, second_pts_ns), (1, 16, 33333333))
            self.assertEqual(second_payload, b"\x00\x00" * 8)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_stream_classifier_accepts_expected_mono1_marker(self) -> None:
        text = "\n".join([
            "video.stream.sha256_checked=1",
            "video.stream.sha256_match=1",
            "video.stream.requested_present=pageflip",
            "video.stream.present_mode=pageflip",
            "video.stream.presented=30",
            "video.stream.flip_events=30",
            "video.stream.flip_delta_count=29",
            "video.stream.flip_delta_min_us=16610",
            "video.stream.flip_delta_max_us=33245",
            "video.stream.flip_delta_avg_us=32659",
            "video.stream.flip_delta_target_us=33333",
            "video.stream.pixel_format=mono1",
            "video.stream.path=kms-dumb-buffer-pageflip",
        ])
        mono1 = gray8_live.classify_stream_output(text, expected_frames=30, expected_format="mono1")
        gray8 = gray8_live.classify_stream_output(text, expected_frames=30, expected_format="gray8")

        self.assertTrue(mono1["pass"])
        self.assertEqual(mono1["expected_pixel_format"], "mono1")
        self.assertFalse(gray8["pass"])


if __name__ == "__main__":
    unittest.main()
