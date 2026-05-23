# Native Init V703 Android-vs-Native Binding Compare Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- classifier: `scripts/revalidation/native_wifi_android_native_binding_compare_v703.py`
- evidence: `tmp/wifi/v703-android-native-binding-compare/`
- decision: `v703-android-icnss-wlfw-delta-classified`

## Scope

V703 consumed existing Android baseline and V702 native focus evidence only. It
did not contact the device, mount filesystems, start daemons or service
managers, start Wi-Fi HAL, scan/connect, use credentials, run DHCP, change
routes, ping externally, write sysfs/debugfs, or write boot images/partitions.

## Result

| check | result |
| --- | --- |
| V702 native input readiness | pass |
| Android ICNSS netdev reference | finding |
| Android WLFW/BDF/fw-ready reference | finding |
| native `icnss` bound and `qca6390` visible | finding |
| native ICNSS-QMI/WLFW/BDF/`wlan0` missing | finding |
| `qca6390` driver-link as next target | rejected |

## Key Evidence

Android reference from `v204` shows successful WLAN surfaces under the ICNSS
parent path:

```text
/sys/devices/platform/soc/18800000.qcom,icnss/net/wlan0
/sys/devices/platform/soc/18800000.qcom,icnss/net/swlan0
/sys/devices/platform/soc/18800000.qcom,icnss/net/p2p0
/sys/devices/platform/soc/18800000.qcom,icnss/net/wifi-aware0
/sys/devices/platform/soc/18800000.qcom,icnss/ieee80211/phy0
```

Android dmesg also contains the progression native is missing:

```text
cnss-daemon wlfw_start: Starting
icnss_qmi: QMI Server Connected
BDF file : regdb.bin
BDF file : bdwlan.bin
icnss: WLAN FW is ready
```

V702 native focus evidence remains below that edge:

```text
icnss_driver_bound=True
qca6390_device_visible=True
qca6390_driver_symlink_visible=False
net_class_has_wlan0=False
wlfw_marker=0
bdf_marker=0
wlan0_marker=0
dmesg_has_icnss_qmi=False
```

## Interpretation

V703 changes the next target. The evidence does not justify writing
`bind`/`unbind` against the `qca6390` child node. Android's working reference
shows WLAN netdevs under the already-bound ICNSS parent and reaches ICNSS-QMI,
WLFW, BDF, and firmware-ready markers before `wlan0` is usable.

The remaining native blocker is therefore the ICNSS QMI/WLFW readiness edge:

```text
native service-notifier 180/74 positive
  -> ICNSS-QMI/WLFW readiness does not start
  -> no BDF download
  -> no firmware-ready event
  -> no wlan0
```

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_native_binding_compare_v703.py

python3 scripts/revalidation/native_wifi_android_native_binding_compare_v703.py \
  --out-dir tmp/wifi/v703-android-native-binding-compare-plan-check plan

python3 scripts/revalidation/native_wifi_android_native_binding_compare_v703.py \
  --out-dir tmp/wifi/v703-android-native-binding-compare run
```

Results:

```text
v703-android-native-binding-compare-plan-ready
v703-android-icnss-wlfw-delta-classified
```

## Next Gate

Plan V704 around ICNSS QMI/WLFW readiness progression:

- keep `qca6390` bind/unbind and `driver_override` writes blocked;
- keep Wi-Fi HAL connect, scan/connect, credentials, DHCP, routing, and
  external ping blocked until `wlan0` exists;
- target a bounded live observer/trigger for the missing ICNSS-QMI/WLFW edge;
- capture cleanup evidence and stop before real Wi-Fi connection attempts.
