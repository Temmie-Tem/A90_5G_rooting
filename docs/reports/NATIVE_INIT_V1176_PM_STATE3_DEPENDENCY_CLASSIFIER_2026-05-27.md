# Native Init V1176 PM State3 Dependency Classifier Report

Date: `2026-05-27`

## Result

- Decision: `v1176-dependency-flag-state-order-gap-classified`
- Pass: `true`
- Classifier: `scripts/revalidation/native_wifi_pm_state3_dependency_classifier_v1176.py`
- Evidence: `tmp/wifi/v1176-pm-state3-dependency-classifier/manifest.json`
- Summary: `tmp/wifi/v1176-pm-state3-dependency-classifier/summary.md`
- Disassembly: `tmp/wifi/v1176-pm-state3-dependency-classifier/host/pm-service-state-machine-disassembly.txt`

## Summary

V1176 classifies the gap after V1175.  The PM-service state-2 ack path opens fd
`8`, but fd `8` is `/dev/subsys_modem`, not `/dev/subsys_esoc0`.  The same
state-2 path also sees dependency flag `0`, so the dependency branch that would
call the dependency state machine is skipped.

The following state-3 invocation is a no-op in the disassembled PM state
machine: current state `3` falls through to unlock/return without a new open,
state set, dependency call, or eSoC trigger.

| key | value |
| --- | --- |
| V1175 decision | `v1175-state2-opened-subsys-modem-not-esoc0` |
| native state order | `[2, 3, 0, 1]` |
| state-2 dependency flag | `[0]` |
| fd `8` target | `/tmp/a90-v231-1047/root/dev/subsys_modem` |
| state-3 behavior | no-op return |
| state-0 delay after state-2 | `15.989501s` |
| state-0 late action | sets state `1` |
| Android-good eSoC get | `9.491382s` |
| Android-good `wlan0` | `15.784281s` |

## Interpretation

The blocker is now PM dependency flag/state-order parity, not fd-target
ambiguity or generic `pm-proxy` liveness:

```text
Native:
  state=2 ack
    -> dependency_flag=0
    -> skip dependency state=2 call
    -> open /dev/subsys_modem
    -> set state=3
  state=3 ack
    -> no-op return
  state=0 arrives ~16s later
    -> late reset/state=1 path

Android-good:
  pm-service reaches __subsystem_get(esoc0)
    -> ICNSS QMI
      -> BDF
        -> FW ready
          -> wlan0
```

The likely missing condition is that Android arms the dependency flag before the
state-2 ack path, while native reaches state `2` first and only later sees the
state-0/state-1 reset sequence.

## Disassembly Checks

| check | result |
| --- | --- |
| state-2 dependency pointer load | pass |
| state-2 dependency flag load | pass |
| zero dependency flag skips dependency branch | pass |
| dependency state-2 call path exists | pass |
| state-3 falls through to return | pass |
| state-0 dependency-flag setter exists | pass |
| state-0 state-1 transition exists | pass |

## Next Gate

V1177 should trace the PM-service state-0 dependency-flag setter and compare
Android/native PM state order:

- trace the state-0 branch around the dependency call/wait/flag-set path
- confirm whether Android arms dependency flag before the first state-2 ack
- repair ordering only after that parity is proven
- keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, boot
  image write, partition write, and flash blocked until eSoC/WLFW appears

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_pm_state3_dependency_classifier_v1176.py`
- `python3 scripts/revalidation/native_wifi_pm_state3_dependency_classifier_v1176.py`
- Host-only execution; no device command or mutation.
- No PM actor, `mdm_helper`, Wi-Fi HAL, scan/connect, credential use,
  DHCP/route, external ping, partition write, boot image write, or flash.
