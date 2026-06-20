# Native Init V2999 DOOM Input Mux Live Handoff Dry Run

## Summary

- Decision: `v2999-doominput-mux-dry-run`
- Result before rollback: `0`
- Track: active Video playback / DOOM input prerequisite.
- Candidate: `A90 Linux init 0.10.67 (v2998-doominput-mux)`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2998_doominput_mux.img`
- Candidate SHA256: `4828fdfba65c80a5d0a2883c2a8964a82074a6863e03e95f0f8f9aa1e9e138d6`
- Events: `event3,event0`
- Private run dir: `workspace/private/runs/input/v2999-doominput-mux-live-20260620-191501`
- Live execution: `0`

## Preflight

- Preflight ok: `1`
- Candidate SHA256 ok: `1`
- Rollback v2321 SHA256 ok: `1`
- Fallback v2237 SHA256 ok: `1`
- Fallback v48 exists: `1`
- Flash helper exists: `1`
- Operator prerequisite: `operator presses VOLUMEUP/VOLUMEDOWN/POWER during the single bounded doominputmux window`

## Evidence

- Candidate version ok: `not-run`
- Candidate selftest fail=0: `not-run`
- Inputscan rc: `not-run` button_candidates=`not-run`
- `doominputmux` rc: `not-run` timeout_ms=`not-run`
- Mux events: `not-run` states=`not-run` active_states=`not-run` proxy_states=`not-run` max_frame=`not-run` sources=`-` proxy_fields=`-`
- Candidate post-sample selftest fail=0: `not-run`

## Button Candidates

- none captured in this run

## Requested Event Checks

- none captured in this run

## Rollback Evidence

- Rollback attempted: `0`
- Rollback step ok: `0`
- Rollback health: version_ok=`0` selftest_fail0=`0`

## Interpretation

- V2999 stages live validation for the V2998 diagnostic multi-event DOOM input mux candidate.
- Pass requires selected `buttons` events, POWER/VOLUME capability bits, and `doominputmux.state` evidence for `forward`, `back`, or `fire` while candidate health remains clean.
- Dry-run mode does not flash; live mode should run only when an operator can press A90 physical buttons during the bounded mux sample window.
- This is diagnostic evdev-to-`doominput.state` liveness proof, not a final DOOM control scheme.

## Safety

- Live mode flashes only the boot partition through `native_init_flash.py`; rollback target remains `v2321`.
- The validation path only reads `/sys/class/input` capability files and `/dev/input/event*` events.
- No input injection, `EVIOCGRAB`, keymap change, sysfs write, Wi-Fi, audio route/playback, video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doominput_mux_live_handoff_v2999.py tests/test_native_doominput_mux_live_handoff_v2999.py`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doominput_mux_live_handoff_v2999`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doominput_mux_live_handoff_v2999.py --count 24 --timeout-ms 45000`: PASS (dry-run preflight/report)
- `git diff --check`: PASS
