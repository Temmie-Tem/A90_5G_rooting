# Native Init V2781 Audio Stage Module Runner Hardening

## Summary

- Cycle: `V2781`
- Track: audio stage module device-validation harness hardening.
- Decision: `v2781-audio-stage-module-runner-hardened-host-only`
- Scope: host-only runner/test changes after the V2780 live abort.
- Target candidate remains: `workspace/private/inputs/boot_images/boot_linux_v2779_audio_stage_module.img`
- Rollback target remains: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`

## Why

- V2780 proved the candidate booted and the protocol envelope for `candidate-selftest` was `rc=0 status=ok`.
- V2780 still aborted because its runner only scanned the human stdout text for `fail=0`; the text stream was desynchronized and omitted that token.
- V2780 rollback also timed out during native-to-recovery handoff even though the device reached recovery and a checked manual V2321 flash succeeded.
- Re-running unchanged would be a retry-loop. The next safe unit is hardening the runner before another live attempt.

## Changes

- Added `protocol_selftest_ok()` and `selftest_step_ok()` so selftest can pass on a valid structured protocol envelope when stdout text is desynchronized.
- Preserved text `fail=0` checks and records whether protocol fallback was used.
- Added `adb_recovery_present()` and `rollback_v2321()` fallback logic.
- If `native_init_flash.py --from-native` fails but ADB reports recovery mode, the runner attempts a second checked V2321 flash without `--from-native`.
- Records rollback attempts and whether recovery fallback was used.

## Safety

- Host-only change; no device action in this iteration.
- The future live path still uses only `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- The future validation remains read-only for audio: no route apply, ACDB SET, mixer write, PCM open, PCM write, or playback execute.
- No private run logs, boot images, firmware, raw binaries, credentials, or device identifiers are committed.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_stage_module_device_validation_handoff_v2781.py tests/test_native_audio_stage_module_device_validation_v2781.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_stage_module_device_validation_v2781`
- `git diff --check`

## Next

- Run one device validation unit with the hardened V2781 runner.
- If the V2779 read-only audio command smoke passes and rollback returns to V2321 with `selftest fail=0`, proceed to the next API/productization unit.
- API/productization should then split call-oriented audio operations behind stable functions rather than adding more host-side orchestration.
