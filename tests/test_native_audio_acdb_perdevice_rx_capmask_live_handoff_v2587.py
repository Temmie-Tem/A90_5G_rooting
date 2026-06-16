"""Host-only tests for the V2587 ACDB RX cap-mask live wrapper."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from _loader import load_revalidation

v2587 = load_revalidation("native_audio_acdb_perdevice_rx_capmask_live_handoff_v2587")


class AcdbPerdeviceRxCapmaskRunnerV2587(unittest.TestCase):
    def test_selected_artifacts_requires_v2586_arg2_one_contract(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2587-artifacts-"))
        helper = root / "helper"
        preload = root / "preload.so"
        helper.write_bytes(b"helper")
        preload.write_bytes(b"preload")
        helper.chmod(0o600)
        preload.chmod(0o600)
        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "ok": True,
                    "capture_contract": {"per_device_call": "acdb_loader_send_audio_cal_v5(15, 1, 0x11135, 48000, 48000, 0, 1)"},
                    "sources": {"required": {"preinit_rx_path_compile_override_guard": True}},
                    "build": {
                        "artifacts": {
                            "helper": {"ok": True, "path": str(helper), "sha256": hashlib.sha256(b"helper").hexdigest()},
                            "preload": {"ok": True, "path": str(preload), "sha256": hashlib.sha256(b"preload").hexdigest()},
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        args = Namespace(
            build_v2586_artifacts=False,
            v2586_manifest_path=manifest,
            helper_path=None,
            helper_sha256=None,
            preload_path=None,
            preload_sha256=None,
        )

        artifacts = v2587.selected_artifacts(args)

        self.assertTrue(artifacts["ok"], artifacts)
        self.assertTrue(artifacts["manifest"]["arg2_one_contract"])
        self.assertTrue(artifacts["manifest"]["source_override_ok"])

    def test_to_v2490_args_selects_combined_preload_and_fake_allocate(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2587-args-"))
        helper = root / "helper"
        preload = root / "preload.so"
        helper.write_bytes(b"helper")
        preload.write_bytes(b"preload")
        artifacts = {
            "helper": {"path": str(helper), "sha256": hashlib.sha256(b"helper").hexdigest()},
            "preload": {"path": str(preload), "sha256": hashlib.sha256(b"preload").hexdigest()},
        }
        args = Namespace(
            dry_run=True,
            run_live=False,
            out_dir=None,
            adb="adb",
            serial=None,
            from_native=True,
            android_timeout=240.0,
            flash_timeout=420.0,
            adb_command_timeout=90.0,
            adb_pull_timeout=120.0,
            helper_timeout=120.0,
            android_root_recheck_attempts=v2587.v2573.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS,
            android_root_recheck_sleep_sec=v2587.v2573.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC,
            android_settle_adb_retry_attempts=v2587.v2573.v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS,
            android_settle_adb_retry_sleep_sec=v2587.v2573.v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC,
            readelf="readelf",
            file="file",
        )

        base = v2587.to_v2490_args(args, artifacts)

        self.assertTrue(base.use_combined_preload)
        self.assertTrue(base.fake_audio_cal_allocate)
        self.assertFalse(base.enable_acdbtap_preload)
        self.assertEqual(base.helper_path, helper)
        self.assertEqual(base.combined_preload_so, preload)


if __name__ == "__main__":
    unittest.main()
