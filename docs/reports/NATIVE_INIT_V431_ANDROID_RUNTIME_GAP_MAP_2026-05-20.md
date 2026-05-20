# Native Init V431 Android Wi-Fi Runtime Gap Map Report

Date: 2026-05-20

## Summary

V431 added a read-only Android runtime gap mapper and a boot-complete handoff
wrapper.  The corrected `su -c` live run passed with:

```text
decision: v431-android-runtime-gap-map-pass
pass: True
reason: Android runtime gap map captured daemon, init definition, service, socket, device, netdev, and data surfaces
wifi_bringup_executed: False
```

The run temporarily booted Android, collected read-only runtime evidence, then
restored native init `A90 Linux init 0.9.61 (v319)`.  No Wi-Fi enable, scan,
connect, link-up, credential, DHCP, routing, rfkill/sysfs write, module
operation, `setprop`, persistent autostart change, or direct daemon start was
executed by the test.

## Implementation

- `scripts/revalidation/wifi_android_runtime_gap_v431.py`
  - read-only Android collector for Wi-Fi process, init rc, framework service,
    proc/fd/maps, socket, devnode, netdev/rfkill, and data directory surfaces;
  - supports `--su` using remote-shell-safe `su -c <quoted command>`;
  - strips command lines before surface classification to avoid false positives;
  - records private evidence and redacts sensitive identifiers.
- `scripts/revalidation/android_wifi_runtime_gap_handoff_v431.py`
  - reuses Android boot-complete handoff and native rollback primitives;
  - supports `--collector-su` to run the V431 collector through `su -c`;
  - compares the captured Android runtime map with V429/V430 references.

## Static Validation

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_runtime_gap_v431.py \
  scripts/revalidation/android_wifi_runtime_gap_handoff_v431.py

git diff --check
```

Both checks passed.

Plan and dry-run evidence:

```text
tmp/wifi/v431-android-runtime-gap-plan-20260520-150722/
tmp/wifi/v431-android-runtime-gap-handoff-plan-20260520-150722/
tmp/wifi/v431-android-runtime-gap-handoff-dryrun-20260520-150722/
tmp/wifi/v431-android-runtime-gap-plan-fix-20260520-151142/
tmp/wifi/v431-android-runtime-gap-handoff-dryrun-fix-20260520-151142/
tmp/wifi/v431-android-runtime-gap-handoff-dryrun-su-20260520-151831/
tmp/wifi/v431-android-runtime-gap-handoff-dryrun-su-quote-20260520-152302/
```

## Live Evidence

Corrected privileged read-only live handoff:

```text
tmp/wifi/v431-android-runtime-gap-handoff-live-su-quote-20260520-152315/
decision: v431-android-runtime-gap-map-pass
pass: True
device_commands_executed: True
device_mutations: True
wifi_bringup_executed: False
```

Collector evidence:

```text
tmp/wifi/v431-android-runtime-gap-handoff-live-su-quote-20260520-152315/v431-android-runtime-gap-run/
decision: v431-android-runtime-gap-map-pass
pass: True
captures all ok: True
```

Superseded live attempts:

```text
tmp/wifi/v431-android-runtime-gap-handoff-live-20260520-150740/
  PASS, but two read-only captures had rc noise and unprivileged /data layout was weak.

tmp/wifi/v431-android-runtime-gap-handoff-live-fix-20260520-151152/
  PASS, capture rc noise fixed, but /data/vendor/wifi layout still required privileged read-only visibility.

tmp/wifi/v431-android-runtime-gap-handoff-live-su-20260520-151844/
  FAIL with rollback complete; root command quoting used `adb shell su -c <args>` and broke shell loops.
```

Rollback/postflight after corrected live:

```text
version: A90 Linux init 0.9.61 (v319)
selftest: pass=11 warn=1 fail=0
status: rc=0 status=ok
```

## Runtime Targets

The corrected V431 map found all target runtime services as both running
processes and init rc definitions:

| Target | Process | Init rc definition |
| --- | --- | --- |
| `android.hardware.wifi@1.0-service` | yes | yes |
| `vendor.samsung.hardware.wifi@2.0-service` | yes | yes |
| `wificond` | yes | yes |
| `wpa_supplicant` | yes | yes |

Relevant process surface also included:

```text
WCNSS_CNTL / WCNSS_DATA / WCNSS_CMD / WCNSS_DCI / WCNSS_DCI_CMD kernel threads
wlan_logging_th
cnss_diag
cnss-daemon
com.samsung.android.server.wifi.mobilewips
```

## Init rc Findings

Key init definitions captured by V431:

```text
/vendor/etc/init/android.hardware.wifi@1.0-service.rc:
  service vendor.wifi_hal_legacy /vendor/bin/hw/android.hardware.wifi@1.0-service
  interface android.hardware.wifi@1.0::IWifi default
  interface android.hardware.wifi@1.1::IWifi default
  interface android.hardware.wifi@1.2::IWifi default
  interface android.hardware.wifi@1.3::IWifi default
  interface android.hardware.wifi@1.4::IWifi default
  class hal
  capabilities NET_ADMIN NET_RAW SYS_MODULE
  user wifi
  group wifi gps

/vendor/etc/init/vendor.samsung.hardware.wifi@2.0-service.rc:
  service vendor.wifi_hal_ext /vendor/bin/hw/vendor.samsung.hardware.wifi@2.0-service
  interface vendor.samsung.hardware.wifi@2.0::ISehWifi default
  interface vendor.samsung.hardware.wifi@2.1::ISehWifi default
  interface vendor.samsung.hardware.wifi@2.2::ISehWifi default
  class hal
  capabilities NET_ADMIN NET_RAW SYS_MODULE
  user wifi
  group wifi gps

/vendor/etc/init/android.hardware.wifi.supplicant-service.rc:
  service wpa_supplicant /vendor/bin/hw/wpa_supplicant
  -O/data/vendor/wifi/wpa/sockets
  -g@android:wpa_wlan0
  socket wpa_wlan0 dgram 660 wifi wifi
```

V431 also captured `hostapd`, `cnss-daemon`, `cnss_diag`, data directory mkdir
rules, and `wifi.interface wlan0` property context from vendor init files.

## Runtime Surface Findings

Framework services present:

```text
sem_wifi
sem_wifi_aware
sem_wifi_p2p
wifi
wifiaware
wifinl80211
wifip2p
wifiscanner
```

Sockets/devnodes present:

```text
/dev/socket/wifihal/wifihal_ctrlsock
/dev/socket/wpa_wlan0
/data/vendor/wifi/wpa/sockets/wlan0
/data/vendor/wifi/sockets/cnss_user_server
/dev/wlan  u:object_r:vendor_wlan_device:s0
```

Netdev/rfkill surface:

```text
wlan0: UP, LOWER_UP, DORMANT
swlan0: DOWN
wifi-aware0: DOWN
/sys/class/net/* driver path includes icnss
```

Data layout, with filenames only and no credential contents read:

```text
/data/vendor/wifi
/data/vendor/wifi/hostapd/sockets
/data/vendor/wifi/wpa/sockets
/data/vendor/wifi/wpa/wpa_supplicant.conf
/data/vendor/wifi/cnss_diag.conf
/data/vendor/wifi/sockets/cnss_user_server
```

## Interpretation

V431 establishes that Android boot-complete has more than just static HAL rows:
it has the full running Wi-Fi runtime stack and runtime surfaces that native
private namespace tests have not reproduced.

The strongest current conclusions are:

- Android starts both AOSP and Samsung Wi-Fi HAL services with `NET_ADMIN`,
  `NET_RAW`, and `SYS_MODULE` capability declarations;
- Android also has `wificond`, `wpa_supplicant`, CNSS services, WCNSS kernel
  threads, Wi-Fi framework binder services, `/dev/wlan`, wpa/wifihal sockets,
  and `wlan0` already `UP,LOWER_UP`;
- native V429 still times out on binderized `lshal`, while V430 showed all
  Samsung `ISehWifi/default` rows through Android neat `lshal`;
- trying to reconstruct the full Android Wi-Fi runtime inside native private
  namespace is likely more expensive than using Android-managed runtime control
  for the first bring-up gate.

## Next

Recommended next cycle: V432 Android-managed Wi-Fi control gate plan.

V432 should not immediately connect to a network.  It should define and verify a
strictly bounded first-control gate around Android's existing runtime:

1. preflight read-only state using the V431 runtime map;
2. decide which single Android-managed control primitive is least invasive;
3. block credentials, external network routing, and arbitrary scans unless a
   later explicit gate approves them;
4. include rollback/disable/cleanup evidence and native restore path.

If V432 proves the control gate is safe, the following versions can split into
Wi-Fi enable-only, scan-only, and connect-only gates instead of combining them.
