# Native Init v286 ICNSS Boot Timing Compare Report

- date: `2026-05-19`
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- boot image change: none
- result: PASS
- decision: `icnss-boot-timing-gap-mapped`

## Summary

v286 adds and validates a read-only Android/TWRP/native ICNSS boot timing
comparator.

The tool consumes existing Android/TWRP Wi-Fi evidence and collects current
native-init evidence through cmdv1.  It does not run Wi-Fi daemons, send
QMI/QRTR packets, write rfkill/sysfs, or perform Wi-Fi scan/connect/link-up.

The comparison maps the first missing native event to Android userspace Wi-Fi
service ordering:

```text
first missing native event: android_wifi_action
```

Android reaches the following sequence:

```text
vendor.wifi_hal_ext start       ~7.021s
cnss_diag start                 ~7.820s
wificond start                  ~7.899s
cnss-daemon start               ~8.090s
wlfw_start                      ~8.220s
QMI server connected            ~9.435s
BDF download                    ~9.509s
WLAN FW ready                   ~14.511s
firmware config load            ~14.518s
wlan driver logs                ~14.525s
FW ready event                  ~14.596s
wlan0 netdev evidence           ~14.815s
```

Native current evidence has late residual CNSS start-only logs from prior
experiments, but within the configured native boot window it does not show the
Android Wi-Fi service ordering or readiness chain.

## Implemented

- Added plan:
  - `docs/plans/NATIVE_INIT_V286_ICNSS_BOOT_TIMING_COMPARE_PLAN_2026-05-19.md`
- Added tool:
  - `scripts/revalidation/wifi_icnss_boot_timing_compare.py`

The tool supports:

- `plan`
- `run`
- Android dmesg file input
- Android/TWRP manifest fallback input
- live native cmdv1 collection
- native boot-window filtering to avoid mistaking old start-only dmesg entries
  for boot-time events

## Static Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Result: PASS.

## Plan Gate

```bash
python3 scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  --out-dir tmp/wifi/v286-icnss-boot-timing-plan \
  plan
```

Result:

```text
decision: icnss-boot-timing-plan-ready
pass: True
```

## Live Native Validation

Final PASS run:

```bash
python3 scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  --out-dir tmp/wifi/v286-icnss-boot-timing-native-20260519-133421 \
  run
```

Result:

```text
decision: icnss-boot-timing-gap-mapped
pass: True
out_dir: /home/temmie/dev/A90_5G_rooting/tmp/wifi/v286-icnss-boot-timing-native-20260519-133421
```

Evidence:

```text
tmp/wifi/v286-icnss-boot-timing-native-20260519-133421/manifest.json
tmp/wifi/v286-icnss-boot-timing-native-20260519-133421/summary.md
tmp/wifi/v286-icnss-boot-timing-native-20260519-133421/native/
```

## Key Evidence

From the final manifest:

```text
native_version_matches: true
android_event_count: 195
twrp_event_count: 3
native_event_count: 132
native_boot_window_sec: 300.0
native_late_event_count: 132
first_missing_native: android_wifi_action
```

The `native_late_event_count` entries are old dmesg entries from prior
start-only experiments and are intentionally excluded from the boot-window
comparison.

Missing native boot-window events:

```text
android_wifi_action
wifi_hal_start
cnss_diag_start
wificond_start
cnss_daemon_start
wlfw_start
qmi_server_connected
bdf_download
wlan_fw_ready
firmware_load
wlan_driver_log
fw_ready_event
wlan_netdev
wiphy_rfkill
```

## Interpretation

v286 narrows the gap:

- ICNSS platform support is present in the stock kernel.
- Android/TWRP evidence shows the ICNSS platform and Android service chain can
  eventually produce `wlan0`/rfkill/wiphy evidence.
- Native start-only experiments safely launch and stop `cnss-daemon`, but do
  not reproduce Android's full Wi-Fi service ordering or WLFW/QMI readiness
  sequence.

The next useful step is not another blind start-only retry.  The next plan
should model Android's service ordering and decide whether the next safe probe
is:

1. no-scan service-order replay with `vendor.wifi_hal_ext`, `cnss_diag`,
   `wificond`, and `cnss-daemon` boundaries; or
2. a separately approved minimal WLFW/QMI handshake probe.

## Guardrails

- No daemon execution.
- No QMI payload.
- No QRTR nameservice packet.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No rfkill write.
- No ICNSS bind/unbind.
- No reboot/recovery/poweroff.
- No Android partition write.

## Next

Recommended v287:

```text
Android Wi-Fi service-order replay plan
```

Purpose:

- turn the v286 timing chain into an explicit no-scan execution model;
- define which services are read-only/status-only, which are start-only, and
  where QMI/packet boundaries would begin;
- keep active Wi-Fi link-up and credentials blocked.
