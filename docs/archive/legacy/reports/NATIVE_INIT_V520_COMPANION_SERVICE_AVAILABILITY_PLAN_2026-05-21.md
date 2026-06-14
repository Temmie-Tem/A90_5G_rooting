# Native Init V520 Companion-Service Availability Plan

## Summary

- target: host-only companion-service availability proof after V519
- runner: `scripts/revalidation/native_wifi_companion_service_availability_v520.py`
- lifecycle collector update: `scripts/revalidation/wifi_icnss_lifecycle_collect.py`
- decision: `v520-companion-android-recapture-needed`
- pass: `true`
- device commands: not executed
- daemon start: not executed
- Wi-Fi bring-up: not executed

V520 converts the V519 companion-service hypothesis into an execution plan. The
important result is not “start more daemons now.” The current Android evidence
already proves the QRTR/QMI/service-notifier/WLAN-PD/BDF/FW-ready sequence, but
the old process and binary captures were too narrow to identify the exact
startable companion services and paths.

## Evidence

Evidence root:

```text
tmp/wifi/v520-companion-service-availability-plan/
```

Key result:

```text
decision: v520-companion-android-recapture-needed
pass: True
reason: Android dmesg proves QRTR/QMI/service-notifier/WLAN-PD sequence, but current process/binary captures do not identify the exact companion services or startable paths
next: boot Android and run widened companion-service recapture; then export or build the proven service set
device_commands_executed: False
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

## Findings

| item | result |
| --- | --- |
| V519 prerequisite | `v519-qrtr-companion-service-gap-classified`, pass |
| Android QRTR/QMI sequence | `qrtr_ns=True`, `sysmon=True`, `service_notifier=True`, `wlan_pd=True`, `qmi=True`, `bdf=True`, `fw=True` |
| Android process coverage | incomplete for `sysmon-qmi`, `service-notifier`, `qmiproxy`, `rmtfs`, `pd-mapper`, `tqftpserv` |
| local startable candidates | no local `qrtr-ns`, `qmiproxy`, `rmtfs`, `pd-mapper`, or `tqftpserv` |
| CNSS local binaries | `cnss-daemon` and `cnss_diag` present in extracted roots |
| QRTR baseline | V250 local bind pass, V270 nameservice readback timeout, V276 static platform surface visible |
| `qcwlanstate` | still blocked until native WLFW/QMI/BDF appears |

Interpretation:

- The current extracted roots do not provide a directly startable companion set.
- Android may use vendor equivalents rather than the mainline service names.
- The next Android boot should capture all companion processes, init rc entries,
  properties, binaries, and dmesg lines with widened filters.
- After that capture, choose one of two paths:
  1. export and start Android-proven vendor equivalents in a bounded no-scan
     proof;
  2. build/deploy static `rmtfs`, `pd-mapper`, and `tqftpserv` candidates if
     Android does not expose equivalent startable vendor binaries.

## Collector Change

`scripts/revalidation/wifi_icnss_lifecycle_collect.py` now includes these
additional terms in Android-side property/process/init/dmesg/logcat filters:

- `qrtr`
- `qmiproxy`
- `sysmon`
- `service-notifier`
- `wlan_pd`
- `rmtfs`
- `pd-mapper`
- `tqftp`
- `perfd`
- `servicemanager`

This makes the next Android lifecycle capture useful for V520 instead of
requiring ad hoc command edits.

## Android Recapture Commands

V520 emits a command contract in
`tmp/wifi/v520-companion-service-availability-plan/manifest.json`. The minimum
Android recapture set is:

```bash
adb shell su -c 'ps -AZ 2>/dev/null | grep -Ei "qrtr|qmi|qmiproxy|sysmon|service-notifier|rmtfs|pd-mapper|tqftp|cnss|wlan|wifi|servicemanager|perfd" || true'

adb shell su -c 'getprop | grep -Ei "init\\.svc\\..*(qrtr|qmi|qmiproxy|sysmon|service|rmtfs|pd|tqftp|cnss|wifi|wlan)|ro\\.boottime\\..*(qrtr|qmi|qmiproxy|sysmon|service|rmtfs|pd|tqftp|cnss|wifi|wlan)|qrtr|qmi|qmiproxy|sysmon|service-notifier|rmtfs|pd-mapper|tqftp|wlan_pd|firmware" || true'

adb shell su -c 'grep -RHiE "service .*(qrtr|qmi|qmiproxy|sysmon|service-notifier|rmtfs|pd-mapper|tqftp|cnss|wifi|wlan)|on property:.*(qrtr|qmi|qmiproxy|sysmon|rmtfs|pd-mapper|tqftp|cnss|wifi|wlan)|wlan_pd|pdr" /system/etc/init /system_ext/etc/init /vendor/etc/init /odm/etc/init /product/etc/init 2>/dev/null || true'

adb shell su -c 'find /system /system_ext /vendor /odm /product -type f \( -name qrtr-ns -o -name qmiproxy -o -name sysmon-qmi -o -name service-notifier -o -name rmtfs -o -name pd-mapper -o -name tqftpserv -o -name cnss-daemon -o -name cnss_diag \) 2>/dev/null | sort || true'

adb shell su -c 'dmesg 2>/dev/null | grep -Ei "qrtr|qmi|qmiproxy|sysmon|service-notifier|wlan_pd|rmtfs|pd-mapper|tqftp|cnss|icnss|bdf|bdwlan|regdb|firmware" | tail -n 1000 || true'
```

## Validation

Commands run:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_companion_service_availability_v520.py \
  scripts/revalidation/wifi_icnss_lifecycle_collect.py

python3 scripts/revalidation/native_wifi_companion_service_availability_v520.py plan
python3 scripts/revalidation/native_wifi_companion_service_availability_v520.py run
```

No device command was executed by V520.

## Next Gate

Recommended V521:

1. boot Android or use the next Android handoff window;
2. run the widened lifecycle collector or the V520 emitted command contract;
3. export any proven `qrtr-ns`, `qmiproxy`, `sysmon-qmi`, `service-notifier`,
   `rmtfs`, `pd-mapper`, or `tqftpserv` binaries and init metadata;
4. only then design a bounded native companion start-only proof;
5. continue blocking `qcwlanstate`, scan/connect, DHCP, routing, and external
   ping until native WLFW/QMI/BDF or `wlan0` evidence exists.
