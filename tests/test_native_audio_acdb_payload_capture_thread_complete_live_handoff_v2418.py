"""Host-only tests for the V2418 thread-complete ACDB capture handoff."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2418 = load_revalidation("native_audio_acdb_payload_capture_thread_complete_live_handoff_v2418")


def args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "materialize_capture_helper": False,
        "helper_out_dir": v2418.v2415.DEFAULT_HELPER_OUT_DIR,
        "cc": v2418.v2415.DEFAULT_CC,
        "stimulus_apk": v2418.v2396.DEFAULT_STIMULUS_APK,
        "adb": "adb",
        "serial": None,
        "android_timeout": 420.0,
        "adb_command_timeout": 120.0,
        "flash_timeout": 900.0,
        "duration_ms": 2000,
        "sample_rate": 48000,
        "amplitude": 0.05,
        "active_delay_sec": 0.75,
        "post_delay_sec": 1.0,
        "capture_duration_sec": 8,
        "capture_warmup_sec": 0.0,
        "max_bytes": 512,
        "from_native": True,
        "approval": "",
        "out_dir": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class AcdbThreadCompleteLiveHandoff(unittest.TestCase):
    def test_dry_run_declares_v2418_thread_complete_m0(self) -> None:
        payload = v2418.dry_run(args())

        self.assertEqual(payload["run_id"], "V2418")
        self.assertEqual(payload["decision"], "v2418-acdb-thread-complete-capture-live-dry-run")
        self.assertTrue(payload["thread_complete_m0"])
        self.assertIn("deferred", payload["magisk_module_escalation"])
        self.assertEqual(payload["approval_phrase_required_for_live"], v2418.APPROVAL_PHRASE)

    def test_rewrite_payload_identity_preserves_summary_and_relabels_decision(self) -> None:
        payload = {
            "run_id": "V2416",
            "build_tag": "old",
            "decision": "v2416-acdb-payload-capture-events-before-rollback-rollback-pass",
            "payload_capture_summary": {"classification": "captured-msm-audio-cal-payload-events"},
        }

        rewritten = v2418.rewrite_payload_identity(payload)

        self.assertEqual(rewritten["run_id"], "V2418")
        self.assertEqual(rewritten["build_tag"], "v2418-audio-acdb-thread-complete-live")
        self.assertEqual(rewritten["decision"], "v2418-acdb-thread-complete-capture-events-before-rollback-rollback-pass")
        self.assertTrue(rewritten["thread_complete_m0"])
        self.assertEqual(rewritten["v2417_observer_fix"]["trace_target"], "--pid <tid>")

    def test_run_live_sets_v2418_out_dir_before_delegating(self) -> None:
        original_run_live = v2418.v2416.run_live

        def fake_run_live(namespace: argparse.Namespace) -> dict[str, object]:
            self.assertIsNotNone(namespace.out_dir)
            out_dir = Path(namespace.out_dir)
            out_dir.mkdir(parents=True)
            (out_dir / "result.json").write_text("{}\n")
            return {
                "run_id": "V2416",
                "build_tag": "old",
                "decision": "v2416-acdb-payload-capture-no-msm-audio-cal-ioctl-observed-before-rollback-rollback-pass",
                "out_dir": v2418.rel(out_dir),
                "ok": True,
                "rolled_back": True,
            }

        v2418.v2416.run_live = fake_run_live
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                payload = v2418.run_live(args(out_dir=Path(temp_dir) / "run"))
                saved = json.loads((Path(temp_dir) / "run" / "result.json").read_text())
        finally:
            v2418.v2416.run_live = original_run_live

        self.assertEqual(payload["run_id"], "V2418")
        self.assertEqual(saved["run_id"], "V2418")
        self.assertIn("thread-complete", payload["decision"])


if __name__ == "__main__":
    unittest.main()
