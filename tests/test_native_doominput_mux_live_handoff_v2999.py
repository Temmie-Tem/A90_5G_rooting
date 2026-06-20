"""Static checks for V2999 physical-button doominput mux live handoff."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workspace/public/src/scripts/revalidation"
RUNNER = SCRIPTS / "native_doominput_mux_live_handoff_v2999.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import native_doominput_mux_live_handoff_v2999 as runner  # noqa: E402


class TestNativeDoominputMuxLiveHandoffV2999(unittest.TestCase):
    def test_runner_targets_v2998_mux_candidate(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V2999"', text)
        self.assertIn('CANDIDATE_VERSION = "0.10.67"', text)
        self.assertIn('CANDIDATE_TAG = "v2998-doominput-mux"', text)
        self.assertIn("boot_linux_v2998_doominput_mux.img", text)
        self.assertIn("4828fdfba65c80a5d0a2883c2a8964a82074a6863e03e95f0f8f9aa1e9e138d6", text)
        self.assertEqual(runner.DEFAULT_EVENTS, ("event3", "event0"))

    def test_runner_preserves_flash_and_input_safety_boundaries(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("native_init_flash.py", text)
        self.assertIn("base.rollback_v2321", text)
        self.assertIn("read-only inputscan/inputcaps plus read-only doominputmux evdev sample", text)
        self.assertIn("no input injection, no EVIOCGRAB, no keymap changes, no sysfs writes", text)
        self.assertNotIn("sendevent", text)
        self.assertNotIn("EVIOCGRAB)", text)
        self.assertNotIn("O_WRONLY", text)

    def test_parse_events_arg_requires_event_names_and_caps_count(self) -> None:
        self.assertEqual(runner.parse_events_arg("event3,event0"), ("event3", "event0"))
        with self.assertRaises(Exception):
            runner.parse_events_arg("event3,/dev/input/event0")
        with self.assertRaises(Exception):
            runner.parse_events_arg("event0,event1,event2,event3,event4")
        with self.assertRaises(Exception):
            runner.parse_events_arg("")

    def test_button_mux_caps_ok_accepts_power_or_volume_keys(self) -> None:
        base_caps = {"has_event_header": True, "decode": {"ev_key": "1"}}
        for key in ("key_volup", "key_voldown", "key_power"):
            caps = {"has_event_header": True, "decode": {"ev_key": "1", key: "1"}}
            self.assertTrue(runner.button_mux_caps_ok(caps))
        self.assertFalse(runner.button_mux_caps_ok(base_caps))
        self.assertFalse(runner.button_mux_caps_ok({"has_event_header": True, "decode": {"ev_key": "0", "key_power": "1"}}))

    def test_parse_doominputmux_counts_sources_and_proxy_states(self) -> None:
        text = "\n".join([
            "doominputmux.event 0: source=event3 type=EV_KEY code=KEY_VOLUMEUP role=doom_button_forward value=1",
            "doominputmux.state 0: source=event3 forward=1 back=0 left=0 right=0 fire=0 use=0 menu=0 run=0 touch=0 x=0 y=0 has_x=0 has_y=0 tracking=-1 slot=0 pressure=0 has_pressure=0 active=1 frame=0",
            "doominputmux.event 1: source=event0 type=EV_KEY code=KEY_POWER role=doom_button_fire value=1",
            "doominputmux.state 1: source=event0 forward=1 back=0 left=0 right=0 fire=1 use=0 menu=0 run=0 touch=0 x=0 y=0 has_x=0 has_y=0 tracking=-1 slot=0 pressure=0 has_pressure=0 active=1 frame=0",
        ])
        parsed = runner.parse_doominputmux(text)
        self.assertEqual(parsed["doominputmux_event_count"], 2)
        self.assertEqual(parsed["doominputmux_state_count"], 2)
        self.assertEqual(parsed["active_state_count"], 2)
        self.assertEqual(parsed["proxy_state_count"], 2)
        self.assertEqual(parsed["source_names"], ["event0", "event3"])
        self.assertEqual(runner.proxy_state_fields(parsed), ["fire", "forward"])
        self.assertTrue(runner.has_proxy_button_state(parsed))

    def test_mux_sample_pass_requires_all_events_caps_and_proxy_state(self) -> None:
        result = {
            "candidate_version_ok": True,
            "candidate_selftest_fail0": True,
            "inputscan_rc": 0,
            "event_results": [
                {"selected_is_button": True, "inputcaps_button_ok": True},
                {"selected_is_button": True, "inputcaps_button_ok": True},
            ],
            "doominputmux_rc": 0,
            "doominputmux": {"parsed": {"states": [{"forward": 1, "active": 1}]}},
            "candidate_selftest_after_doominputmux_fail0": True,
        }
        self.assertTrue(runner.mux_sample_pass(result))
        result["event_results"][1]["inputcaps_button_ok"] = False
        self.assertFalse(runner.mux_sample_pass(result))
        result["event_results"][1]["inputcaps_button_ok"] = True
        result["doominputmux"] = {"parsed": {"states": [{"left": 1, "active": 1}]}}
        self.assertFalse(runner.mux_sample_pass(result))

    def test_dry_run_contract_mentions_single_mux_window(self) -> None:
        args = Namespace(events=("event3", "event0"), count=24, timeout_ms=45000)
        state = {
            "candidate": {"sha256_ok": True},
            "rollback": {"sha256_ok": True},
            "fallback_v2237": {"sha256_ok": True},
            "fallback_v48": {"exists": True},
            "flash_helper": {"exists": True},
            "events": ["event3", "event0"],
            "timeout_ms": 45000,
            "count": 24,
        }
        payload = runner.dry_run_payload(args, state)
        self.assertEqual(payload["decision"], "v2999-doominput-mux-dry-run")
        self.assertTrue(payload["ok"])
        self.assertIn("doominputmux event3,event0 24 45000", payload["commands"])
        self.assertTrue(any("single bounded mux window" in item for item in payload["commands"]))

    def test_render_report_lists_mux_fields(self) -> None:
        result = {
            "decision": "v2999-doominput-mux-state-pass-before-rollback",
            "pass": True,
            "live_executed": True,
            "out_dir": "workspace/private/runs/input/example",
            "preflight": {"events": ["event3", "event0"]},
            "inputscan": {"button_candidates": 2, "button_events": [{"event": "event3", "name": "gpio_keys", "class": "buttons"}]},
            "event_results": [{"event": "event3", "selected_is_button": True, "inputcaps_button_ok": True, "inputcaps_rc": 0}],
            "doominputmux_rc": 0,
            "doominputmux": {
                "timeout_ms": 45000,
                "parsed": {
                    "doominputmux_event_count": 2,
                    "doominputmux_state_count": 2,
                    "active_state_count": 1,
                    "proxy_state_count": 1,
                    "max_frame": 0,
                    "source_names": ["event0", "event3"],
                    "states": [{"forward": 1, "active": 1}],
                },
            },
        }
        report = runner.render_report(result)
        self.assertIn("Native Init V2999 DOOM Input Mux Live", report)
        self.assertIn("button_candidates=`2`", report)
        self.assertIn("sources=`event0,event3`", report)
        self.assertIn("proxy_fields=`forward`", report)
        self.assertIn("not a final DOOM control scheme", report)


if __name__ == "__main__":
    unittest.main()
