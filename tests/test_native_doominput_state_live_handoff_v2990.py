"""Static checks for V2990 doominput state live handoff."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workspace/public/src/scripts/revalidation"
RUNNER = SCRIPTS / "native_doominput_state_live_handoff_v2990.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import native_doominput_state_live_handoff_v2990 as runner  # noqa: E402


class TestNativeDoominputStateLiveHandoffV2990(unittest.TestCase):
    def test_runner_targets_v2989_candidate(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn('RUN_ID = "V2990"', text)
        self.assertIn('CANDIDATE_VERSION = "0.10.65"', text)
        self.assertIn('CANDIDATE_TAG = "v2989-doominput-state"', text)
        self.assertIn("boot_linux_v2989_doominput_state.img", text)
        self.assertIn("30e37c64196e7ff2649291c1398c67e96efea9313b25c51dade39d1c62c9ccc2", text)

    def test_runner_preserves_flash_and_input_safety_boundaries(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("native_init_flash.py", text)
        self.assertIn("rollback to v2321 and verify selftest fail=0", text)
        self.assertIn("base.rollback_v2321", text)
        self.assertIn("inputcaps <event>", text)
        self.assertIn("doominput <event>", text)
        self.assertIn("no input injection, no EVIOCGRAB, no keymap changes, no sysfs writes", text)
        self.assertNotIn("sendevent", text)
        self.assertNotIn("EVIOCGRAB)", text)
        self.assertNotIn("O_WRONLY", text)

    def test_parse_doominput_extracts_touch_and_doom_state(self) -> None:
        sample = "\n".join([
            "doominput.event 0: type=EV_ABS code=ABS_MT_POSITION_X role=touch_x value=750",
            "doominput.state 0: forward=0 back=0 left=0 right=0 fire=0 use=0 menu=0 run=0 touch=0 x=750 y=0 has_x=1 has_y=0 tracking=-1 slot=0 pressure=0 has_pressure=0 active=0 frame=0",
            "doominput.event 1: type=EV_KEY code=KEY_W role=doom_forward value=1",
            "doominput.state 1: forward=1 back=0 left=0 right=0 fire=0 use=0 menu=0 run=0 touch=0 x=750 y=0 has_x=1 has_y=0 tracking=-1 slot=0 pressure=0 has_pressure=0 active=1 frame=0",
        ])
        parsed = runner.parse_doominput(sample)
        self.assertEqual(parsed["doominput_event_count"], 2)
        self.assertEqual(parsed["doominput_state_count"], 2)
        self.assertEqual(parsed["touch_state_count"], 2)
        self.assertEqual(parsed["active_state_count"], 1)
        self.assertEqual(parsed["doom_button_state_count"], 1)
        self.assertTrue(parsed["has_touch_state"])
        self.assertTrue(parsed["has_doom_button_state"])
        self.assertEqual(parsed["events"][0]["role"], "touch_x")
        self.assertEqual(parsed["states"][1]["forward"], 1)

    def test_choose_event_auto_prefers_keyboard_then_touch_event6(self) -> None:
        scan = {
            "keyboard_events": [{"event": "event9", "name": "usbkbd", "class": "keyboard"}],
            "touch_events": [{"event": "event6", "name": "sec_touchscreen", "class": "touch"}],
            "events": [
                {"event": "event6", "name": "sec_touchscreen", "class": "touch"},
                {"event": "event9", "name": "usbkbd", "class": "keyboard"},
            ],
        }
        mode, selected = runner.choose_event(scan, None, "auto")
        self.assertEqual(mode, "keyboard")
        self.assertEqual(selected["event"], "event9")

        scan["keyboard_events"] = []
        mode, selected = runner.choose_event(scan, None, "auto")
        self.assertEqual(mode, "touch")
        self.assertEqual(selected["event"], "event6")

    def test_touch_and_keyboard_evaluators_require_state_evidence(self) -> None:
        common = {
            "candidate_version_ok": True,
            "candidate_selftest_fail0": True,
            "inputscan_rc": 0,
            "inputcaps": {"rc": 0, "parsed": {}},
            "doominput_rc": 0,
            "candidate_selftest_after_doominput_fail0": True,
        }
        touch = {
            **common,
            "selected_mode": "touch",
            "selected_event": {"event": "event6", "class": "touch"},
            "inputcaps": {
                "rc": 0,
                "parsed": {
                    "has_event_header": True,
                    "decode": {"ev_abs": "1", "btn_touch": "1", "mt_x": "1", "mt_y": "1", "mt_tracking_id": "1"},
                },
            },
            "doominput": {"parsed": {"has_touch_state": True}},
        }
        keyboard = {
            **common,
            "selected_mode": "keyboard",
            "selected_event": {"event": "event9", "class": "keyboard"},
            "inputcaps": {
                "rc": 0,
                "parsed": {
                    "has_event_header": True,
                    "decode": {
                        "ev_key": "1",
                        "key_w": "1",
                        "key_a": "1",
                        "key_s": "1",
                        "key_d": "1",
                        "key_enter": "1",
                        "key_space": "1",
                        "key_esc": "1",
                    },
                },
            },
            "doominput": {"parsed": {"has_doom_button_state": True}},
        }
        self.assertTrue(runner.evaluate_result(touch))
        self.assertTrue(runner.evaluate_result(keyboard))
        touch["doominput"] = {"parsed": {"has_touch_state": False}}
        self.assertFalse(runner.evaluate_result(touch))

    def test_preflight_and_dry_run_contract_mentions_doominput_state_surface(self) -> None:
        args = Namespace(mode="auto", event=None, count=32, timeout_ms=45000)
        state = {
            "candidate": {"sha256_ok": True},
            "rollback": {"sha256_ok": True},
            "fallback_v2237": {"sha256_ok": True},
            "fallback_v48": {"exists": True},
            "flash_helper": {"exists": True},
            "requested_mode": "auto",
            "timeout_ms": 45000,
            "count": 32,
        }
        payload = runner.dry_run_payload(args, state)
        self.assertEqual(payload["decision"], "v2990-doominput-state-dry-run")
        self.assertTrue(payload["ok"])
        self.assertIn("require doominput.state active/touch/DOOM button state lines", payload["commands"])


if __name__ == "__main__":
    unittest.main()
