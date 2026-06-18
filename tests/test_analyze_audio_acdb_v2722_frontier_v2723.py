"""Tests for V2723 V2722 ACDB frontier analysis."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2723 = load_revalidation("analyze_audio_acdb_v2722_frontier_v2723")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2723-test-"))
    defaults: dict[str, object] = {
        "v2722_run": v2723.DEFAULT_V2722_RUN,
        "v2721_manifest": v2723.DEFAULT_V2721_MANIFEST,
        "v2632_events": v2723.DEFAULT_V2632_EVENTS,
        "report": root / "report.md",
        "write_report": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class AnalyzeAudioAcdbV2722FrontierV2723(unittest.TestCase):
    def test_detects_old_path_cleared_and_new_frontier(self) -> None:
        payload = v2723.build_payload(args())

        self.assertTrue(payload["ok"], payload.get("blockers"))
        self.assertEqual(payload["decision"], "v2723-old-asm-cleared-new-afe-q6asm-frontier")
        self.assertTrue(payload["old_stale_cleared"])
        self.assertTrue(payload["new_frontier_present"])
        self.assertEqual(payload["stale_cal_types_present"], [])
        self.assertTrue(payload["v2722_result"]["rollback_selftest_fail0"])

    def test_order_audit_surfaces_goal_artifact_conflict(self) -> None:
        payload = v2723.build_payload(args())

        self.assertEqual(payload["v2721_per_device_order"], [13, 9, 11, 12, 15, 23, 16, 21])
        self.assertEqual(payload["v2632_event_order"], [13, 9, 11, 12, 15, 23, 16, 21])
        self.assertTrue(payload["per_device_matches_v2632"])
        self.assertEqual(payload["goal_text_order_claim"], [13, 9, 11, 12, 15, 16, 21, 23])
        self.assertTrue(payload["goal_order_conflict_with_v2632_events"])

    def test_report_is_metadata_only_and_names_next_unit(self) -> None:
        ns = args()
        payload = v2723.build_payload(ns)
        v2723.write_report(ns.report, payload)
        text = ns.report.read_text(encoding="utf-8")

        self.assertIn("AUDIO_SET_CALIBRATION", text)
        self.assertIn("ADSP_EBADPARAM", text)
        self.assertIn("GOAL text order conflicts", text)
        self.assertNotIn("bytes_hex", text)
        self.assertNotIn("payload.bin", text)


if __name__ == "__main__":
    unittest.main()
