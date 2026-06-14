# Native Init Wi-Fi V478-V482 SELinux Context Handoff Report

Date: 2026-05-21

## Goal

Move native-init Wi-Fi bring-up toward a verified Samsung Wi-Fi HAL registration path before any scan, credential use, association, DHCP, routing, or external ping.

## Scope Executed

- Deployed execns helper v37 through v41 to `/cache/bin/a90_android_execns_probe` only.
- Ran child-only SELinux exec-context proofs.
- Ran bounded Samsung `ISehWifi/default` registration smoke with service-manager, hwservicemanager, Samsung Wi-Fi HAL, and CNSS only.
- Did not run Wi-Fi scan/connect/link-up, did not read credentials, and did not run external ping.

## Key Evidence

| Version | Evidence | Decision | Result |
| --- | --- | --- | --- |
| V478/v37 | `tmp/wifi/v478-native-selinux-domain-proof-run-20260521-031935/manifest.json` | `v478-native-selinux-domain-proof-pass` | Initial proof was too weak: write returned success but exec attr readback stayed `kernel`. |
| V479/v38 | `tmp/wifi/v479-samsung-registration-selinux-context-run2-20260521-034208/manifest.json` | `v479-samsung-wifi-registration-selinux-context-absent` | Registration absent; service/HAL children still showed `selinux.exec=kernel`. |
| V480/v39 | `tmp/wifi/v480-native-selinux-domain-proof-v39-20260521-035133/manifest.json` | `v478-native-selinux-domain-proof-blocked` | NUL-inclusive attr write still did not produce target readback. |
| V481/v40 | `tmp/wifi/v481-native-selinux-domain-proof-v40-20260521-040046/manifest.json` | `v478-native-selinux-domain-proof-blocked` | Thread-local attr path still did not produce target readback. |
| V482/v41 | `tmp/wifi/v482-native-selinux-domain-proof-v41-20260521-040931/manifest.json` | `v478-native-selinux-domain-proof-blocked` | Post-exec probe did not prove transition; postexec child died with signal 11. |
| V482/v41 | `tmp/wifi/v479-samsung-registration-selinux-context-v41-20260521-040955/manifest.json` | `v479-samsung-wifi-registration-selinux-context-absent` | Cleanup clean, but Samsung `ISehWifi/default` still not registered. |

## Current Blocker

The native-init process runs as SELinux context `kernel`. Attempts to set Android service/HAL exec contexts report write success, but the observable context remains `kernel`:

- `servicemanager`: requested `u:r:servicemanager:s0`, observed `selinux.exec=kernel`
- `hwservicemanager`: requested `u:r:hwservicemanager:s0`, observed `selinux.exec=kernel`
- Samsung Wi-Fi HAL: requested `u:r:hal_wifi_default:s0`, observed `selinux.exec=kernel`

The latest Samsung registration smoke still ends with:

- `child.wifi_hal.signal=6`
- `wifi_hal_composite_start.result=service-query-runtime-gap`
- `libc: Unable to set property "hwservicemanager.ready" to "true": connection failed; errno=2`
- `Service not found (missing permissions or not in VINTF manifest?).`

## Interpretation

Property-area read issues from V475/V476 are no longer the dominant blocker. The remaining gap is Android runtime parity for daemon execution:

1. Android SELinux domain handoff is not proven under native init.
2. Android property service write socket is absent, so `property_set()` callers such as hwservicemanager cannot update runtime properties.
3. Samsung Wi-Fi HAL still aborts before registering `vendor.samsung.hardware.wifi@2.x::ISehWifi/default`.

## Next Work

V483 should focus on runtime service prerequisites, not Wi-Fi credentials or connect yet:

1. Capture exact crash/backtrace or abort reason for Samsung Wi-Fi HAL under v41.
2. Build a bounded property-service socket proof for `hwservicemanager.ready` only, or prove that socket absence is non-fatal.
3. Capture actual `/proc/<pid>/attr/current` for live manager/HAL children before cleanup.
4. Decide whether native init can safely host Android service domains, or whether Wi-Fi bring-up must happen through Android boot/init handoff.

## External Reference

Android libselinux `setexeccon` writes to `/proc/self/task/<tid>/attr/exec` with `strlen(context) + 1`, which informed the v39/v40 helper corrections.

- https://android.googlesource.com/platform/external/libselinux/+/jb-dev/src/procattr.c
