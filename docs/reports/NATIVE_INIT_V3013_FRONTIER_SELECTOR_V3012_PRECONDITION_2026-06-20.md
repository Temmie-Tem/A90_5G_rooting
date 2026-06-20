# Native Init V3013 Frontier Selector V3012 Precondition

## Summary

- Decision: `v3013-frontier-selector-v3012-precondition-pass`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM input prerequisite plus T3 selector anti-churn hardening.
- Selector decision: `frontier-selector-no-automatic-safe-unit`
- First evaluated track: `VIDEO` / `doom-input`
- First track status: `external-hardware-stimulus-required`
- V3012 live-precondition report present: `1`
- V3012 resident health ok: `1`
- V3012 live-gate assets ready: `1`
- V3012 A90 OTG keyboard evidence: `0`
- V3012 host-only gate audit stop: `1`

## Change

- `native_init_frontier_select.py` now reads the V3012 DOOM input live-precondition report when present.
- The selector carries V3012 evidence into the first-class `VIDEO` / `doom-input` evaluation.
- When V3012 says resident health and V3004 live-gate assets are clean but A90-side USB keyboard/OTG evidence is absent, the selector tells the loop to stop DOOM input host-only gate audits until hardware plus operator key presses are available.

## Rationale

- V3009 through V3012 were useful host-only gate/selector refinements, but the GOAL anti-churn guard says a streak of host-only metadata/audit work without new tested device behavior must force re-evaluation.
- V3012 proved the current bridge/resident health and asset readiness are not the blocker.
- The remaining blocker is external hardware stimulus, so the selector should not keep offering more host-only DOOM gate audits as forward progress.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_init_frontier_select.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_init_frontier_select`: PASS (16 tests)
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json`: PASS
- `git diff --check`: PASS

## Safety

- Host-only selector/test/report change.
- No flash, no serial command, no evdev open, no input injection, and no sysfs write.
- No Wi-Fi/audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- V3012 raw command output remains private under `workspace/private/runs/`; this report includes metadata only.
