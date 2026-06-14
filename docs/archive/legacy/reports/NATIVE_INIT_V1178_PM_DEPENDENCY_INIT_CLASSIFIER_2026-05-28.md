# Native Init V1178 PM Dependency Init Classifier Report

Date: `2026-05-28`

## Result

- Decision: `v1178-pm-dep-init-order-gap-classified`
- Pass: `true`
- Classifier: `scripts/revalidation/native_wifi_pm_dependency_init_classifier_v1178.py`
- Evidence: `tmp/wifi/v1178-pm-dependency-init-classifier/manifest.json`
- Summary: `tmp/wifi/v1178-pm-dependency-init-classifier/summary.md`

## Summary

V1178 classifies the two-dependency structure found by V1177 and identifies the
root-cause ordering gap.  The PM-service state machine maintains two distinct
dependency slots for the wlan peripheral:

| dep slot | address | offset from peripheral | role |
| --- | --- | --- | --- |
| state-2 dep | `0xb400007fa4226000` | `peripheral-0x180` | eSoC/mdm3 proxy; flag at `+0x140` arms esoc0 |
| state-0 dep | `0xb400007fa42261c0` | `peripheral+0x40` | per_proxy_helper session; state=1 when complete |

The two failure conditions observed in V1177 are causally linked:

1. **state-2** sees `dependency_flag=0` → skips `__subsystem_get(esoc0)`, opens
   `/dev/subsys_modem` instead.
2. **state-0** sees `dependency_state=1` → skips the dependency state-0 call and
   the `dependency_flag` set path → `dependency_flag` is never armed.

The ordering gap is:

```text
Android:
  per_proxy_helper starts t=6.67s → registers wlan peripheral
  per_proxy starts        t=8.82s → delta from pph = 2.16s
  parent peripheral state-2 arrives while dep (pph session) still in-flight
  parent peripheral state-0 arrives → dep state ≠ 1 → flag-set path runs
  dependency_flag set to 1
  next state-2 → flag=1 → calls dependency state-2 → __subsystem_get(esoc0)
  pm-service esoc0 get    t=9.49s
  wlan0                   t=15.78s

Native:
  per_proxy_helper starts early (Android actor path)
  per_proxy_helper PM state machine completes → dep (pph session) reaches state=1
  per_proxy starts LATE (after mdm_helper holds /dev/esoc-0) → t≈993s
  parent peripheral state-2 arrives t=993.94s → dep already state=1 → flag stays 0
  parent peripheral state-0 arrives t=1009.93s → dep state=1 → skip flag-set
  dependency_flag never armed → esoc0 branch never taken
```

## Key Evidence

| key | value |
| --- | --- |
| V1177 decision | `v1177-dependency-flag-not-armed` |
| peripheral | `0xb400007fa4226180` |
| state-2 dep addr | `0xb400007fa4226000` |
| state-2 dep offset | `peripheral-0x180` |
| state-2 dep flag | `0x0` |
| state-0 dep addr | `0xb400007fa42261c0` |
| state-0 dep offset | `peripheral+0x40` |
| state-0 dep state (first read) | `0x1` |
| state-0 dep state (second read) | `0x1` |
| native state sequence | `[2, 3, 0, 1]` |
| state-2 → state-0 gap | `15.990s` |
| Android per_proxy_helper start | `6.666s` |
| Android per_proxy start | `8.824s` |
| Android per_proxy − per_proxy_helper | `2.159s` |
| Android pm_service esoc0 get | `9.491s` |
| Android wlan0 | `15.784s` |

## Disassembly Checks

All nine checks pass against the extracted `pm-service` binary:

| check | result |
| --- | --- |
| state2_dep_ptr_load_0x148 | pass |
| state2_dep_flag_load_0x140 | pass |
| state2_dep_flag_cbz_skip | pass |
| state2_dep_state_check_ne3 | pass |
| state2_dep_state_check_ne2 | pass |
| state2_dep_flag_set_store | pass |
| state2_flag_set_offset_0x140 | pass |
| state0_branch_cbz | pass |
| state1_branch_beq | pass |

## Dependency Identity Hypotheses

### State-0 dep (peripheral+0x40)

The dependency at `peripheral+0x40` is the first entry in the wlan peripheral's
client list, or per_proxy_helper's own PM session sub-object.  It reaches
`state=1` when per_proxy_helper's own PM state machine completes.  In native,
per_proxy_helper starts early (Android actor path), so this object is `state=1`
well before `t=993s`.  In Android, the parent peripheral's `state-0` is
processed before the dep reaches `state=1`, so the flag-set path runs and arms
`dep_flag=1` for the next `state-2`.

### State-2 dep (peripheral-0x180)

The state-2 dependency at `peripheral-0x180` is a co-located peripheral or
dependency-tracker object for the eSoC/mdm3 subsystem.  Its flag field at
`peripheral+0x140` is set to `1` by the `state-0` flag-set path when it runs.
With `flag=0`, the `state-2` branch skips `__subsystem_get(esoc0)` and opens
`/dev/subsys_modem` instead.

## Root Cause

Native starts `per_proxy` late (after `mdm_helper` holds `/dev/esoc-0`).  By
that point per_proxy_helper has already completed its own PM state machine, so
the dependency at `peripheral+0x40` is already `state=1`.  When the parent
peripheral's `state-0` arrives it sees `dep_state=1`, skips the dependency
state-0 call and the flag-set path, and never arms `dep_flag=1`.  On the
subsequent `state-2` the flag is still `0`, so `__subsystem_get(esoc0)` is
never called.

## Repair Strategy

Start `per_proxy` (pm-proxy) **before** per_proxy_helper's PM state machine
completes — i.e., within ~2s of per_proxy_helper start, not after mdm_helper
acquires `/dev/esoc-0`.

This matches the Android timing:
- `per_proxy_helper_start` = 6.666s
- `per_proxy_start` = 8.824s
- Δ = **2.159s**

The simplest approach: arm per_proxy alongside (or within a few seconds of)
per_proxy_helper, independently of the mdm_helper esoc-0 gate.  The mdm_helper
gate was added to prevent a blind subsys_esoc0 open before mdm_helper is ready,
but per_proxy itself does not open subsys_esoc0 — that is pm-service's job after
the dep_flag is armed.

Do **not** simply remove the mdm_helper gate without first proving (via V1179
uprobes) that the dep transitions correctly when per_proxy connects earlier.

## Next Gate

V1179 should arm uprobes **before** per_proxy_helper/per_proxy/pm-service
startup to capture ALL peripheral state transitions from `t=0`:

1. When does the dep at `peripheral+0x40` transition from `state=0` to `state=1`?
2. Is this transition triggered by per_proxy_helper's own ack sequence, or by
   per_proxy connecting?
3. Prove that starting per_proxy within ~2s of per_proxy_helper keeps the dep in
   `state=0` when the parent peripheral's `state-0` is processed.

Keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, boot
image write, partition write, and flash blocked until `/dev/subsys_esoc0` or
WLFW appears.

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_pm_dependency_init_classifier_v1178.py`
- `python3 scripts/revalidation/native_wifi_pm_dependency_init_classifier_v1178.py`
- Host-only execution; no device command or mutation.
- No PM actor, `mdm_helper`, Wi-Fi HAL, scan/connect, credential use,
  DHCP/route, external ping, partition write, boot image write, or flash.
