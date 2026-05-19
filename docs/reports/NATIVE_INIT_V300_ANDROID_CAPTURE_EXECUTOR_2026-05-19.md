# Native Init v300 Android Capture Executor Report

- date: `2026-05-19`
- scope: guarded executor for Android property capture handoff
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V300_ANDROID_CAPTURE_EXECUTOR_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/android_capture_handoff_execute.py`

## Summary

v300 adds a fail-closed executor for the v299 Android capture handoff. It
records the exact live sequence but refuses to execute reboot/recovery/flash
unless all approval flags are present.

No live handoff was executed in this validation.

## Evidence

| item | path | result |
| --- | --- | --- |
| plan | `tmp/wifi/v300-android-capture-executor-plan/` | `android-capture-executor-plan-ready` |
| dry-run | `tmp/wifi/v300-android-capture-executor-dryrun/` | `android-capture-executor-dryrun-ready` |
| approval refusal | `tmp/wifi/v300-android-capture-executor-refuse/` | `android-capture-executor-approval-required` |

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

Result: PASS, all live steps recorded as skipped.

Approval refusal:

```bash
python3 scripts/revalidation/android_capture_handoff_execute.py \
  --out-dir tmp/wifi/v300-android-capture-executor-refuse \
  run
```

Result: expected failure, decision `android-capture-executor-approval-required`.

Post-check:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
```

Result:

- `A90 Linux init 0.9.60 (v261)` still running.
- runtime SD backend still active.
- netservice disabled, tcpctl stopped.

## Approval Contract

`run` requires:

- `--allow-android-boot-flash`
- `--assume-yes`
- `--i-understand-native-rollback`

Without all three, it exits before recovery, reboot, or boot partition write.

## Safety

- No reboot.
- No recovery transition.
- No boot partition write.
- No Android boot image flashing.
- No property mutation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## Interpretation

The host side is now prepared for an operator-approved Android property capture
maintenance window:

1. v300 executor performs Android boot handoff.
2. v297 captures Android property baseline.
3. v298 compares static/native and Android baselines.
4. v300 restores native v261.

Execution remains blocked until explicit operator approval is given.
