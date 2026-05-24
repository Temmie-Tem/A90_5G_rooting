# Native Init V785 Android/Native Memshare Delta Report

## Result

- decision: `v785-memshare-common-nonfatal-sibling-sysmon-gap`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py`
- evidence: `tmp/wifi/v785-android-native-memshare-delta/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py
python3 scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py plan
python3 scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py run
```

V785 was host-only.  It did not execute any device command.

## Memshare Comparison

| Signal | Android V611 | Native V782 |
| --- | --- | --- |
| request sizes | `100663296`, `33554432` | `100663296`, `33554432` |
| failed sizes | `100663296`, `33554432` | `100663296`, `33554432` |
| CMA failure | `8192` pages, `-12`, `33554432` bytes | `8192` pages, `-12`, `33554432` bytes |
| request sum | `134217728` bytes | `134217728` bytes |
| downstream success | yes | no |

## Chain Comparison

| Marker | Android V611 | Native V782 |
| --- | --- | --- |
| QRTR RX/TX | present | present |
| memshare request/fail | present | present |
| CMA fail | present | present |
| sibling sysmon `slpi/adsp/cdsp` | present | absent |
| modem sysmon | present | present |
| service-locator | present | present |
| service-notifier `180/74` | present | absent |
| WLAN-PD | present | absent |
| ICNSS-QMI | present | absent |
| BDF `regdb.bin`/`bdwlan.bin` | present | absent |
| WLAN FW ready | present | absent |
| `wlan0` | present | absent |

## Timing

| Delta | Android V611 | Native V782 |
| --- | --- | --- |
| memshare fail to modem sysmon | `4.560ms` | `-0.308ms` |
| modem sysmon to service-locator | `38.830ms` | `723.531ms` |
| modem sysmon to service-notifier `180` | `53.927ms` | absent |
| modem sysmon to service-notifier `74` | `55.393ms` | absent |
| modem sysmon to WLAN-PD | `2373.363ms` | absent |
| modem sysmon to ICNSS-QMI | `2375.767ms` | absent |
| modem sysmon to WLAN FW ready | `7646.908ms` | absent |
| modem sysmon to `wlan0` | `7847.430ms` | absent |

## Interpretation

V785 demotes memshare/CMA failure as the sole blocker.  Android and native both
show the same memshare request sizes, failed sizes, and CMA `-12` failure.
Android still proceeds to sibling sysmon, service-notifier `180/74`, WLAN-PD,
ICNSS-QMI, BDF, firmware-ready, and `wlan0`.

The first Android/native divergence is now `sysmon_slpi`: Android has sibling
sysmon for `slpi/adsp/cdsp`, while native V782 has none.  Native also keeps
`mdm3=OFFLINING` while Android has `mdm3=ONLINE`.

The next target is therefore not another memshare-only probe, `boot_wlan`
retry, or daemon-ordering retry.  The next target is the mdm3/esoc0 and sibling
sysmon/service-notifier prerequisite chain.

## Safety

- device command: not executed
- boot image or partition write: not executed
- reboot: not executed
- Wi-Fi HAL/service-manager: not executed
- scan/connect/credential use: not executed
- DHCP/routes/external ping: not executed
- `boot_wlan` or `qcwlanstate ON`: not executed
- module load/unload, bind/unbind, `esoc0`: not executed

## Next

V786 should focus on native sibling sysmon/service-notifier prerequisites and
the mdm3/esoc0 `ONLINE` transition.  It should not repeat memshare-only probes
or blind `boot_wlan`/`qcwlanstate` attempts.
