from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import native_audio_acdbtap_live_planner_v2476 as v2476
import native_audio_acdbtap_vendor_preload_live_handoff_v2481 as v2481
import native_audio_acdbtap_vendor_preload_planner_v2480 as v2480


class V2481VendorPreloadLiveHandoffTests(unittest.TestCase):
    def args(self) -> Namespace:
        return Namespace(
            adb="adb",
            serial=None,
            out_dir=None,
            module_out_dir=v2480.DEFAULT_MODULE_OUT_DIR,
            materialize_module=True,
            stage_dir=v2476.DEFAULT_STAGE_DIR,
            stimulus_apk=Path("workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk"),
            duration_ms=2000,
            sample_rate=48000,
            amplitude=0.05,
            active_delay_sec=0.75,
            post_delay_sec=1.0,
            capture_observe_sec=8.0,
            android_timeout=240.0,
            adb_command_timeout=45.0,
            flash_timeout=240.0,
            from_native=False,
            android_root_recheck_attempts=4,
            android_root_recheck_sleep_sec=2.0,
        )

    def test_dry_run_declares_vendor_module_preload_and_partial_success_policy(self) -> None:
        payload = v2481.dry_run_payload(self.args())
        flat = json.dumps(payload, sort_keys=True)
        self.assertTrue(payload["command_safety"]["ok"])
        self.assertTrue(payload["module_safety"]["ok"])
        self.assertIn(v2480.MODULE_ID, flat)
        self.assertIn("/vendor/lib/libacdbtap.so", flat)
        self.assertIn("/system/vendor/lib/libacdbtap.so", flat)
        self.assertIn("LD_PRELOAD", flat)
        self.assertIn("A90_ACDBTAP_PRELOAD_CONFIRMED", flat)
        self.assertIn("captured-acdbtap-full-outbuf-set-no-4916", flat)
        self.assertIn("cleanup_exact_module", flat)
        self.assertIn("rollback_v2321", flat)
        self.assertNotIn("setenforce 0", flat)
        self.assertNotIn("magisk --install-module", flat)
        self.assertNotIn("AUDIO_SET_CALIBRATION", flat)

    def test_verified_preload_candidate_requires_matching_sha_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdout = Path(tmp) / "verify.stdout.txt"
            stdout.write_text(
                "missing /vendor/lib/libacdbtap.so\n"
                f"{v2476.TAP_SHA256}  /system/vendor/lib/libacdbtap.so\n"
            )
            record = {"stdout": str(stdout)}
            self.assertEqual(v2481.verified_preload_candidates(record), ["/system/vendor/lib/libacdbtap.so"])
            self.assertEqual(v2481.selected_preload_candidate(record), "/system/vendor/lib/libacdbtap.so")

    def test_verified_preload_candidate_rejects_wrong_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdout = Path(tmp) / "verify.stdout.txt"
            stdout.write_text("0" * 64 + "  /vendor/lib/libacdbtap.so\n")
            record = {"stdout": str(stdout)}
            self.assertEqual(v2481.verified_preload_candidates(record), [])
            self.assertIsNone(v2481.selected_preload_candidate(record))

    def test_manual_start_uses_selected_vendor_path_not_tmp_lib(self) -> None:
        command = v2481.manual_start_vendor_preload_command(self.args(), "/vendor/lib/libacdbtap.so")
        flat = json.dumps(command)
        self.assertIn("LD_PRELOAD=/vendor/lib/libacdbtap.so", flat)
        self.assertIn("A90_ACDBTAP_PRELOAD_CONFIRMED", flat)
        self.assertNotIn("LD_PRELOAD=/data/local/tmp/a90-acdbtap-v2476/lib/libacdbtap.so", flat)

    def test_command_safety_rejects_policy_install_and_native_calibration(self) -> None:
        safety = v2481.command_safety({
            "commands": ["setenforce 0", "magisk --install-module x.zip", "AUDIO_SET_CALIBRATION", "service.sh"],
        })
        names = {item["name"] for item in safety["findings"]}
        self.assertIn("silent_permissive", names)
        self.assertIn("magisk_install_module", names)
        self.assertIn("native_cal_set_symbol", names)
        self.assertIn("service_script", names)


if __name__ == "__main__":
    unittest.main()
