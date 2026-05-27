# Native Init V1137 Post-PM mdm_helper Composite Helper Build Report

Date: `2026-05-27`

## Result

- Decision: `v1137-execns-helper-v214-post-pm-mdm-helper-composite-built`
- Pass: `true`
- Source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- Artifact: `tmp/wifi/v1137-execns-helper-v214-build/a90_android_execns_probe`
- SHA256: `4dd6dea42fddfc1b70732e5695323421a0abf505530ab2d437c6e5418a75638f`
- Size: `1253872`

## Summary

V1137 is source/build-only. It implements the V1136-selected helper surface:

```text
V1134 upper PM/CNSS path
  + post-PM mdm_helper/eSoC observer
```

The helper version is now:

```text
a90_android_execns_probe v214
```

New guarded mode:

```text
wifi-companion-post-pm-mdm-helper-esoc-observer
```

New live-only allow/start flags:

```text
--allow-post-pm-mdm-helper-esoc-observer
--pm-observer-start-mdm-helper-after-cnss
```

## Implementation

- Added a PM observer mode alias for post-PM `mdm_helper`/eSoC observation.
- Added fail-closed validation for the new allow flag and CNSS-before-mdm-helper start contract.
- Extended the PM observer child set with `mdm_helper` after `cnss-daemon`.
- Preserved the existing service-manager, PM provider, CNSS PM register/connect path.
- Added post-PM output fields for:
  - `mdm_helper` observability;
  - `/dev/esoc-0` and `/dev/subsys_esoc0` fd counts;
  - MHI pipe fd/process evidence;
  - `ks` process evidence;
  - queue/provider readiness snapshots;
  - `mss`/`mdm3`, QRTR/WLFW/BDF/MHI/wlan0 lower-surface snapshots.

## Guardrails

This build did not execute any live device action.

- Deploy: not executed.
- PM/CNSS live actors: not executed.
- Wi-Fi HAL: not executed.
- Scan/connect/link-up: not executed.
- Credentials: not used.
- DHCP/route/external ping: not executed.
- Partition write/boot image write/flash/reboot: not executed.

The new mode also emits explicit guardrail fields:

```text
post_pm_mdm_helper_esoc_observer.wifi_hal_start_executed=0
post_pm_mdm_helper_esoc_observer.scan_connect_linkup=0
post_pm_mdm_helper_esoc_observer.credentials=0
post_pm_mdm_helper_esoc_observer.dhcp_routing=0
post_pm_mdm_helper_esoc_observer.external_ping=0
```

## Validation

Executed:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v1137-execns-helper-v214-build/a90_android_execns_probe

strings tmp/wifi/v1137-execns-helper-v214-build/a90_android_execns_probe \
  | rg 'a90_android_execns_probe v214|wifi-companion-post-pm-mdm-helper-esoc-observer'

git diff --check
```

Build result:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
There is no dynamic section in this file.
```

Marker result:

```text
version_marker=a90_android_execns_probe v214
mode_marker=wifi-companion-post-pm-mdm-helper-esoc-observer
allow_marker_present=1
start_marker_present=1
result_marker_present=1
```

## Next

V1138 should be deploy/check-only for helper `v214`:

1. deploy the static helper only;
2. verify remote SHA/version/usage markers;
3. run native health/selftest;
4. do not start PM actors, `mdm_helper`, Wi-Fi HAL, scan/connect, credentials, DHCP, route, external ping, or flash.

Only after V1138 passes should a bounded V1139 live gate run the new mode.
