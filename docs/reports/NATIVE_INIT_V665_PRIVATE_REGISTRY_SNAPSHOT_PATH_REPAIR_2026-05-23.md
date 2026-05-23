# Native Init V665 Private Registry Snapshot Path Repair Report

- date: `2026-05-23 KST`
- status: `live-pass`; Wi-Fi external ping is **not** complete
- helper: `a90_android_execns_probe v109`
- runner: `scripts/revalidation/native_wifi_private_registry_snapshot_path_repair_v665.py`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v109_deploy_preflight.py`
- live evidence: `tmp/wifi/v665-private-registry-snapshot-path-repair-live-retry/`
- decision: `v665-private-registry-snapshot-path-repair-pass`

## Scope

V665 fixes the V664 observation gap where the helper context had a private
`/dev/__properties__`, but the registry snapshot still inspected host/global
`/dev` paths. The live proof remains below Wi-Fi bring-up: no fresh CNSS retry,
no Wi-Fi HAL, no scan/connect, no DHCP, no route change, and no external ping.

## Changes

- Updated `stage3/linux_init/helpers/a90_android_execns_probe.c` to helper
  `v109`.
- Changed registry snapshot capture to use helper private temp-root paths for
  `dev/__properties__` and `dev/socket`.
- Added explicit path keys for before/after registry snapshots.
- Added `scripts/revalidation/native_wifi_private_registry_snapshot_path_repair_v665.py`.
- Added `scripts/revalidation/wifi_execns_helper_v109_deploy_preflight.py`.
- Fixed V664 parsing/classification so a service `74` timeout remains a gate
  timeout instead of being overwritten by materialization classification.

## Validation

Static validation:

```text
python3 -m py_compile scripts/revalidation/native_wifi_private_runtime_materialization_v664.py scripts/revalidation/native_wifi_private_registry_snapshot_path_repair_v665.py scripts/revalidation/wifi_execns_helper_v109_deploy_preflight.py
bash scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v665-execns-helper-v109-build/a90_android_execns_probe
strings tmp/wifi/v665-execns-helper-v109-build/a90_android_execns_probe | rg 'a90_android_execns_probe v109|dev_properties_capture_path|dev_socket_capture_path|wifi-companion-service74-gated-vnd-service-manager-registry-snapshot-start-only'
```

Build result:

```text
sha256: eda3e88405d15cfa2b12ef3252cef3ff25ba23aae69aeb5075700fa147150030
static: no dynamic section
```

Live prerequisite refresh:

- V641 one-shot clean-DSP refresh:
  `tmp/wifi/v665-v641-refresh-20260523-121542/`
- V401 SELinuxfs mount after V641:
  `tmp/wifi/v665-v401-toybox-selinuxfs-mount-after-v641/`
- V490 current-boot policy load:
  `tmp/wifi/v665-v490-current-run/`
- Helper v109 serial deploy:
  `tmp/wifi/v665-execns-helper-v109-deploy-live-1850/`

The first V665 live attempt reached cleanup safely but service `74` did not
open, so it did not reach the registry snapshot phase. After another clean-DSP
and V490 refresh, the retry passed:

```text
decision: v665-private-registry-snapshot-path-repair-pass
pass: True
wifi_bringup_executed: False
```

Key materialization values from the passing retry:

| key | value |
| --- | --- |
| context_dev_properties_exists | `1` |
| context_dev_properties_access_r | `1` |
| context_dev_properties_access_x | `1` |
| property_service_shim_started | `1` |
| property_service_shim_postflight_safe | `1` |
| before_dev_properties_capture_path | `/tmp/a90-v231-632/root/dev/__properties__` |
| after_dev_properties_capture_path | `/tmp/a90-v231-632/root/dev/__properties__` |
| before_dev_socket_capture_path | `/tmp/a90-v231-632/root/dev/socket` |
| after_dev_socket_capture_path | `/tmp/a90-v231-632/root/dev/socket` |
| before_dirs_captured | `2` |
| after_dirs_captured | `2` |
| before_end | `1` |
| after_end | `1` |

## Interpretation

V665 proves that the private property/runtime snapshot path is now real, not a
host/global `/dev` false negative. The next blocker is no longer snapshot path
visibility. The next bounded gate should retry fresh `cnss-daemon` after the
proven service `74` and `vndservicemanager` readiness path, while still blocking
Wi-Fi HAL and actual network bring-up.

## Next Gate

Plan V666 as a fresh CNSS retry with the repaired private property/runtime
snapshot surface. Required guardrails remain: no Wi-Fi HAL start, no scan or
connect, no credentials, no DHCP, no route changes, and no external ping until
WLFW/WLAN-PD/BDF/`wlan0` evidence advances.
