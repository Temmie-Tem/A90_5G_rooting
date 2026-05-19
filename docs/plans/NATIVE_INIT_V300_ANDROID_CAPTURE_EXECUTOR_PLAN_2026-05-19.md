# Native Init v300 Android Capture Executor Plan

- date: `2026-05-19`
- scope: guarded executor for Android property capture handoff
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/android_capture_handoff_execute.py`
- prerequisite: v299 decision `android-capture-handoff-ready-needs-operator`

## Summary

v299 generated the handoff runbook and verified that local inputs are ready.
v300 turns that runbook into a fail-closed host executor. The default mode is
plan/dry-run only. The executor must refuse live execution unless all explicit
approval flags are present.

This step still does not boot Android or write the boot partition during normal
validation. It prepares the exact controlled command path for the later
operator-approved maintenance window.

## Live Run Approval Flags

`run` requires all of:

- `--allow-android-boot-flash`
- `--assume-yes`
- `--i-understand-native-rollback`

Without those flags, `run` exits before reboot/recovery/flash.

## Intended Live Sequence

Only after approval:

1. Verify native bridge `version/status`.
2. Request native init to enter recovery/TWRP.
3. Wait for recovery ADB.
4. Push the selected Android boot image to TWRP.
5. Verify remote SHA-256.
6. Flash Android boot image to `/dev/block/by-name/boot`.
7. Read back boot prefix SHA-256.
8. Reboot system to Android.
9. Wait for Android ADB.
10. Run v297 property capture.
11. Run v298 property baseline compare.
12. Reboot Android to recovery.
13. Restore native init v261 with `native_init_flash.py`.

## Guardrails

- Default validation uses `plan` and `dry-run` only.
- No live run without approval flags.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No property mutation.
- No service-manager/HAL/Wi-Fi daemon execution.
- Native rollback image is mandatory.

## Validation

Static:

```bash
python3 -m py_compile scripts/revalidation/android_capture_handoff_execute.py
git diff --check
```

Dry-run:

```bash
python3 scripts/revalidation/android_capture_handoff_execute.py \
  --out-dir tmp/wifi/v300-android-capture-executor-dryrun \
  dry-run
```

Approval refusal:

```bash
python3 scripts/revalidation/android_capture_handoff_execute.py \
  --out-dir tmp/wifi/v300-android-capture-executor-refuse \
  run
```

Expected: refusal before any reboot/recovery/flash.

## Acceptance

- `dry-run` records the full live sequence without mutating the device.
- `run` without approval flags refuses before dangerous operations.
- The live sequence references v297 capture and v298 compare artifacts.
- The executor preserves the v299 operator boundary.
