# Native Init V2993 DOOM Input Frontier Decision

## Summary

- Decision: `v2993-doom-input-frontier-pivot-keyboard-fallback`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM input prerequisite.
- Built-in touch nodes sampled: `1`
- Built-in touch zero-event result: `1`
- V2991 rollback clean: `1`
- Keyboard candidates seen in V2991 inputscan: `0`
- V2992 keyboard fallback staged: `1`

## Touch Capability Baseline

| Event | rc | EV_ABS | BTN_TOUCH | MT_X | MT_Y | MT_TRACKING_ID | runtime_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `event6` | `0` | `1` | `1` | `1` | `1` | `1` | `unsupported` |
| `event8` | `0` | `1` | `1` | `1` | `1` | `1` | `unsupported` |

## Latest Touch Live Result

| Event | selected_touch | caps_ok | doominput_rc | events | states | touch_states | pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `event6` | `1` | `1` | `-110` | `0` | `0` | `0` | `0` |
| `event8` | `1` | `1` | `-110` | `0` | `0` | `0` | `0` |

## Decision

- V2984 showed both `event6 sec_touchscreen` and `event8 sec_touchpad` expose touch/MT capability bits; runtime PM reported `unsupported`, not `suspended`.
- V2991 then sampled both known touch-class nodes under the V2989 `doominput.state` candidate, and both bounded windows timed out with zero `doominput.event` and zero `doominput.state` lines.
- Repeating the same touch sample without a deliberate input-state change or a new touch-driver hypothesis is low-information.
- V2992 already stages the USB-keyboard/OTG fallback on the same `doominput.state` surface. That is the next live path when a keyboard-class event appears.

## Next Action

- Do not keep re-running identical event6/event8 touch samples. Run V2992 live only when USB keyboard/OTG hardware is attached, or reopen touch with a new evidence-backed hypothesis.

## Evidence Inputs

- V2984 result: `workspace/private/runs/input/v2984-inputcaps-touch-diag-live-20260620-164505/result.json`
- V2991 result: `workspace/private/runs/input/v2991-doominput-dual-touch-live-20260620-181451/result.json`
- V2992 report: `docs/reports/NATIVE_INIT_V2992_DOOMINPUT_KEYBOARD_STATE_LIVE_HANDOFF_DRY_RUN_2026-06-20.md`

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v2993.py tests/test_native_doom_input_frontier_decision_v2993.py`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_input_frontier_decision_v2993`: PASS (`4` tests)
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v2993.py`: PASS (host-only report materialized)
- `git diff --check`: PASS

## Safety

- Host-only metadata consolidation; no flash, no serial command, no evdev open, no input injection, no sysfs writes.
- No Wi-Fi/audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- Private raw command outputs remain under `workspace/private/runs/`; this report includes metadata only.
