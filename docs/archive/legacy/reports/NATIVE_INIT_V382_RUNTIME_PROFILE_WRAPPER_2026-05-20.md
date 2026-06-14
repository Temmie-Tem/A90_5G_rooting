# V382 Runtime Profile Wrapper Readiness Report

## Result

- decision: `v382-runtime-profile-wrapper-ready`
- scope: host-side runner/wrapper readiness only
- device mutations: `false`
- daemon_start_executed: `false`
- wifi_bringup_executed: `false`
- blocker before live run: `helper-v14`

## What Changed

- `scripts/revalidation/wifi_service_manager_start_only_live_runner.py`
  - added optional `--property-root`
  - added optional `--data-wifi-mode none|private-empty`
  - records both values into the generated plan
  - includes both values in the helper argv for service-manager start-only runs
  - preflights the property root with a read-only `stat`
- `scripts/revalidation/wifi_service_manager_start_only_v382_live_runner.py`
  - fixes V382 defaults to helper v14 sha256
  - fixes property root to `/mnt/sdext/a90/private-property-v317/dev/__properties__`
  - fixes data mode to `private-empty`

## Evidence

| phase | path | result |
| --- | --- | --- |
| plan | `tmp/wifi/v382-service-manager-live-wrapper-plan/manifest.json` | pass |
| preflight | `tmp/wifi/v382-service-manager-live-wrapper-preflight/manifest.json` | blocked only by remote helper v14 not deployed |
| deploy no-approval regression | `tmp/wifi/v382-deploy-noapproval-regression/manifest.json` | blocked, no mutation |
| live no-approval regression | `tmp/wifi/v382-live-noapproval-regression/manifest.json` | approval-required, no daemon start |

## Checks

- Python compile: PASS
- `git diff --check`: PASS
- V382 plan command includes:
  - `--data-wifi-mode private-empty`
  - `--property-root /mnt/sdext/a90/private-property-v317/dev/__properties__`
- V382 read-only preflight:
  - `property-root-visible`: PASS
  - `data-wifi-mode`: PASS
  - `helper-v14`: BLOCKED because the remote helper is still v13
- V382 deploy no-approval regression:
  - decision: `execns-helper-v14-deploy-blocked`
  - `device_mutations=false`
  - `daemon_start_executed=false`
  - `wifi_bringup_executed=false`
- V382 live no-approval regression:
  - decision: `service-manager-start-only-live-approval-required`
  - `steps_len=0`
  - `observations_len=0`
  - `daemon_start_executed=false`
  - `wifi_bringup_executed=false`

## Interpretation

V381 added helper support for private property runtime, but the old live runner
would not have passed the new runtime arguments. V382 now has a dedicated wrapper
that will exercise the intended v14 path once `/cache/bin/a90_android_execns_probe`
is updated.

## Next

Run the V382 deploy only after the exact approval phrase:

`approve v382 deploy execns helper v14 only; no daemon start and no Wi-Fi bring-up`

After the v14 deploy is verified, rerun the V382 live wrapper with the existing
service-manager start-only approval phrase. Wi-Fi HAL, scan, connect, DHCP, and
routing remain blocked.
