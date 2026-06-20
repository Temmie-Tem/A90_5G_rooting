# Native Init V3003 DOOM Input Frontier Decision

## Summary

- Decision: `v3003-doom-input-frontier-hardware-stimulus-gated`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM input prerequisite.
- Touch zero-event pivot present: `1`
- Keyboard fallback staged: `1`
- V3002 button events button-capable: `1`
- V3002 physical-button mux zero-event result: `1`
- V3002 rollback clean: `1`

## V3002 Button Candidate Evidence

| Event | name | class | selected_buttons | caps_ok | inputcaps_rc |
| --- | --- | --- | --- | --- | --- |
| `event3` | `gpio_keys` | `buttons` | `1` | `1` | `0` |
| `event0` | `qpnp_pon` | `buttons` | `1` | `1` | `0` |

## V3002 Mux Evidence

- `doominputmux` rc: `-110`
- Timeout: `60000` ms
- Duration: `60.072` sec
- Events: `0`
- States: `0`
- Active states: `0`
- Proxy states: `0`
- Sources seen: ``

## Decision

- Built-in touch remains not proven: prior MT-capable touch nodes produced zero events and no new touch-driver hypothesis exists.
- Physical-button fallback is now also only partially proven: `event3` and `event0` are button-capable, but V3002 captured zero events/states over the bounded mux window.
- Repeating the identical physical-button mux live run without confirmed operator button input would be low-information churn.
- USB keyboard/OTG remains the next higher-information fallback path because it can introduce a new keyboard-class evdev source instead of resampling the same silent built-in sources.

## Next Action

- Do not repeat the same event3,event0 mux live run unless an operator is explicitly available to press VOLUMEUP/VOLUMEDOWN/POWER during the bounded window. The higher-information path is USB keyboard/OTG attach followed by the staged keyboard live handoff.

## Evidence Inputs

- V2993 report: `docs/reports/NATIVE_INIT_V2993_DOOM_INPUT_FRONTIER_DECISION_2026-06-20.md`
- V2992 report: `docs/reports/NATIVE_INIT_V2992_DOOMINPUT_KEYBOARD_STATE_LIVE_HANDOFF_DRY_RUN_2026-06-20.md`
- V3002 result: `workspace/private/runs/input/v3002-doominput-mux-live-20260620-193808/result.json`
- V3002 report: `docs/reports/NATIVE_INIT_V3002_DOOMINPUT_MUX_LIVE_2026-06-20.md`

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v3003.py tests/test_native_doom_input_frontier_decision_v3003.py`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_input_frontier_decision_v3003`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v3003.py`: PASS (host-only report materialized)
- `git diff --check`: PASS

## Safety

- Host-only metadata consolidation; no flash, no serial command, no evdev open, no input injection, no sysfs writes.
- No Wi-Fi/audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- Private raw command outputs remain under `workspace/private/runs/`; this report includes metadata only.
