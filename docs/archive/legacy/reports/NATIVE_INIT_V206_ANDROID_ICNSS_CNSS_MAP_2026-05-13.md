# v206 Android ICNSS/CNSS Dependency Map

## Summary

v206 adds a host-side Android ADB collector for ICNSS/CNSS/Wi-Fi dependency
mapping. This is a read-only Wi-Fi investigation step and does not change the
native init boot image.

Result: PASS.

Final decision: `ready-for-native-preflight-plan`.

Reason: Android dependency map is complete enough to design a future native
read-only Wi-Fi preflight. This still does not approve active Wi-Fi bring-up.

## Changes

- Added `scripts/revalidation/android_icnss_cnss_map.py`.
- Added v206 plan:
  `docs/plans/NATIVE_INIT_V206_ANDROID_ICNSS_CNSS_MAP_PLAN_2026-05-13.md`.
- Updated task queue and next-work notes.

## Scope

The collector captures Android-side:

- Wi-Fi/CNSS/ICNSS init rc and property trigger evidence
- daemon/process state for `cnss`, `icnss`, `wificond`, Wi-Fi HAL, supplicant,
  hostapd, QMI/QRTR-adjacent components
- firmware candidates such as `bdwlan.bin`, `regdb.bin`, WCNSS/wlanmdsp files
- sysfs state for ICNSS, WLAN interfaces, rfkill, and `ieee80211`
- dmesg/logcat readiness evidence
- VINTF HAL declarations
- v204/v205 manifest comparison

## Static Validation

```bash
python3 -m py_compile scripts/revalidation/android_icnss_cnss_map.py
```

Result: PASS.

```bash
git diff --check
```

Result: PASS.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import android_icnss_cnss_map
android_icnss_cnss_map.validate_no_active_wifi_commands()
print('v206 command guard PASS')
PY
```

Result: PASS.

## Guardrails

- No Wi-Fi enablement.
- No rfkill write.
- No WLAN link-up.
- No scan/connect.
- No module load/unload.
- No firmware mutation.
- No Android Wi-Fi service/supplicant/hostapd/cnss-daemon start.
- No `/data/misc/wifi` default collection.

## Device Validation

Android boot transition:

- boot image flashed: `backups/baseline_a_20260423_030309/boot.img`
- Android boot image SHA256:
  `c15ce425abb8da41f0b1696d19d05a625fd7cec949b4ae50651a5f1e7293057b`
- Android ADB detected:
  `product:r3qks model:SM_A908N device:r3q`
- Magisk root check:
  `uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0`

Collector run:

```bash
python3 scripts/revalidation/android_icnss_cnss_map.py \
  --android-adb \
  --su \
  --v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json \
  --v205-manifest tmp/wifi/v205-icnss-nl80211-readonly/manifest.json \
  --out-dir tmp/wifi/v206-android-icnss-cnss-map
```

Result: PASS.

Decision: `ready-for-native-preflight-plan`.

Evidence:

- `tmp/wifi/v206-android-icnss-cnss-map/manifest.json`
- `tmp/wifi/v206-android-icnss-cnss-map/summary.md`
- `tmp/wifi/v206-android-icnss-cnss-map/android/commands/`

Hashes:

- `tmp/wifi/v206-android-icnss-cnss-map/manifest.json`:
  `2837fe4d2003b3fa25d0a1b590068f9e9cc8b4975d371b084f103fa3ed93ac20`
- `tmp/wifi/v206-android-icnss-cnss-map/summary.md`:
  `1232ca6b2888cb966aaa796fd3178c1ee368af90933f581e57a68c7749c3603c`

Post-collection native restore:

- restored boot image: `stage3/boot_linux_v159.img`
- native boot image SHA256:
  `7e7e81a6af774b3b523c993851d64b86484be4c471dbee02edf062b3903c536f`
- post-restore `cmdv1 version/status`: PASS
- restored runtime: `A90 Linux init 0.9.59 (v159)`

## Decision Model

- `ready-for-native-preflight-plan`
- `android-cnss-map-complete`
- `missing-firmware-map`
- `missing-service-map`
- `native-replay-prereq-missing`
- `manual-review-required`

## Current Result

- `android_ready_from_v204`: `true`
- `native_gap_from_v205`: `true`
- `has_service`: `true`
- `has_firmware`: `true`
- `has_interface`: `true`
- `has_icnss`: `true`
- `has_qmi_or_log`: `true`
- `has_mounts`: `true`
- service evidence: `51`
- init evidence: `48`
- firmware evidence: `14`
- interface evidence: `120`
- ICNSS evidence: `120`
- QMI evidence: `17`
- HAL evidence: `85`
- log evidence: `120`

Important evidence:

```text
[init.svc.cnss-daemon]: [running]
[init.svc.cnss_diag]: [running]
[init.svc.vendor.wifi_hal_ext]: [running]
[init.svc.vendor.wifi_hal_legacy]: [running]
[init.svc.wificond]: [running]
[init.svc.wpa_supplicant]: [running]
/vendor/etc/init/hw/init.qcom.rc:service cnss-daemon /system/vendor/bin/cnss-daemon -n -l
/vendor/etc/init/android.hardware.wifi@1.0-service.rc:service vendor.wifi_hal_legacy /vendor/bin/hw/android.hardware.wifi@1.0-service
/system/etc/init/wificond.rc:service wificond /system/bin/wificond
/vendor/firmware/wlan/qca_cld/bdwlan.bin
/vendor/firmware/wlan/qca_cld/regdb.bin
/vendor/firmware/wlanmdsp.mbn
/sys/devices/platform/soc/18800000.qcom,icnss/net/wlan0
/sys/devices/platform/soc/18800000.qcom,icnss/ieee80211/phy0
```

Interpretation:

- Android needs a running CNSS/ICNSS service chain, Wi-Fi HAL services,
  `wificond`, supplicant service state, vendor firmware paths, QMI/QRTR-adjacent
  readiness, and ICNSS-backed netdev/wiphy state.
- Native v205 currently has only the ICNSS platform node and lacks the Android
  userspace/service chain that creates WLAN netdev and wiphy state.
- The next step should be a native read-only preflight plan that prepares and
  checks prerequisites without enabling Wi-Fi or starting active connectivity.

## Next

Plan v207 as a native read-only Wi-Fi preflight. It should check mount/device
visibility and service prerequisites only. Active Wi-Fi bring-up remains blocked.
