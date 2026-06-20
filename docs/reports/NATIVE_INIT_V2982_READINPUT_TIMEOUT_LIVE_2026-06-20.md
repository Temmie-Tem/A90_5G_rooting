# Native Init V2982 Readinput Timeout Live Handoff

## Summary

- Decision: `v2982-readinput-dry-run`
- Result before rollback: `0`
- Track: Video playback / DOOM input prerequisite.
- Candidate reused: `A90 Linux init 0.10.61 (v2981-readinput-timeout)`
- Candidate SHA256: `c5ca7f973823f1f4ca5fc63a9c4d6c19582f4af632531f2954459e2f8a827d98`
- Event under test: `event6` count=`16` timeout_ms=`60000`
- Private run dir: `workspace/private/runs/input/v2982-readinput-timeout-live-20260620-153114`

## Evidence

- Candidate version ok: `0`
- Candidate selftest fail=0: `0`
- Hide before inputscan ok: `0`
- Full `inputscan` rc: `None` selected_found=`0` touch_class=`0`
- Hide before readinput ok: `0`
- `readinput` rc: `None` timeout_ms=`None`
- Read events: `0` abs=`0` key=`0` syn=`0`
- Touch signal: `0` touch_abs=`0` btn_touch=`0`
- Candidate post-sample selftest fail=0: `0`

## Captured Event Sample

- none captured

## Inputscan Recheck

- Summary found: `0` events=`0` touch_candidates=`0`

## Rollback Evidence

- Rollback attempted: `0`
- Rollback step ok: `0`
- Rollback health: version_ok=`0` selftest_fail0=`0`

## Interpretation

- This unit is the first live validation of native-bounded readinput timeout around an actual evdev sample for the DOOM prerequisite.
- A pass proves the selected touch event emits EV_ABS/BTN_TOUCH-class data through native init without input injection or configuration writes.
- If the sample window times out, native `readinput` returns `-ETIMEDOUT`; no host-side `q` cancellation is required.

## Safety

- Only the boot partition is flashed, through `native_init_flash.py`; rollback target is `v2321`.
- The live path only opens and reads the selected `/dev/input/event*` node through `readinput`; no input injection, keymap writes, Wi-Fi, audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- Raw command output stays private under `workspace/private/runs/`; this report includes only event metadata.
