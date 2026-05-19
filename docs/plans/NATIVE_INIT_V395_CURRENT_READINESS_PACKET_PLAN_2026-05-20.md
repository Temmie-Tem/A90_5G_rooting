# Native Init v395 Current V392 Readiness Packet Plan

## Goal

Create a current approval-readiness packet for the V392 helper v21 deploy and service-manager backchain capture cycle.

The packet must be host-only. It must read already collected safe evidence, emit the exact approved command sequence, and never open the serial bridge, deploy helpers, start daemons, start Wi-Fi HAL, scan, connect, collect credentials, or mutate the device.

## Inputs

- V392 helper v21 deploy preflight manifest.
- V392 service-manager backchain live preflight manifest.
- V392 no-approval executor manifest.
- V394 post-live router manifest.
- Optional read-only `a90ctl` JSON captures:
  - `version`
  - `status`
  - `selftest`

## Expected Current State

Before approval, the correct state is:

- local helper v21 exists and matches expected SHA.
- remote helper is still v20, so deploy preflight is blocked only by expected `remote-helper-v21` and approval gate.
- live preflight is blocked only by helper v21 not yet being deployed and approval gate.
- no-approval executor is fail-closed.
- post-live router points to awaiting approval.
- device health is read-only clean.
- no Wi-Fi HAL/start/scan/connect actions occur.

## Decision Labels

- `v392-current-readiness-ready-for-approval`
  - all blocker checks are in expected pre-approval state
- `v392-current-readiness-blocked`
  - at least one blocker check is missing, unsafe, or not in expected state
- `v392-current-readiness-regression-pass`
  - synthetic regression cases pass
- `v392-current-readiness-regression-failed`
  - synthetic regression cases fail

## Validation

- `python3 -m py_compile scripts/revalidation/wifi_v392_current_readiness_packet.py`
- Regression must cover:
  - ready state
  - scope violation
  - missing deploy preflight
- Current packet must decide `v392-current-readiness-ready-for-approval`.
- Packet output must report:
  - `device_commands_executed=False`
  - `device_mutations=False`
  - `daemon_start_executed=False`
  - `wifi_bringup_executed=False`

## Expected Outcome

The next operator action is a single exact-approved V392 executor run. After that run, the V394 post-live router should consume the executor manifest and choose the next safe Wi-Fi work item.
