# Native Init v304 Android Capture Live Guard Report

- date: `2026-05-19`
- scope: host-only go/no-go guard before Android capture live handoff
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V304_ANDROID_CAPTURE_LIVE_GUARD_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/android_capture_live_guard.py`

## Summary

v304 adds a final host-side live guard for the approval-gated Android capture
maintenance window. It re-checks the v302 approval packet, target propagation,
Android and native rollback image hashes, v303 postprocess state, and current
native bridge health. If all blocker checks pass, it writes `live-command.txt`
for the exact v300 live command.

The guard does not execute the live command.

## Evidence

| item | path | result |
| --- | --- | --- |
| live guard | `tmp/wifi/v304-android-capture-live-guard/` | `android-capture-live-guard-go` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/android_capture_live_guard.py
python3 scripts/revalidation/android_capture_live_guard.py \
  --out-dir tmp/wifi/v304-android-capture-live-guard \
  run
git diff --check
```

Result: PASS.

## Checks

| check | result |
| --- | --- |
| v302 approval packet | PASS |
| v300 target propagation | PASS |
| live command approval flags | PASS |
| Android boot image hash/size | PASS |
| native rollback image hash/size | PASS |
| v303 postprocess waiting state | PASS |
| native bridge `version` | PASS |
| native bridge `status` | PASS |
| repo cleanliness | WARN during implementation; commit before live handoff |

## Live Command

The guard copies the v302 command into `live-command.txt` only when blocker
checks pass:

```bash
python3 scripts/revalidation/android_capture_handoff_execute.py --out-dir tmp/wifi/v300-android-capture-executor-live run --allow-android-boot-flash --assume-yes --i-understand-native-rollback
```

## Safety

- No reboot.
- No recovery transition.
- No boot partition write.
- No Android boot image flashing.
- No ADB command execution.
- No property mutation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## Interpretation

The live handoff is currently GO from a host-side readiness perspective, but it
still requires explicit operator approval because the command writes the boot
partition and performs Android/native boot transitions.
