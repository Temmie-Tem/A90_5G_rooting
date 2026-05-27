# Native Init V1168 PM-Service Callback Dispatch Live Report

Date: `2026-05-27`

## Result

- Decision: `v1168-callback-branch-dispatched-but-no-esoc0`
- Pass: `true`
- Plan: `docs/plans/NATIVE_INIT_V1168_PM_CALLBACK_DISPATCH_LIVE_PLAN_2026-05-27.md`
- V401 evidence: `tmp/wifi/v1168-v401-selinuxfs-mount/manifest.json`
- V490 evidence: `tmp/wifi/v1168-v490-policy-load/manifest.json`
- Live evidence: `tmp/wifi/v1168-pm-callback-dispatch-live-after-v490/manifest.json`
- Live summary: `tmp/wifi/v1168-pm-callback-dispatch-live-after-v490/summary.md`

## Summary

V1168 proves the state helper does iterate client records and branch into a
resolved callback target.  The first `state=2` path reaches:

```text
0x92dc state helper
  -> client node 0xb400007f13e06120
    -> client record 0xb400007f13e060e0
      -> callback wrapper 0x8630
        -> target object 0xb400007f13e15080
          -> callback pointer 0x7f9a0eca5c
            -> no /dev/subsys_esoc0
```

So the blocker is no longer state helper dispatch.  The callback branch itself
is reached, but its side effect does not open `/dev/subsys_esoc0`.

## Key Evidence

| key | value |
| --- | --- |
| decision | `v1168-callback-branch-dispatched-but-no-esoc0` |
| callback event count | `30` |
| state values observed | `2`, `3`, `0`, `1` |
| state `2` callback branch | observed |
| client records | `0xb400007f13e060e0`, `0xb400007f13e06180` |
| callback pointer | `0x7f9a0eca5c` |
| callback target objects | `0xb400007f13e15080`, `0xb400007f13e150c0` |
| callback vtable | `0x7f9a0efab0` |
| `/dev/subsys_esoc0` | not opened |
| MHI/WLFW/BDF/`wlan0` | all absent |
| Wi-Fi HAL/scan/connect/credentials | not executed |
| DHCP/route/external ping | not executed |

## Maps Gap

The V1168 collector attempted to capture `/proc/<pm-service-pid>/maps` after
the child gate exited.  At that late point `pm-service` was no longer visible,
so `pm_callback_dispatch.maps_count` is `0`.  The callback pointer itself was
captured, but the pointer-to-binary mapping remains unresolved.

## Next Gate

V1169 should move maps capture into the live sample loop while `pm-service` is
still alive.  The gate should preserve the same callback probes and add:

- `pm_service_maps_sample_begin index=N`
- `/proc/<pm-service-pid>/maps` content for samples where `pm-service` exists
- target mapping for callback `0x7f9a0eca5c`

If the target maps to `libperipheral_client.so`, the next step is tracing the
client-side callback implementation.  If it maps to `pm-service`, trace the
local callback body directly.

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_pm_callback_dispatch_live_v1168.py`
- `python3 scripts/revalidation/native_wifi_pm_callback_dispatch_live_v1168.py plan`
- V401 selinuxfs mount proof passed.
- V490 SELinux policy load proof passed.
- V1168 live gate passed.
- Post-cleanup native health:
  - `version`: `A90 Linux init 0.9.68 (v724)`
  - `selftest`: `pass=11 warn=1 fail=0`
  - `netservice`: disabled, `ncm0=absent`, `tcpctl=stopped`
