# Native Init V703 Android-vs-Native Binding Compare Plan

- date: `2026-05-24 KST`
- cycle: `v703`
- type: host-only classifier over Android baseline and V702 native evidence

## Goal

V702 proved that native has `icnss` bound and the `qca6390` platform node
visible, but no `qca6390` driver symlink, `wlan0`, ICNSS-QMI, WLFW, BDF, or
firmware-ready progression.

V703 answers the next narrower question:

```text
Is the missing native edge a qca6390 bind problem, or is Android's working path
actually ICNSS/WLFW readiness under the already-bound icnss parent?
```

## Inputs

- `tmp/wifi/v702-cnss2-focus-surface-classifier/manifest.json`
- `tmp/wifi/v204-android-baseline/summary.md`
- `tmp/wifi/v204-android-baseline/root-icnss-sysfs-files.txt`
- `tmp/wifi/v204-android-baseline/root-dmesg-wifi-tail.txt`

## Guardrails

V703 must not:

- contact the device;
- mount or bind mount filesystems;
- start daemons, service managers, Wi-Fi HAL, `wificond`, supplicant, or hostapd;
- scan, connect, link up, use credentials, DHCP, route changes, or external
  ping;
- write `bind`, `unbind`, `driver_override`, sysfs, debugfs, boot images, or
  partitions.

## Implementation

Add `scripts/revalidation/native_wifi_android_native_binding_compare_v703.py`.

The classifier parses:

- Android ICNSS sysfs evidence for `wlan0`, `swlan0`, `p2p0`, `wifi-aware0`,
  `phy0`, and rfkill paths under `18800000.qcom,icnss`;
- Android dmesg evidence for `wlfw_start`, ICNSS-QMI connection, BDF download,
  and firmware-ready markers;
- V702 native focus classification for `icnss` binding, `qca6390` node
  visibility, absent `qca6390` driver symlink, absent `wlan0`, and absent WLFW
  markers.

## Decision Criteria

`v703-android-icnss-wlfw-delta-classified` requires:

- V702 input is ready;
- Android has WLAN netdev evidence under `18800000.qcom,icnss`;
- Android has WLFW/BDF/firmware-ready dmesg progression;
- native has `icnss` bound and `qca6390` visible;
- native still lacks ICNSS-QMI/WLFW/BDF/`wlan0`;
- the evidence is strong enough to avoid `qca6390` bind/unbind writes as the
  next target.

## Validation Plan

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_native_binding_compare_v703.py

python3 scripts/revalidation/native_wifi_android_native_binding_compare_v703.py \
  --out-dir tmp/wifi/v703-android-native-binding-compare-plan-check plan

python3 scripts/revalidation/native_wifi_android_native_binding_compare_v703.py \
  --out-dir tmp/wifi/v703-android-native-binding-compare run
```

## Next Gate

If V703 classifies Android's successful path as ICNSS/WLFW readiness rather
than a child `qca6390` bind delta, the next live unit should target the ICNSS
QMI/WLFW readiness edge. Keep `bind`/`unbind`, Wi-Fi HAL connect, credentials,
DHCP, route changes, and external ping blocked until `wlan0` exists.
