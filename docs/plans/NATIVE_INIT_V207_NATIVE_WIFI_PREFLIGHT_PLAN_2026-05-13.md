# v207 Plan: Native Read-Only Wi-Fi Preflight

## Summary

v207 designs the native-side Wi-Fi preflight that follows the v205/v206
evidence chain.

This is still not active Wi-Fi bring-up. The goal is to verify, from native
init, whether the Android-mapped ICNSS/CNSS/firmware/service prerequisites are
visible enough to justify a later tightly-scoped daemon feasibility step.

Implementation target:

- `scripts/revalidation/native_wifi_preflight.py`
- evidence output: `tmp/wifi/v207-native-wifi-preflight`
- report: `docs/reports/NATIVE_INIT_V207_NATIVE_WIFI_PREFLIGHT_2026-05-13.md`

No native boot image change is planned for v207.

## Baseline

- v203 native Wi-Fi refresh: `no-go`
- v204 Android baseline: `ready-for-readonly-nl80211-probe-plan`
- v205 native ICNSS/nl80211 probe: `native-icnss-present-no-wiphy`
- v206 Android ICNSS/CNSS dependency map: `ready-for-native-preflight-plan`

Current known state:

- Android can expose `wlan0` and `phy0` through the ICNSS-backed Wi-Fi path.
- Native init currently sees `/sys/devices/platform/soc/18800000.qcom,icnss`
  but lacks WLAN netdev, Wi-Fi rfkill, and `ieee80211` wiphy state.
- Android-side mapping shows the relevant service chain:
  `cnss-daemon`, Wi-Fi HAL services, `wificond`, and `wpa_supplicant`.
- Firmware evidence includes `bdwlan.bin`, `regdb.bin`, and `wlanmdsp.mbn`.

## Reference Model

- Android Wi-Fi services use Wi-Fi HAL surfaces, and `wificond` talks to the
  Wi-Fi driver with standard `nl80211` commands:
  <https://source.android.com/docs/core/connect/wifi-overview>
- Android Wi-Fi HAL is split across Vendor, Supplicant, and Hostapd HAL
  surfaces:
  <https://source.android.com/docs/core/connect/wifi-hal>
- Android init service/class/property ordering is driven by rc files and init
  triggers:
  <https://android.googlesource.com/platform/system/core/+/master/init/README.md>
- AOSP `wificond.rc` shows `wifi`, `net_raw`, `net_admin`, `NET_RAW`, and
  `NET_ADMIN` context requirements:
  <https://android.googlesource.com/platform/system/connectivity/wificond/+/master/wificond.rc>
- Linux `nl80211` has read-only discovery operations such as `get-wiphy`,
  `get-interface`, and `get-protocol-features`:
  <https://docs.kernel.org/networking/netlink_spec/nl80211.html>
- Linux firmware lookup uses `/lib/firmware` search paths and the optional
  `firmware_class.path` parameter:
  <https://docs.kernel.org/driver-api/firmware/fw_search_path.html>

## Scope

Add `scripts/revalidation/native_wifi_preflight.py`.

The collector runs through the native serial/broker control path and captures
read-only evidence from:

- native version/status/bootstatus for baseline metadata
- `mountsystem ro` result and mounted-system path visibility
- vendor/system init rc files related to Wi-Fi, CNSS, ICNSS, HAL, supplicant,
  hostapd, and `wificond`
- vendor firmware candidates:
  - `/mnt/system/vendor/firmware/wlan/qca_cld/bdwlan.bin`
  - `/mnt/system/vendor/firmware/wlan/qca_cld/regdb.bin`
  - `/mnt/system/vendor/firmware/wlanmdsp.mbn`
  - related `/mnt/system/vendor/firmware*` and `/mnt/system/vendor/etc/wifi`
    candidates
- ICNSS sysfs:
  - `/sys/devices/platform/soc/18800000.qcom,icnss`
  - child nodes such as `net`, `ieee80211`, `ramdump`, `wakeup`, and
    `iommu_group` if present
- native Wi-Fi kernel surfaces:
  - `/sys/class/net/wlan0`
  - `/sys/class/net/swlan0`
  - `/sys/class/net/p2p0`
  - `/sys/class/net/wifi-aware0`
  - `/sys/class/ieee80211`
  - `/sys/class/rfkill`
  - `/proc/net/wireless`
  - `/proc/modules`
- firmware loader state:
  - `/sys/module/firmware_class/parameters/path`
  - `/proc/sys/kernel/hotplug` if present
- optional local state for the existing GET-only helper:
  - `/cache/bin/a90_nl80211_ro`
  - `stage3/linux_init/helpers/a90_nl80211_ro` build metadata in the host
    manifest
- v205/v206 manifest comparison

Default v207 mode must not deploy or write files to the device. It only records
whether `/cache/bin/a90_nl80211_ro` already exists and can be executed.

An explicit opt-in mode may be designed for later use:

```text
--deploy-readonly-helper
```

That mode is not part of default PASS criteria. If implemented, it must verify
the helper hash, copy only the GET-only static helper, and clearly mark the
evidence as non-default because it mutates `/cache/bin`.

## Guardrails

The collector must not:

- enable Wi-Fi
- write rfkill state
- bring up any WLAN interface
- scan or connect
- send active `nl80211` commands such as trigger scan, set interface, set
  wiphy, connect, or disconnect
- load or unload modules
- write `firmware_class.path`
- mutate firmware files or firmware directories
- start `cnss-daemon`, `cnss_diag`, Wi-Fi HAL, `wificond`, `wpa_supplicant`, or
  `hostapd`
- run Android framework Wi-Fi commands such as `cmd wifi`, `svc wifi`, or
  `dumpsys wifi`
- collect saved network material under `/data/misc/wifi`

Allowed active device commands are limited to safe shell/control commands:

- `version`
- `status`
- `bootstatus`
- `mountsystem ro`
- `ls`, `cat`, `stat`, and read-only `run` helpers
- optional existing `/cache/bin/a90_nl80211_ro` GET-only execution if already
  present

## Decision Model

- `native-preflight-ready`
  - mounted-system firmware/init paths are visible, ICNSS sysfs is visible, and
    read-only kernel surfaces are fully captured. This does not approve Wi-Fi
    bring-up; it only approves the next feasibility plan.
- `userspace-service-gap-confirmed`
  - firmware/init/ICNSS prerequisites are visible but native still lacks
    WLAN netdev/wiphy/rfkill. This points to a missing native userspace daemon
    or service-order dependency.
- `missing-mounted-vendor`
  - `mountsystem ro` failed or mounted vendor/system paths are not visible.
- `missing-firmware-path`
  - Android-mapped firmware files are not visible from native.
- `missing-icnss-sysfs`
  - the ICNSS platform sysfs node is not visible from native.
- `missing-nl80211-helper`
  - no existing `/cache/bin/a90_nl80211_ro` helper is available, so `nl80211`
    GET-only validation could not run.
- `missing-wiphy-netdev`
  - ICNSS and firmware are visible, but no native WLAN netdev/wiphy/rfkill state
    exists.
- `manual-review-required`
  - command failures or incomplete manifests prevent a reliable decision.

## Validation Plan

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_preflight.py \
  scripts/revalidation/wifi_icnss_nl80211_probe.py \
  scripts/revalidation/android_icnss_cnss_map.py \
  scripts/revalidation/a90harness/evidence.py

python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import native_wifi_preflight
native_wifi_preflight.validate_no_active_wifi_commands()
print('v207 command guard PASS')
PY

git diff --check
```

Native device validation:

```bash
python3 scripts/revalidation/a90ctl.py hide || true
python3 scripts/revalidation/a90ctl.py mountsystem ro

python3 scripts/revalidation/native_wifi_preflight.py \
  --native-bridge \
  --v205-manifest tmp/wifi/v205-icnss-nl80211-readonly/manifest.json \
  --v206-manifest tmp/wifi/v206-android-icnss-cnss-map/manifest.json \
  --out-dir tmp/wifi/v207-native-wifi-preflight
```

Expected successful output:

- private/no-follow evidence bundle
- `manifest.json`
- `summary.md`
- one of the defined decisions
- command guard PASS
- no active Wi-Fi command in the command manifest

Optional helper build validation:

```bash
scripts/revalidation/build_nl80211_ro_helper.sh
file stage3/linux_init/helpers/a90_nl80211_ro
sha256sum stage3/linux_init/helpers/a90_nl80211_ro
```

This only validates the host artifact. Device deployment remains opt-in and is
not required for default v207 acceptance.

## Acceptance

- Native mounted-system firmware and init paths are compared against v206
  Android evidence.
- Native ICNSS, WLAN netdev, rfkill, `ieee80211`, firmware loader, and optional
  `nl80211` helper state are captured.
- v205 and v206 manifests are compared.
- A clear next decision is produced without enabling Wi-Fi.
- Default validation does not write to device storage except existing normal
  native-init logging paths.
- Active Wi-Fi bring-up remains blocked.

## Next

If v207 returns `userspace-service-gap-confirmed` or `native-preflight-ready`,
the next work should be a narrow v208 feasibility plan for CNSS/ICNSS userspace
startup requirements. That plan should still avoid scan/connect and should first
map daemon dependencies, sockets, device nodes, firmware expectations, QMI/QRTR
requirements, permissions, and failure behavior.

If v207 returns a missing mount, firmware, or ICNSS decision, fix that native
visibility gap before any daemon feasibility work.
