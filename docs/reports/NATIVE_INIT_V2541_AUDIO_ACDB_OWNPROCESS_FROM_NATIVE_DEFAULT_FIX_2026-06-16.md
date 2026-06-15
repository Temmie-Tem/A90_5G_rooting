# NATIVE_INIT V2541 — ACDB own-process Android handoff from-native default fix

Date: 2026-06-16
Scope: host-only runner fix for the V2490/V2540 own-process ACDB Android handoff.
Boundary: no device flash in this unit; no ACDB execution; no raw payload handling.

## Problem

V2540's live attempt did not exercise the armed ACDB topology path. It failed before Android helper staging:

- Private run: `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-073017`
- Failure: `flash-android failed rc=1`
- Evidence: `flash-android.stderr.txt` ended with `ADB state timeout; wanted=['recovery'] last=<none>` after `wait_recovery_adb` timed out at 180.844s.
- Recovery: the runner found the native bridge still alive, used `--from-native` rollback fallback, reflashed V2321, and final selftest was `fail=0`.

The key clue is that the device never entered recovery for the Android flash. The V2490 runner generated `flash_android` without `--from-native` by default, while the device was resident in native init. In that state `native_init_flash.py` waits for recovery ADB but does not ask native init to reboot there.

## Root cause

`workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py` had:

```python
parser.add_argument("--from-native", action="store_true")
```

That made `from_native=False` unless explicitly passed, unlike the later Android handoff runners that default to `from_native=True` for native-resident starts.

## Fix

Changed the runner CLI to:

```python
parser.add_argument("--from-native", action=argparse.BooleanOptionalAction, default=True)
```

This keeps an explicit `--no-from-native` escape hatch for non-native starts, but makes the safe/common native-resident path the default.

The V2490 unit test default was updated to `from_native=True`, and dry-run now asserts that `payload["commands"]["flash_android"]` contains `--from-native`.

## Validation

Commands run:

```bash
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py
PYTHONPATH=tests python3 -m unittest tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py
```

Result:

- `py_compile`: pass
- unittest: `Ran 34 tests ... OK`

V2540 artifact dry-run with the patched runner:

- `ok=True`
- `live_ready=True`
- `live_blockers=[]`
- `flash_android` includes `--from-native`
- Flash command tail: `--post-flash-target android-adb --android-root-check --android-timeout 240.0 --adb adb --from-native`

Current device health check after the previous V2540 rollback:

- Resident version: V2321 / `0.9.285`
- `selftest fail=0`

## Classification

`v2541-ownprocess-android-handoff-from-native-fixed`

This fixes the pre-helper transport bug that prevented V2540 from exercising the armed ACDB path. The next meaningful live unit is to rerun the same V2540 helper/preload artifacts using the patched V2490 runner.
