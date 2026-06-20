# Native Init V3011 Frontier Selector V3010 Assets

## Summary

- Decision: `v3011-frontier-selector-v3010-assets-pass`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM input prerequisite plus T3 selector hardening.
- Selector decision: `frontier-selector-no-automatic-safe-unit`
- First evaluated track: `VIDEO` / `doom-input`
- First track status: `external-hardware-stimulus-required`
- V3010 flash-gate report present: `1`
- V3010 flash-gate assets ready: `1`
- V3010 current gate reports ok: `1`
- V3010 external hardware wait retained: `1`

## Change

- `native_init_frontier_select.py` now reads the V3010 DOOM input flash-gate asset report when present.
- The selector keeps the current `VIDEO` / `doom-input` evaluation non-actionable, but now records that the V3004 live-gate assets are present and checksum-clean.
- The next-operator decision now distinguishes "assets are ready" from the missing external prerequisite: A90-side USB keyboard/OTG plus operator DOOM key presses.

## Rationale

- V3008/V3009 correctly stopped automatic touch/button live repeats while the active DOOM input tier needs external hardware stimulus.
- V3010 then proved the V3004 candidate image, rollback/fallback assets, TWRP recovery, flash helper, and current gate reports are ready.
- Without this selector update, the main frontier output still looked like it only knew V3008, which could obscure that the remaining gap is hardware stimulus, not flash-gate prep.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_init_frontier_select.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_init_frontier_select`: PASS (13 tests)
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py`: PASS
- `git diff --check`: PASS

## Safety

- Host-only selector/test/report change.
- No flash, no serial command, no evdev open, no input injection, no sysfs write.
- No Wi-Fi/audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
