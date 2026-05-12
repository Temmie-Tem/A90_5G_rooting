# v206 Plan: Android ICNSS/CNSS Dependency Map

## Summary

v206 maps the Android-side ICNSS/CNSS/Wi-Fi dependency chain that exists before
native init can safely attempt any Wi-Fi preparation. The target is a read-only
host-side collector, not a boot image change.

Target decision: determine whether Android evidence is complete enough for a
future native read-only preflight plan.

## Baseline

- v203 native Wi-Fi refresh: `no-go`
- v204 Android baseline: `ready-for-readonly-nl80211-probe-plan`
- v205 native ICNSS/nl80211 probe: `native-icnss-present-no-wiphy`
- Current known gap: Android exposes WLAN interfaces and ICNSS readiness, while
  native init sees ICNSS sysfs only and no WLAN netdev/wiphy/rfkill.

## Reference Model

- Android Wi-Fi architecture routes Framework Wi-Fi service through HAL surfaces
  and `wificond`; `wificond` talks to the driver over standard `nl80211`:
  <https://source.android.com/docs/core/connect/wifi-overview>
- Android Wi-Fi HAL has Vendor, Supplicant, and Hostapd HAL surfaces:
  <https://source.android.com/docs/core/connect/wifi-hal>
- Android init loads rc files from system/vendor/odm/product init directories
  and starts services through class/property/event triggers:
  <https://android.googlesource.com/platform/system/core/+/master/init/README.md>
- AOSP `wificond.rc` shows the expected `wifi`, `net_raw`, `net_admin`,
  `NET_RAW`, and `NET_ADMIN` runtime context:
  <https://android.googlesource.com/platform/system/connectivity/wificond/+/master/wificond.rc>
- Linux `nl80211` separates read operations such as `get-wiphy`,
  `get-interface`, and `get-protocol-features` from active commands such as
  scan/connect/set operations:
  <https://docs.kernel.org/netlink/specs/nl80211.html>
- Linux firmware search includes `/lib/firmware` and optional
  `/sys/module/firmware_class/parameters/path` override:
  <https://www.kernel.org/doc/html/v6.15/driver-api/firmware/fw_search_path.html>

## Scope

Add `scripts/revalidation/android_icnss_cnss_map.py`.

The collector runs against Android ADB with root already available and captures:

- init rc files and service/property trigger references for Wi-Fi/CNSS/ICNSS
- process and `init.svc.*` state for `cnss-daemon`, `wificond`, Wi-Fi HAL,
  supplicant, hostapd, QMI/QRTR-adjacent daemons
- firmware and config candidate paths such as `bdwlan.bin`, `regdb.bin`,
  `wlanmdsp`, `WCNSS`, `/vendor/firmware_mnt`, and `/vendor/etc/wifi`
- sysfs mappings for ICNSS, WLAN netdevs, rfkill, and `ieee80211`
- dmesg/logcat lines around ICNSS/CNSS/WLAN/QMI/firmware readiness
- VINTF HAL declarations and socket/devnode visibility
- v204/v205 manifest comparison

## Guardrails

The collector must not:

- enable Wi-Fi
- write rfkill state
- bring any WLAN interface up
- scan or connect
- load or unload modules
- mutate firmware search path or firmware files
- start `wpa_supplicant`, `hostapd`, `wificond`, or `cnss-daemon`
- collect `/data/misc/wifi`, `dumpsys wifi`, `cmd wifi status`, or saved
  network material by default

## Decision Model

- `ready-for-native-preflight-plan`
  - Android dependency map is complete and v205 confirms native missing gates.
- `android-cnss-map-complete`
  - Android service, firmware, interface, ICNSS, QMI/log, and mount evidence are
    mapped, but comparison inputs are incomplete or not decisive.
- `missing-firmware-map`
  - firmware/regdb/BDF candidates are not mapped.
- `missing-service-map`
  - Android init/service trigger chain is not mapped.
- `native-replay-prereq-missing`
  - Android evidence is partial and native replay prerequisites remain unclear.
- `manual-review-required`
  - ADB capture failed or evidence is insufficient.

## Validation Plan

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/android_icnss_cnss_map.py \
  scripts/revalidation/android_twrp_wifi_baseline.py \
  scripts/revalidation/wifi_icnss_nl80211_probe.py \
  scripts/revalidation/a90harness/evidence.py

python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import android_icnss_cnss_map
android_icnss_cnss_map.validate_no_active_wifi_commands()
print('v206 command guard PASS')
PY

git diff --check
```

Android device validation:

```bash
python3 scripts/revalidation/android_icnss_cnss_map.py \
  --android-adb \
  --su \
  --v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json \
  --v205-manifest tmp/wifi/v205-icnss-nl80211-readonly/manifest.json \
  --out-dir tmp/wifi/v206-android-icnss-cnss-map
```

Expected successful output:

- private/no-follow evidence bundle
- `manifest.json`
- `summary.md`
- one of the defined decisions
- no active Wi-Fi command in command guard

## Acceptance

- Android ICNSS/CNSS dependency map is captured read-only.
- v204 and v205 evidence are compared.
- The result states whether v207 can safely design a native read-only Wi-Fi
  preflight step.
- Active Wi-Fi bring-up remains blocked unless a future plan explicitly approves
  a narrower preflight.

## Next

If v206 returns `ready-for-native-preflight-plan`, v207 should design a native
Wi-Fi preflight that only prepares mounts/device visibility and performs
read-only checks. If v206 returns a missing-map decision, collect the missing
Android side first.
