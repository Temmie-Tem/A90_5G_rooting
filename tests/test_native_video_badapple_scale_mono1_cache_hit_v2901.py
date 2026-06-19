import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import native_video_badapple_scale_mono1_cache_hit_live_handoff_v2901 as cache_live
import native_video_gray8_stream_live_handoff_v2893 as gray8_live


class NativeVideoBadAppleScaleMono1CacheHitV2901(unittest.TestCase):
    def test_wrapper_requires_badapple_scale_cache_hit(self) -> None:
        with mock.patch.object(sys, "argv", ["native_video_badapple_scale_mono1_cache_hit_live_handoff_v2901.py"]):
            args = cache_live.configure_args(cache_live.video_live.parse_args())

        self.assertEqual(args.stream_format, "mono1")
        self.assertEqual(args.pattern, "checker")
        self.assertEqual(args.frames, 6501)
        self.assertEqual(args.stride, 135)
        self.assertTrue(args.require_cache_hit)
        self.assertEqual(args.stream_timeout, 540.0)

    def test_cached_fixture_writes_only_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "workspace/private/test-runs") as temp:
            out_dir = Path(temp)
            fixture = cache_live.generate_cached_fixture(argparse.Namespace(), out_dir, [])
            manifest = ROOT / fixture["manifest_path"]
            stream = ROOT / fixture["stream_path"]

            self.assertTrue(manifest.exists())
            self.assertFalse(stream.exists())
            self.assertEqual(gray8_live.sha256_file(manifest), cache_live.FIXTURE_MANIFEST_SHA256)
            self.assertEqual(fixture["sha256"], cache_live.FIXTURE_SHA256)
            self.assertEqual(fixture["stream_bytes"], cache_live.FIXTURE_STREAM_BYTES)
            self.assertFalse(fixture["local_stream_generated"])

    def test_install_fixture_stops_before_upload_when_fixed_cache_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "workspace/private/test-runs") as temp:
            out_dir = Path(temp)
            fixture = cache_live.generate_cached_fixture(argparse.Namespace(), out_dir, [])
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
            self.assertTrue(result["cache_required"])
            self.assertFalse(result["cache_required_hit_ok"])
            self.assertFalse(result["cache_hit"])
            self.assertFalse(result["cache_uploaded"])
            readiness.assert_not_called()


if __name__ == "__main__":
    unittest.main()
