# Native Init V437 Wi-Fi Branch Decision Plan

Date: 2026-05-20

## Goal

V437 consumes V436 disabled-persistence evidence and chooses the next Wi-Fi
branch.  It is host-side only and does not touch the device.

V436 proved a contained Android baseline.  Since the project objective is to
continue toward Wi-Fi functionality, V437 should select a controlled Android
Wi-Fi re-enable observation gate as the next step, while keeping scan/connect,
credentials, server exposure, and external probes blocked.

## Scope

Allowed:

- load latest or explicit V436 disabled-persistence manifest;
- verify contained-state markers;
- select and document the next branch and constraints.

Not allowed:

- device commands or device mutations;
- Wi-Fi enable/disable, scan/connect, credentials, DHCP/routing mutation,
  external packet probes, server exposure, or new listeners.

## Implementation

- Selector: `scripts/revalidation/wifi_android_branch_decision_v437.py`
  - finds the latest V436 live manifest by default;
  - verifies `disabled`, `no_wlan_ip`, `route_absent`, `connectivity_absent`,
    and `listener_safe`;
  - selects `controlled-android-reenable-observation` when V436 proves a
    persistent contained baseline.

## Validation Plan

```text
python3 -m py_compile scripts/revalidation/wifi_android_branch_decision_v437.py

python3 scripts/revalidation/wifi_android_branch_decision_v437.py \
  --out-dir tmp/wifi/v437-wifi-branch-decision-plan-<ts> plan

python3 scripts/revalidation/wifi_android_branch_decision_v437.py \
  --out-dir tmp/wifi/v437-wifi-branch-decision-hostrun-<ts> run

git diff --check
```

## Expected Decisions

- `v437-wifi-branch-plan-ready`
- `v437-wifi-branch-controlled-reenable-selected`
- `v437-wifi-branch-review-required`
- `v437-wifi-branch-missing-v436`
- `v437-wifi-branch-v436-failed`

Any PASS decision must keep `device_commands_executed=False`,
`device_mutations=False`, and `wifi_bringup_executed=False`.

## Next Gate Rule

If V437 selects controlled re-enable, V438 may allow exactly one bounded Android
Wi-Fi mutation:

```text
cmd wifi set-wifi-enabled enabled
```

V438 must still forbid scan/connect, credentials, server exposure, external
packet probes, DHCP/routing mutation, and new Wi-Fi-facing listeners.  It should
only observe what Android does after re-enable and then restore native v319.
