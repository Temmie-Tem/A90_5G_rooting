"""Static checks for V3003 DOOM input frontier decision."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workspace/public/src/scripts/revalidation"
RUNNER = SCRIPTS / "native_doom_input_frontier_decision_v3003.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import native_doom_input_frontier_decision_v3003 as runner  # noqa: E402


class TestNativeDoomInputFrontierDecisionV3003(unittest.TestCase):
    def test_runner_is_host_only_metadata_consolidation(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V3003"', text)
        self.assertIn("v3003-doom-input-frontier-hardware-stimulus-gated", text)
        self.assertIn("Host-only metadata consolidation; no flash", text)
        self.assertNotIn("native_init_flash.py", text)
        self.assertNotIn("a90ctl", text)
        self.assertNotIn("run_serial_step", text)
        self.assertNotIn("EVIOCGRAB", text)
        self.assertNotIn("O_WRONLY", text)

    def test_v3002_event_rows_extract_button_capability(self) -> None:
        sample = {
            "event_results": [
                {
                    "event": "event3",
                    "selected_is_button": True,
                    "inputcaps_button_ok": True,
                    "inputcaps_rc": 0,
                    "selected_event": {"name": "gpio_keys", "class": "buttons"},
                },
                {
                    "event": "event0",
                    "selected_is_button": True,
                    "inputcaps_button_ok": True,
                    "inputcaps_rc": 0,
                    "selected_event": {"name": "qpnp_pon", "class": "buttons"},
                },
            ]
        }
        rows = runner.v3002_event_rows(sample)
        self.assertEqual([row["event"] for row in rows], ["event3", "event0"])
        self.assertEqual(rows[0]["name"], "gpio_keys")
        self.assertTrue(all(row["selected_is_button"] and row["inputcaps_button_ok"] for row in rows))

    def test_v3002_mux_summary_extracts_zero_event_timeout(self) -> None:
        sample = {
            "doominputmux_rc": -110,
            "doominputmux": {
                "timeout_ms": 60000,
                "duration_sec": 60.072,
                "parsed": {
                    "doominputmux_event_count": 0,
                    "doominputmux_state_count": 0,
                    "active_state_count": 0,
                    "proxy_state_count": 0,
                    "source_names": [],
                },
            },
        }
        summary = runner.v3002_mux_summary(sample)
        self.assertEqual(summary["rc"], -110)
        self.assertEqual(summary["event_count"], 0)
        self.assertEqual(summary["proxy_state_count"], 0)
        self.assertEqual(summary["timeout_ms"], 60000)

    def test_render_report_records_hardware_stimulus_gate(self) -> None:
        payload = {
            "decision": runner.DECISION,
            "touch_pivot_present": True,
            "keyboard_fallback_staged": True,
            "button_capable": True,
            "physical_button_mux_zero_event": True,
            "v3002_rollback_clean": True,
            "button_event_rows": [
                {"event": "event3", "name": "gpio_keys", "class": "buttons", "selected_is_button": True, "inputcaps_button_ok": True, "inputcaps_rc": 0},
                {"event": "event0", "name": "qpnp_pon", "class": "buttons", "selected_is_button": True, "inputcaps_button_ok": True, "inputcaps_rc": 0},
            ],
            "mux_summary": {
                "rc": -110,
                "timeout_ms": 60000,
                "duration_sec": 60.072,
                "event_count": 0,
                "state_count": 0,
                "active_state_count": 0,
                "proxy_state_count": 0,
                "source_names": [],
            },
            "inputs": {
                "v2993_report": "docs/reports/v2993.md",
                "v2992_report": "docs/reports/v2992.md",
                "v3002_result": "workspace/private/runs/input/v3002/result.json",
                "v3002_report": "docs/reports/v3002.md",
            },
            "next_action": "Do not repeat the same event3,event0 mux live run unless an operator is explicitly available.",
        }
        report = runner.render_report(payload)
        self.assertIn("Native Init V3003 DOOM Input Frontier Decision", report)
        self.assertIn("hardware-stimulus-gated", report)
        self.assertIn("V3002 physical-button mux zero-event result: `1`", report)
        self.assertIn("Do not repeat the same event3,event0 mux live run", report)
        self.assertIn("USB keyboard/OTG remains the next higher-information fallback path", report)
        self.assertIn("Host-only metadata consolidation; no flash", report)


if __name__ == "__main__":
    unittest.main()
