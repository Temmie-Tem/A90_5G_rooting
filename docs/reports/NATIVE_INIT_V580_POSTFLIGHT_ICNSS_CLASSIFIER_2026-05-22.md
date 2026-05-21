# Native Init V580 Postflight ICNSS Classifier

- date: `2026-05-22 KST`
- objective: separate the V579 cleanup artifact from the real Wi-Fi blocker, using read-only current-state evidence
- status: `classified`; Wi-Fi external ping is **not** complete

## Scope

- Consume V579 evidence from `tmp/wifi/v579-v95-companion-driver-state/manifest.json`.
- Capture current native state with read-only commands only.
- Verify whether V579's failed cleanup gate represents a real residual-process hazard.
- Confirm whether the stable blocker is still below `qcwlanstate ON` and `IWifi.start()`.

## Guardrails

- No daemon start.
- No Wi-Fi HAL start.
- No qcwlanstate or sysfs write.
- No scan/connect/link-up/DHCP/routing.
- No external ping.
- No Android partition write.

## Implementation

- `scripts/revalidation/native_wifi_v579_postflight_icnss_v580.py`
  - loads V579 and V514 evidence
  - captures current `status`, `selftest`, `a90_wlanbootctl status`, process table, `/sys/class/net`, `/sys/class/ieee80211`, `/proc/net/dev`, `/proc/net/qrtr`, and `dmesg`
  - verifies no current helper-owned Wi-Fi companion/HAL/CNSS process remains
  - reclassifies V579's helper cleanup failure against delayed native PID1 reaper evidence
  - classifies `qcwlanstate ON` `EINVAL` plus `icnss: Modules not initialized just return` as the current blocker

## V580 Result

Command result:

```text
decision: v580-delayed-clean-icnss-module-init-blocker-confirmed
pass: True
reason: V579 helper cleanup false is explained by delayed reaping; the stable blocker is qcwlanstate EINVAL with ICNSS modules-not-initialized
next: build V581 Android-vs-native ICNSS module-init ordering comparator before any more driver-state or IWifi.start retries
```

Evidence:

- `tmp/wifi/v580-v579-postflight-icnss/`

## Current Surface

```text
native_healthy=True
target_process_count=0
reaper.total=1
reaper.last_pid=987
reaper.last=signal=15
/dev/wlan=char 478:0
qcwlanstate=OFF
wlan0_exists=False
ieee80211_count=0
proc_net_qrtr_present=False
```

## V579 Reclassified

V579's own helper window reported:

```text
all_postflight_safe=False
wifi_hal_legacy.postflight_safe=0
wifi_hal_legacy.reaped=0
wifi_hal_legacy.kill_sent=1
driver_state_write_executed=True
driver_state_write_rc=1
driver_state_write_errno=22
driver_state_write_duration_ms=20205
qipcrtr_sockets_window=0
qrtr_readback_qmi_attempted=0
qrtr_readback_service_events=0
wlan_count_window=0
phy_count_window=0
scan_connect_linkup=False
external_ping=False
```

V580 proves the cleanup issue did not persist:

```text
delayed-postflight-process-clean: pass
target_process_count=0
native PID1 reaper consumed pid=987 with signal=15
```

So the V579 result should not be interpreted as “live state unsafe”. It should be interpreted as “helper timeout/reap accounting too strict for this child”, with the device back at a clean native state.

## ICNSS Blocker

The dmesg classifier found:

```text
modules_not_initialized=55
timed_out=2
wifi_turning_on=2
cnss_netlink=72
driver_loaded=0
driver_load_failure=0
qmi_server_connected=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
```

This matches the V514/V579 pattern:

- `cnss_diag` and `cnss-daemon` reach `cld80211` netlink.
- `/dev/wlan` exists and the driver-state write reaches the driver.
- The write returns `EINVAL` after waiting.
- No QRTR/QMI/BDF/WLFW readiness marker appears.
- No `wlan0`, wiphy, or scan-capable surface appears.

## Source Interpretation

The upstream QCACLD path shows `qcwlanstate` accepts `ON`, waits for driver load completion when `cds_is_driver_loaded()` is false, and returns `-EINVAL` on timeout. The same source logs `Modules not initialized just return` when the WLAN driver status is still `DRIVER_MODULES_UNINITIALIZED`.

That matches the current native evidence: native has reached the qcwlanstate control path, but not the lower ICNSS/WLAN module initialization state needed before `IWifi.start()` can advance.

Source:

- `wlan_hdd_main.c` in Android kernel/msm QCACLD: https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c

## Next Gate

Recommended V581:

1. Build an Android-vs-native ICNSS module-init ordering comparator.
2. Compare markers around:
   - `boot_wlan`
   - WLAN driver load/state initialized
   - service locator reconnect
   - QRTR namespace readiness
   - WLAN-PD/service-notifier readiness
   - `cnss-daemon` WLFW start
   - BDF/FW-ready events
3. Keep qcwlanstate retry, `IWifi.start()`, scan, connect, and ping blocked until a below-qcwlanstate dependency changes.
