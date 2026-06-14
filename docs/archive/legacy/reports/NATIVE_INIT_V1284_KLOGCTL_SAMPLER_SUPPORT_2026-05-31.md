# Native Init V1284 klogctl Sampler Support

- generated: 2026-05-31
- cycle: V1284
- command: source/build-only
- decision: `v1284-klogctl-sampler-build-pass`
- pass: true
- helper: `a90_android_execns_probe v269`
- stage3 binary: `stage3/linux_init/helpers/a90_android_execns_probe_v269`
- sha256: `dbb1f67652913ffe94b1f083a082d8f221820040b9f28e08b226eb1e0a50fc83`
- size: `1319408`

## Scope

V1284 repairs the V1283 kernel-log collector gap. V1283 proved that `/dev/kmsg`
is absent in the native runtime, while `/proc/kmsg` exists and BusyBox `dmesg`
can read kernel output. The helper now keeps the `/dev/kmsg` path first, then
falls back to a read-only `syslog(SYSLOG_ACTION_READ_ALL)`/klogctl read path.

This keeps the next live sampler inside the existing bounded PM-service response
window while allowing it to classify PCIe, GDSC, MHI, eSoC, SDX50M, ICNSS, WLFW,
and subsystem-restart kernel messages when `/dev/kmsg` is unavailable.

## Changes

- Bumped `stage3/linux_init/helpers/a90_android_execns_probe.c` to
  `a90_android_execns_probe v269`.
- Added `collect_response_syslog_markers()` as the klogctl fallback after a
  failed `/dev/kmsg` open.
- Added `kmsg_source` to the per-sample output so live reports can distinguish
  `dev-kmsg`, `syslog-read-all`, and failed collector paths.
- Extended `scripts/revalidation/native_wifi_late_per_proxy_response_sampler_live_v1242.py`
  to parse and summarize `kmsg_source`.
- Added `scripts/revalidation/native_wifi_response_sampler_klogctl_support_v1284.py`
  as the source/build-only gate.

## Validation

| check | result |
| --- | --- |
| V1283 input manifest | pass |
| Python compile | pass |
| helper build | pass |
| static aarch64 | pass |
| no interpreter | pass |
| no dynamic section | pass |
| required source strings | pass |
| required binary strings | pass |
| device commands | not executed |
| Wi-Fi bring-up | not executed |

Evidence:

- `tmp/wifi/v1284-execns-helper-v269-build/manifest.json`
- `tmp/wifi/v1284-execns-helper-v269-build/summary.md`
- `tmp/wifi/v1284-execns-helper-v269-build/logs/`

## Safety

No device command, deploy, PM actor, GPIO line request, PMIC write, direct eSoC
ioctl, Wi-Fi HAL start, scan/connect, credential use, DHCP/route change,
external ping, flash, boot image write, or partition write was executed by
V1284.

## Next

V1285 should deploy helper v269 only. V1286 should rerun the bounded
PCIe/GDSC/klogctl response sampler and verify whether the live collector uses
`syslog-read-all` and captures any response-window PCIe/GDSC/MHI/eSoC/SDX50M/
WLFW kernel markers.
