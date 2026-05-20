# Native Init V437 Wi-Fi Branch Decision Report

Date: 2026-05-20

## Summary

V437 added a host-side Wi-Fi branch selector.  The host-run passed with:

```text
decision: v437-wifi-branch-controlled-reenable-selected
pass: True
branch: controlled-android-reenable-observation
reason: Android Wi-Fi is persistently contained, so the next Wi-Fi-progressing gate can safely observe controlled re-enable
wifi_bringup_executed: False
```

V437 did not execute any device command.  It consumed V436 evidence and selected
the next gate that moves toward Wi-Fi functionality without jumping to
scan/connect or server exposure.

## Implementation

- `scripts/revalidation/wifi_android_branch_decision_v437.py`
  - loads the latest or explicit V436 manifest;
  - checks contained-state markers from V436;
  - selects `controlled-android-reenable-observation`;
  - records V438 constraints.

## Static Validation

```text
python3 -m py_compile scripts/revalidation/wifi_android_branch_decision_v437.py

git diff --check
```

Both checks passed.

Plan and host-run evidence:

```text
tmp/wifi/v437-wifi-branch-decision-plan-20260520-164708/
tmp/wifi/v437-wifi-branch-decision-hostrun-20260520-164708/
```

## Input Evidence

V437 used the latest V436 live evidence:

```text
tmp/wifi/v436-android-wifi-disabled-persistence-handoff-live-20260520-164037/manifest.json
decision: v436-android-wifi-disabled-persistence-pass
pass: True
```

Contained-state markers:

| Item | Value |
| --- | --- |
| `enabled_by_status` | `False` |
| `disabled_by_status` | `True` |
| `wlan0_has_ip` | `False` |
| `default_route_wlan` | `False` |
| `route_get_wlan` | `False` |
| `connectivity_validated_wifi` | `False` |
| `dns_surface_wlan` | `False` |
| `global_listener_observed` | `False` |
| `disabled` | `True` |
| `route_absent` | `True` |
| `connectivity_absent` | `True` |
| `listener_safe` | `True` |

## Decision

Selected branch:

```text
controlled-android-reenable-observation
```

Blocked actions remain:

- scan/connect;
- credential operations;
- server exposure;
- external packet probes;
- DHCP or routing mutation;
- new Wi-Fi-facing listeners.

V438 constraints:

- only `cmd wifi set-wifi-enabled enabled` may be allowed as the bounded
  mutation;
- capture pre/post status, route/DNS/connectivity/listener state;
- do not issue scan/connect or credentials;
- do not send ping/curl/nc/dig/nslookup traffic;
- restore native v319 and verify rollback.

## Interpretation

V437 keeps the project moving toward Wi-Fi while preserving the safety boundary.
The device now has a proven contained Android baseline.  The next useful test is
not server exposure and not scan/connect; it is a bounded observation of what
Android does after framework Wi-Fi is re-enabled.

## Next

Recommended next cycle: V438 controlled Android Wi-Fi re-enable observation.

V438 is allowed to re-enable Wi-Fi only as a bounded mutation and must treat any
auto-connect or route/DNS exposure as observation evidence, not as permission to
serve traffic or connect to networks explicitly.
