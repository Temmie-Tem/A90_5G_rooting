# v215 Plan: ICNSS/CNSS Lifecycle Research

## Summary

v215 follows the v214 `SAFETY STOP` result. The goal is to explain the ICNSS
lifecycle gap without running Wi-Fi bring-up or repeating unsafe generic sysfs
unbind/bind.

This version is read-only. It collects and correlates Android, TWRP, and native
ICNSS/CNSS/Wi-Fi lifecycle evidence, then produces a decision that determines
whether v216 can model Android service replay.

- baseline native runtime: `A90 Linux init 0.9.59 (v159)`
- blocking result: v214 `icnss-rebind-failed`
- collector: `scripts/revalidation/wifi_icnss_lifecycle_collect.py`
- evidence output: `tmp/wifi/v215-icnss-cnss-lifecycle`
- report after execution:
  `docs/reports/NATIVE_INIT_V215_ICNSS_CNSS_LIFECYCLE_RESEARCH_2026-05-13.md`

## Reference Notes

- Android init service definitions, service classes, property triggers, and
  `ctl.*` commands define the userspace lifecycle that native init must model
  before starting vendor Wi-Fi services:
  <https://chromium.googlesource.com/aosp/platform/system/core/+/master/init/README.md>
- Linux driver `probe()` and `remove()` are real lifecycle callbacks. v214
  showed that generic ICNSS platform-driver reprobe is unsafe on this kernel:
  <https://docs.kernel.org/6.7/driver-api/driver-model/driver.html>
- Linux firmware lookup policy only solves file discovery. It does not power or
  register ICNSS/WLAN by itself:
  <https://docs.kernel.org/driver-api/firmware/fw_search_path.html>
- Qualcomm ICNSS source references show recovery, PDR/SSR, service-location,
  debugfs/sysfs, firmware service, and driver registration paths that should be
  mapped before active Wi-Fi work:
  <https://android.googlesource.com/kernel/msm/+/c9760d512dc5a7d452676a4cc97cfcb683809c19/drivers/soc/qcom/icnss.c>

## Current Evidence Chain

- v206 Android evidence shows `cnss-daemon`, `cnss_diag`, Wi-Fi HAL,
  `wificond`, and supplicant services running when Android exposes WLAN objects.
- v214 proves direct ICNSS `unbind`/`bind` leaves driver binding broken until
  reboot.
- The next useful question is no longer “where is firmware?” but “which service
  and driver lifecycle events make ICNSS create WLAN netdev/wiphy state?”

## Scope

Allowed:

- parse existing v204/v206/v214 manifests and summaries
- collect read-only native bridge evidence
- collect read-only Android/TWRP ADB evidence when the device is already in
  those modes or when the operator intentionally boots them
- parse vendor/system init rc service definitions from captured text
- classify service ordering, triggers, binaries, properties, mounts, sysfs
  nodes, debugfs nodes, and dmesg/logcat hints
- write host-only evidence bundles

Forbidden:

- ICNSS `unbind` or `bind`
- Wi-Fi scan/connect
- `rfkill block` / `rfkill unblock`
- `ip link set wlan* up`
- `svc wifi`, `cmd wifi set-wifi-enabled`, or `dumpsys wifi` in default mode
- `cnss-daemon`, `cnss_diag`, Wi-Fi HAL, `wificond`, `wpa_supplicant`, or
  `hostapd` start
- module load/unload
- firmware path writes
- vendor/system mount mutations
- boot image or PID1 change

## Collector Design

Add `scripts/revalidation/wifi_icnss_lifecycle_collect.py`.

Inputs:

- `--native-bridge`
- `--android-adb`
- `--twrp-adb`
- `--v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json`
- `--v206-manifest tmp/wifi/v206-android-icnss-cnss-map/manifest.json`
- `--v214-manifest tmp/wifi/v214-icnss-reprobe/manifest.json`
- `--out-dir tmp/wifi/v215-icnss-cnss-lifecycle`

Default behavior:

- if no live mode is selected, parse existing manifests only
- if `--native-bridge` is selected, run only read-only `a90ctl` commands
- if `--android-adb` or `--twrp-adb` is selected, run only read-only ADB shell
  commands

Required captures:

- native:
  - `version`
  - `status`
  - `cat /sys/devices/platform/soc/18800000.qcom,icnss/uevent`
  - `ls /sys/devices/platform/soc/18800000.qcom,icnss`
  - `ls /sys/bus/platform/drivers/icnss`
  - `ls /sys/kernel/debug`
  - filtered `dmesg`
- Android/TWRP:
  - `getprop` Wi-Fi/CNSS/ICNSS/service properties
  - `init.svc.*` service states
  - `ps -A` filtered service/process list
  - filtered `dmesg`
  - filtered `logcat` where available
  - `find`/`grep` over init rc paths for Wi-Fi/CNSS services
  - sysfs net/rfkill/ieee80211/ICNSS state

Classifier output:

- service evidence count
- init rc evidence count
- Android running service list
- native missing service list
- ICNSS bound status
- WLAN object visibility
- debug/recovery control candidates
- v214 failure correlation
- recommended v216 input set

## Decision Model

- `lifecycle-map-ready`
  - Android service/init evidence, native ICNSS state, and v214 failure evidence
    are complete enough to build a service replay model.
- `android-only-required`
  - evidence indicates native init lacks a required Android-only runtime layer
    that cannot be cheaply modeled.
- `insufficient-live-evidence`
  - existing manifests are useful but live native/Android/TWRP capture is needed.
- `manual-review-required`
  - manifests conflict, required evidence is missing, or the collector cannot
    safely classify the state.

## Validation

Static:

```sh
python3 -m py_compile scripts/revalidation/wifi_icnss_lifecycle_collect.py
git diff --check
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_icnss_lifecycle_collect
wifi_icnss_lifecycle_collect.validate_no_active_commands()
print('v215 command guard PASS')
PY
```

Manifest-only:

```sh
python3 scripts/revalidation/wifi_icnss_lifecycle_collect.py \
  --v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json \
  --v206-manifest tmp/wifi/v206-android-icnss-cnss-map/manifest.json \
  --v214-manifest tmp/wifi/v214-icnss-reprobe/manifest.json \
  --out-dir tmp/wifi/v215-icnss-cnss-lifecycle
```

Native read-only:

```sh
python3 scripts/revalidation/wifi_icnss_lifecycle_collect.py \
  --native-bridge \
  --out-dir tmp/wifi/v215-icnss-cnss-lifecycle-native
```

Android/TWRP read-only:

```sh
python3 scripts/revalidation/wifi_icnss_lifecycle_collect.py \
  --android-adb \
  --out-dir tmp/wifi/v215-icnss-cnss-lifecycle-android
```

## Acceptance

- No active Wi-Fi or ICNSS mutation command exists in the collector's default
  command sets.
- Manifest-only mode works from existing evidence.
- Native mode works through the bridge when native init is available.
- Android/TWRP modes are optional and read-only.
- Summary clearly states whether v216 can proceed to Android service replay
  modeling.

## Next Step

If v215 returns `lifecycle-map-ready`, v216 should build the Android service
replay model. If it returns `insufficient-live-evidence`, collect the missing
Android/TWRP/native mode and rerun v215 before designing replay.
