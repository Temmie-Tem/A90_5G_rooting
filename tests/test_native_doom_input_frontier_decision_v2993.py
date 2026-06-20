"""Static checks for V2993 DOOM input frontier decision."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workspace/public/src/scripts/revalidation"
RUNNER = SCRIPTS / "native_doom_input_frontier_decision_v2993.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import native_doom_input_frontier_decision_v2993 as runner  # noqa: E402


class TestNativeDoomInputFrontierDecisionV2993(unittest.TestCase):
    def test_runner_is_host_only_metadata_consolidation(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V2993"', text)
        self.assertIn("v2993-doom-input-frontier-pivot-keyboard-fallback", text)
        self.assertIn("Host-only metadata consolidation; no flash", text)
        self.assertNotIn("native_init_flash.py", text)
        self.assertNotIn("a90ctl", text)
        self.assertNotIn("run_serial_step", text)
        self.assertNotIn("run_timeout_doominput", text)
        self.assertNotIn("EVIOCGRAB", text)
        self.assertNotIn("O_WRONLY", text)

    def test_touch_caps_summary_extracts_v2984_metadata(self) -> None:
        sample = {
            "inputcaps": {
                "event6": {
                    "rc": 0,
                    "parsed": {
                        "runtime_status": "unsupported",
                        "decode": {"ev_abs": "1", "btn_touch": "1", "mt_x": "1", "mt_y": "1", "mt_tracking_id": "1"},
                    },
                },
                "event8": {
                    "rc": 0,
                    "parsed": {
                        "runtime_status": "unsupported",
                        "decode": {"ev_abs": "1", "btn_touch": "1", "mt_x": "1", "mt_y": "1", "mt_tracking_id": "1"},
                    },
                },
            }
        }
        rows = runner.touch_caps_summary(sample)
        self.assertEqual([row["event"] for row in rows], ["event6", "event8"])
        self.assertEqual(rows[0]["mt_x"], "1")
        self.assertEqual(rows[1]["runtime_status"], "unsupported")

    def test_v2991_touch_results_extract_zero_event_timeout(self) -> None:
        sample = {
            "event_results": [
                {
                    "event": "event6",
                    "selected_is_touch": True,
                    "inputcaps_touch_ok": True,
                    "doominput_rc": -110,
                    "parsed": {"doominput_event_count": 0, "doominput_state_count": 0, "touch_state_count": 0},
                    "pass": False,
                }
            ]
        }
        rows = runner.v2991_touch_results(sample)
        self.assertEqual(rows[0]["event"], "event6")
        self.assertEqual(rows[0]["doominput_rc"], -110)
        self.assertEqual(rows[0]["touch_states"], 0)
        self.assertFalse(rows[0]["pass"])

    def test_render_report_records_pivot_and_next_action(self) -> None:
        payload = {
            "decision": runner.DECISION,
            "all_touch_nodes_sampled": True,
            "all_touch_zero_event": True,
            "rollback_clean_after_touch_live": True,
            "keyboard_candidates_in_v2991": 0,
            "keyboard_fallback_staged": True,
            "touch_caps": [
                {"event": "event6", "rc": 0, "ev_abs": "1", "btn_touch": "1", "mt_x": "1", "mt_y": "1", "mt_tracking_id": "1", "runtime_status": "unsupported"},
                {"event": "event8", "rc": 0, "ev_abs": "1", "btn_touch": "1", "mt_x": "1", "mt_y": "1", "mt_tracking_id": "1", "runtime_status": "unsupported"},
            ],
            "touch_results": [
                {"event": "event6", "selected_touch": True, "caps_ok": True, "doominput_rc": -110, "doominput_events": 0, "doominput_states": 0, "touch_states": 0, "pass": False},
                {"event": "event8", "selected_touch": True, "caps_ok": True, "doominput_rc": -110, "doominput_events": 0, "doominput_states": 0, "touch_states": 0, "pass": False},
            ],
            "inputs": {"v2984_result": "private-v2984", "v2991_result": "private-v2991", "v2992_report": "public-v2992"},
            "action": "Do not keep re-running identical event6/event8 touch samples.",
        }
        report = runner.render_report(payload)
        self.assertIn("Native Init V2993 DOOM Input Frontier Decision", report)
        self.assertIn("pivot-keyboard-fallback", report)
        self.assertIn("Do not keep re-running identical event6/event8 touch samples", report)
        self.assertIn("V2992 keyboard fallback staged: `1`", report)
        self.assertIn("## Host Validation", report)


if __name__ == "__main__":
    unittest.main()
