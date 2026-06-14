# Native Init V650 Post-Warning Continuation Report

- date: `2026-05-23 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_post_warning_continuation_v650.py`
- evidence: `tmp/wifi/v650-post-warning-continuation/`
- decision: `v650-post-warning-wlfw-continuation-gap-classified`

## Scope

V650 is host-only. It compares Android V649 replay evidence with native V644
dmesg. It does not contact the device, write sysfs, start daemons, start Wi-Fi
HAL, run `qcwlanstate`, scan/connect, use credentials, run DHCP, change routes,
reboot, flash, or ping externally.

## Result

```text
decision: v650-post-warning-wlfw-continuation-gap-classified
pass: True
reason: Android and native both continue through sound-card registration after the ASoC warning, but only Android reaches WLFW/WLAN-PD/QMI/BDF/wlan0
next: plan V651 CNSS/WLFW post-warning continuation guard; keep HAL/scan/connect blocked
```

## Key Deltas

| delta | Android ms | Native V644 ms |
| --- | ---: | ---: |
| service `74` → QoS warning | `8.967` | `11.820` |
| QoS warning → sound card | `784.783` | `513.488` |
| QoS warning → WLFW start | `1282.936` | missing |
| QoS warning → WLAN-PD | `2351.543` | missing |

## Continuation Matrix

| marker | Android count | Native V644 count |
| --- | ---: | ---: |
| audio codec registered | `1` | `1` |
| sound card registered | `1` | `1` |
| WLFW start | `1` | `0` |
| WLAN-PD | `2` | `0` |
| QMI server connected | `1` | `0` |
| BDF `regdb.bin` | `1` | `0` |
| BDF `bdwlan.bin` | `1` | `0` |
| WLAN FW ready | `2` | `0` |
| `wlan0` | `6` | `0` |

## Interpretation

The ASoC `pm_qos` warning is shared by Android and native V644. It is not the
first native-only stop condition. Both paths continue far enough to register
the sound card after the warning.

The first meaningful native-only gap is WLFW continuation:

```text
Android: warning -> sound card -> WLFW -> WLAN-PD -> QMI -> BDF -> wlan0
Native:  warning -> sound card -> no WLFW/WLAN-PD/QMI/BDF/wlan0
```

## Next Gate

Proceed to V651 CNSS/WLFW post-warning continuation guard:

1. compare Android `cnss-daemon` state/log/properties around WLFW start with
   native V644 child state;
2. check service-manager/binder/runtime surfaces that may be required after
   service `74`;
3. keep V644 retry, Wi-Fi HAL, `qcwlanstate`, scan/connect, credentials, DHCP,
   route changes, and external ping blocked until the WLFW continuation gap is
   classified.
