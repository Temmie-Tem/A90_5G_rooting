# Native Init v394 Post-V392 Router Plan

## Goal

Add a host-only router that consumes V392 executor/framechain manifests and selects the next safe Wi-Fi work item after the approved V392 backchain capture.

The router must not open the serial bridge, deploy helpers, start service-manager, start Wi-Fi HAL, scan, connect, collect credentials, or mutate the device.

## Inputs

- V392 executor manifest:
  - `tmp/wifi/v392-approved-full-*/manifest.json`
  - or an explicitly supplied `--executor-manifest`
- V392 framechain analyzer manifest:
  - inferred from `<executor-run>/framechain/manifest.json`
  - or an explicitly supplied `--framechain-manifest`

## Decision Model

- `v392-post-live-router-awaiting-executor`
  - no V392 executor evidence exists
- `v392-post-live-router-awaiting-approval`
  - executor is plan/no-approval gated
- `v392-post-live-router-scope-violation`
  - any evidence reports Wi-Fi bring-up
- `v392-post-live-router-blocked`
  - deploy/live preflight failed
- `v392-post-live-router-hal-start-only-packet-ready`
  - service-manager start-only path is clean
- `v392-post-live-router-symbolized-caller-ready`
  - framechain has non-abort symbolized caller candidates
- `v392-post-live-router-symbolized-abort-only`
  - framechain symbolized but still only abort-family frames are visible
- `v392-post-live-router-elf-artifact-required`
  - frame map rows exist but matching ELF is unavailable
- `v392-post-live-router-frame-maprow-required`
  - frame return addresses exist but map rows are missing
- `v392-post-live-router-awaiting-backchain-live`
  - V392 frame-chain evidence is not yet present
- `v392-post-live-router-manual-review`
  - unexpected or ambiguous manifest state

## Validation

- `python3 -m py_compile scripts/revalidation/wifi_v392_post_live_router.py`
- Synthetic regression must cover missing, awaiting approval, scope violation, blocked, symbolized caller, abort-only, maprow-ready, no-maprow, and needs-live cases.
- Route current no-approval V392 evidence to `v392-post-live-router-awaiting-approval`.
- Confirm router manifests always report:
  - `device_commands_executed=False`
  - `device_mutations=False`
  - `daemon_start_executed=False`
  - `wifi_bringup_executed=False`

## Expected Outcome

After the approved V392 run, the next step should be selected from evidence rather than manually inferred. Wi-Fi HAL/start/scan/connect remain blocked until service-manager runtime evidence is clean enough for a separate HAL start-only approval packet.
