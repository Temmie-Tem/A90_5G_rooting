# NATIVE_INIT V2364 — checked flash helper Android target mode

Date: 2026-06-15

## Scope

- Unit: host-only implementation for the V2362 Android route-delta helper gap.
- Touched public code:
  - `workspace/public/src/scripts/revalidation/native_init_flash.py`
  - `tests/test_native_init_flash.py`
- No boot image was built.
- No device command or flash ran in this iteration.

## Result

Decision: `v2364-flash-helper-android-target-mode-host-only-pass`.

The checked flash helper now supports an explicit Android post-flash verification target:

```bash
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  <android-boot.img> \
  --expect-sha256 <sha256> \
  --expect-android-magic \
  --post-flash-target android-adb \
  --android-root-check
```

The default path remains unchanged: without `--post-flash-target android-adb`, the helper still
flashes through recovery and verifies native init over the serial bridge.

## Implementation

- Added `--post-flash-target native-init|android-adb`, defaulting to `native-init`.
- Added `--android-timeout` for Android ADB device + boot-complete polling.
- Added `--android-root-check` to require `adb shell su -c id` to report `uid=0`.
- Added `--expect-android-magic` to require the local boot image to start with `ANDROID!`.
- Added `verify_post_flash_target()` so `--verify-only` and post-reboot verification use the same
  target dispatch.
- Android mode waits for ADB state `device`, then polls `sys.boot_completed` and `dev.bootcomplete`
  until either reports `1`.

## Safety boundary

- The helper remains the only allowed flash path.
- The helper still writes only the configured boot block; this iteration did not widen partition
  scope.
- Android mode does not run any audio, mixer, tinyalsa, `AudioTrack`, or route-delta capture by
  itself.
- Future Android route-delta live capture still needs a separate exact operator gate and a bounded
  runner that uses this helper mode, then rolls back to V2321.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_init_flash.py tests/test_native_init_flash.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_native_init_flash -v`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `git diff --check`
