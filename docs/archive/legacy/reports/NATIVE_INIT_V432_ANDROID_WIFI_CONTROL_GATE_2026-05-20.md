# Native Init V432 Android Wi-Fi Control Gate Report

Date: 2026-05-20

## Summary

V432 added a read-only Android-managed Wi-Fi control gate and a boot-complete
handoff wrapper.  The corrected live handoff passed with:

```text
decision: v432-android-wifi-already-connected-auto-gate-pass
pass: True
reason: Android auto-connected Wi-Fi from saved framework state; next gate must contain and characterize this before any explicit scan/connect
wifi_bringup_executed: False
```

The run temporarily booted Android, collected read-only Wi-Fi control evidence,
then restored native init `A90 Linux init 0.9.61 (v319)`.  V432 itself did not
issue Wi-Fi enable, scan, connect, credentials, DHCP, routing, rfkill/sysfs
writes, module operations, `setprop`, or direct daemon starts.

## Implementation

- `scripts/revalidation/wifi_android_control_gate_v432.py`
  - read-only Android collector for `cmd wifi status`, safe command help,
    settings, framework services, Wi-Fi processes, `wlan0`, rfkill, and filtered
    `dumpsys wifi`;
  - blocks mutating Wi-Fi commands from the capture list before execution;
  - classifies already-connected auto state separately from enable-ready state;
  - redacts MAC, IP, SSID/BSSID, serial, and credential-like fields.
- `scripts/revalidation/android_wifi_control_gate_handoff_v432.py`
  - reuses the Android boot-complete handoff and native rollback path;
  - runs the V432 collector after Android boot-complete settle;
  - maps collector decisions into handoff decisions while preserving
    `wifi_bringup_executed=False`.

## Static Validation

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_control_gate_v432.py \
  scripts/revalidation/android_wifi_control_gate_handoff_v432.py

git diff --check
```

Both checks passed.

Plan and dry-run evidence:

```text
tmp/wifi/v432-android-control-gate-plan-20260520-153521/
tmp/wifi/v432-android-control-gate-handoff-plan-20260520-153521/
tmp/wifi/v432-android-control-gate-handoff-dryrun-20260520-153521/
tmp/wifi/v432-android-control-gate-handoff-dryrun-classifierfix-20260520-153959/
```

## Live Evidence

Corrected live handoff:

```text
tmp/wifi/v432-android-control-gate-handoff-live-classifierfix-20260520-154009/
decision: v432-android-wifi-already-connected-auto-gate-pass
pass: True
device_commands_executed: True
device_mutations: True
wifi_bringup_executed: False
```

Collector evidence:

```text
tmp/wifi/v432-android-control-gate-handoff-live-classifierfix-20260520-154009/v432-android-wifi-control-gate-run/
decision: v432-android-wifi-already-connected-auto-gate-pass
pass: True
```

Superseded live attempt:

```text
tmp/wifi/v432-android-control-gate-handoff-live-20260520-153539/
  PASS-equivalent evidence, but the first classifier labeled the auto-connected
  state as review-required.  The classifier was then tightened and rerun.
```

Rollback/postflight after corrected live:

```text
version: A90 Linux init 0.9.61 (v319)
selftest: pass=11 warn=1 fail=0
status: rc=0 status=ok
```

## Runtime Findings

V432 observed Android boot-complete Wi-Fi state as:

| Item | Value |
| --- | --- |
| `enabled_by_status` | `True` |
| `disabled_by_status` | `False` |
| `wifi_connected` | `True` |
| `android_auto_connect_observed` | `True` |
| `wlan0_has_ip` | `True` |
| `wlan0_up_lower` | `False` |
| `airplane_off` | `True` |
| `framework_services_present` | `True` |
| `runtime_processes_present` | `True` |

The important detail is that Android had already connected Wi-Fi from saved
framework state by boot-complete.  Evidence included redacted `cmd wifi status`
connection state, `Supplicant state: COMPLETED`, and filtered `dumpsys wifi`
state transitions such as saved-network connection and IPv4 provisioning.

## Interpretation

V432 changes the next step.  The project should not proceed to an enable-only
gate, because Android does not appear to need one in this boot path.  It should
also not jump directly to scan/connect, because an already-connected saved
network means external exposure may exist before any explicit test command.

The strongest current conclusions are:

- Android-managed Wi-Fi is functional enough to auto-connect at boot-complete;
- V432 did not cause that connection with an enable, scan, connect, or routing
  command;
- the remaining problem is controlled operation: containment, observation,
  cleanup, and policy boundaries before server-style use;
- native/Linux Wi-Fi integration remains incomplete, but it is now lower
  leverage than understanding Android-managed auto-connect behavior.

## Next

Recommended next cycle: V433 Android Wi-Fi auto-connect containment and
stability gate.

V433 should remain read-only or cleanup-only unless explicitly split into a
separate mutating gate.  It should:

- capture bounded connection stability, route/DNS/default-gateway exposure, and
  external-interface reachability without credentials;
- prove whether Android auto-connect can be contained or intentionally disabled
  for lab runs;
- define cleanup/rollback behavior if Android connects unexpectedly;
- keep scan/connect/link-up and credential operations blocked until containment
  is understood.
