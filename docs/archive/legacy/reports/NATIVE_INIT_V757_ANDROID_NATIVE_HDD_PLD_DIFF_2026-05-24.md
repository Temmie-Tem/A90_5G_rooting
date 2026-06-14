# Native Init V757 Android/Native HDD/PLD Differential Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_android_native_hdd_pld_diff_v757.py`
- plan evidence: `tmp/wifi/v757-android-native-hdd-pld-diff-plan/`
- run evidence: `tmp/wifi/v757-android-native-hdd-pld-diff/`
- decision: `v757-boot-image-log-instrumentation-selected`
- status: `pass`

## Summary

V757 compared existing Android success logs with native lower-window failure
logs. Android proves the complete Wi-Fi lower path, and native proves entry into
the HDD/qcwlanstate boundary, but existing dmesg does not show the pre-QMI
`pld_init` / `hdd_init` / `wlan_hdd_register_driver` boundary.

Key Android timing from existing evidence:

```text
sysmon modem: 6.885148
service 180: 6.915578
service 74: 6.922139
cnss_diag: 7.863255
cnss-daemon: 8.116077
wlfw_start: 8.331328
wlan_pd indication: 9.342940
icnss_qmi: 9.345449
BDF regdb: 9.422615
BDF bdwlan: 9.438520
FW ready: 14.401169
wlan0: 14.615634
```

Native V752 still shows:

```text
wlan_loading: 1
hdd_state_major: 1
qcwlanstate: 30
driver_loaded: 0
icnss_qmi_connected: 0
fw_ready: 0
bdf: 0
wlan0: 0
```

Therefore V758 should not be another live `boot_wlan` retry. V758 should first
classify whether rollback-safe kernel/source/boot-image log instrumentation is
actually feasible for this device and repo.

## Checks

| check | result |
| --- | --- |
| V753 input | pass; `v753-hdd-pld-register-driver-gap-needs-instrumentation` |
| V756 input | pass; `v756-nonftrace-live-observers-exhausted` |
| Android complete reference | pass; QMI, BDF, FW-ready, and `wlan0` present |
| native gap reference | pass; HDD entry and qcwlanstate creation present, success markers absent |
| Android dmesg boundary resolution | review; Android has post-FW HDD markers but no pre-QMI PLD/HDD/register-driver boundary |
| instrumentation need | review; live kernel observers are closed, so feasibility must be classified before patching |

## Safety Result

V757 was host-only. It executed no device command and performed no device
mutation, no mount, no ftrace/dynamic-debug/kprobe write, no `boot_wlan` or
`qcwlanstate` write, no service-manager or Wi-Fi HAL start, no scan/connect, no
credential use, no DHCP/routes, and no external ping.

## Interpretation

The useful new conclusion is negative but actionable: existing logs prove the
gap, not the internal failing call. Android dmesg only becomes HDD-rich after
FW-ready and netdev creation. Native reaches the earlier HDD/qcwlanstate edge
and then stops before QMI/BDF/FW-ready/netdev.

The remaining low-level observability route is therefore not a live tracer and
not existing dmesg. The next step must answer whether we can safely create a
temporary, rollback-ready instrumentation boot image or whether we first need
source acquisition/build feasibility work.

## Evidence

- `tmp/wifi/v757-android-native-hdd-pld-diff/manifest.json`
- `tmp/wifi/v757-android-native-hdd-pld-diff/summary.md`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/android-summaries.json`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/native-summaries.json`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/extract-v649-filtered.txt`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/extract-v649-unfiltered.txt`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/extract-v752-summary.txt`
- `tmp/wifi/v757-android-native-hdd-pld-diff/host/extract-v756-focused-dmesg.txt`

## Source References

- QCACLD `__hdd_module_init`:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c#9341>
- QCACLD `boot_wlan` callback:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c#9406>
- QCACLD driver ops:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_driver_ops.c>
