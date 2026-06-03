# V1986 Android RIL/QMI Producer Pidof Fast-attach Handoff

## Summary

- Cycle: `V1986`
- Decision: `v1986-reject-degraded-or-pre-wlan0-pcie-mhi`
- Label: `reject-degraded-or-pre-wlan0-pcie-mhi`
- Pass: `False`
- Reason: capture rejected because it was degraded or included pre-wlan0 PCIe/MHI contamination
- Evidence: `tmp/wifi/v1986-android-ril-qmi-producer-pidof-fastattach-live`
- Native rollback selftest fail=0: `True`
- Base handoff: `v1521-magisk-postfs-pre-lower-window-rollback-pass` / `True`

## Producer Window

| field | value |
| --- | --- |
| wlan_pd UP | 44.619278 |
| wlan0 | 50.327863 |
| attach times | {"cnss_daemon": 45.68, "pm_service": 45.55, "rild": 45.63} |
| required strace before wlan_pd | False |
| pre-wlan0 PCIe/MHI | 10 |
| degraded 257s-like | False |
| wlanmdsp logcat lines | 10 |
| base normal window | False |
| base producer-window strace | False |

## Strace And QRTR

| field | value |
| --- | --- |
| strace rild | {"lines": 390, "present": true, "qipcrtr_lines": 248, "recv_lines": 281, "send_lines": 106} |
| strace cnss-daemon | {"lines": 46, "present": true, "qipcrtr_lines": 7, "recv_lines": 37, "send_lines": 5} |
| strace pm-service | {"lines": 210, "present": true, "qipcrtr_lines": 130, "recv_lines": 210, "send_lines": 0} |
| QRTR targeted events | {"dms": 1, "nas": 1, "wds": 1, "wildcard": 64} |
| QRTR file count | 5 |

## Offline QMI Decode

| field | value |
| --- | --- |
| decoded messages | 385 |
| decoded RIL messages | 248 |
| RIL DMS msg IDs | ["0x0001", "0x0020", "0x0025", "0x005f"] |
| RIL NAS msg IDs | ["0x0002", "0x0003", "0x0031", "0x0034", "0x0039", "0x0041", "0x0043", "0x004d", "0x004e", "0x004f", "0x0050", "0x0051", "0x0053", "0x005c", "0x0070", "0x007d", "0x0090", "0x00ac", "0x00d4", "0x010c"] |
| RIL WDS msg IDs | [] |
| RIL DMS+NAS present | True |
| producer-window decoded lead count | 0 |
| decode error | None |

## Scope

- Internal-modem producer measurement only; no external SDX50M/eSoC/PCIe/GDSC path is touched.
- V1986 changes only attach mechanics: `pidof`/`comm` lookup first and `strace` launch before process snapshots.
- The live additions remain strace on `rild`, `cnss-daemon`, `pm-service`, unfiltered dmesg/logcat capture, and QRTR nameservice lookup/readback.

## Interpretation

- The attach optimization improved launch time versus V1985 (`rild` 48.46s -> 45.63s), but still landed after `wlan_pd` UP at 44.619278s.
- The capture again decoded RIL DMS/NAS traffic and enumerated WDS/DMS/NAS, but the run is not a valid normal producer-window trace because pre-`wlan0` PCIe/MHI contamination started at 43.851645s.
- Repeating direct pre-`wlan0` ptrace/strace is now low value: it both misses the sub-second producer edge and perturbs the clean Android-good path. The next producer observer should avoid ptrace in the pre-`wlan_pd` window.

## Safety

Rollbackable Android-handoff to native v724 only. No QMI payload replay, Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC/regulator write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, sda29 remount-write, or partition write beyond the declared boot-image handoff/rollback.

## Steps

| step | status | rc | duration | file |
| --- | --- | --- | --- | --- |
| prepare-v1970-magisk-module | ok | 0 | 0.001s | steps/prepare-v1970-magisk-module.txt |
| native-version | ok | 0 | 0.436s | steps/native-version.txt |
| native-status | ok | 0 | 0.468s | steps/native-status.txt |
| hide-menu | ok | 0 | 0.002s | steps/hide-menu.txt |
| native-recovery | ok | 0 | 0.101s | steps/native-recovery.txt |
| wait-recovery | ok | 0 | 27.138s | steps/wait-recovery.txt |
| push-android-boot | ok | 0 | 0.665s | steps/push-android-boot.txt |
| remote-android-sha | ok | 0 | 0.109s | steps/remote-android-sha.txt |
| flash-android-boot | ok | 0 | 0.477s | steps/flash-android-boot.txt |
| readback-android-boot | ok | 0 | 0.359s | steps/readback-android-boot.txt |
| reboot-android | ok | 0 | 1.031s | steps/reboot-android.txt |
| wait-android | ok | 0 | 33.161s | steps/wait-android.txt |
| wait-android-boot-complete-for-install | ok | 0 | 1.488s | steps/wait-android-boot-complete-for-install.txt |
| wait-android-ready-for-module-push | ok | 0 | 2.013s | steps/wait-android-ready-for-module-push.txt |
| push-v1970-module-prop-android | ok | 0 | 0.034s | steps/push-v1970-module-prop-android.txt |
| push-v1970-post-fs-data-android | ok | 0 | 0.011s | steps/push-v1970-post-fs-data-android.txt |
| push-v1970-sepolicy-android | ok | 0 | 0.016s | steps/push-v1970-sepolicy-android.txt |
| push-v1970-strace-android | ok | 0 | 0.045s | steps/push-v1970-strace-android.txt |
| push-v1970-qrtr-ns-probe-android | ok | 0 | 0.024s | steps/push-v1970-qrtr-ns-probe-android.txt |
| install-v1970-module-android-su | ok | 0 | 0.473s | steps/install-v1970-module-android-su.txt |
| reboot-android-with-v1521-module | ok | 0 | 2.821s | steps/reboot-android-with-v1521-module.txt |
| wait-android-second | ok | 0 | 72.347s | steps/wait-android-second.txt |
| wait-v1521-sampler-done | ok | 0 | 69.320s | steps/wait-v1521-sampler-done.txt |
| capture-android-dmesg-filtered | ok | 0 | 0.369s | steps/capture-android-dmesg-filtered.txt |
| pull-v1521-sampler-evidence | ok | 0 | 0.288s | steps/pull-v1521-sampler-evidence.txt |
| cleanup-v1521-module-android | ok | 0 | 0.107s | steps/cleanup-v1521-module-android.txt |
| reboot-recovery-for-rollback | ok | 0 | 3.200s | steps/reboot-recovery-for-rollback.txt |
| wait-rollback-recovery | ok | 0 | 18.097s | steps/wait-rollback-recovery.txt |
| cleanup-v1521-module-recovery-best-effort | ok | 0 | 0.095s | steps/cleanup-v1521-module-recovery-best-effort.txt |
| restore-native | ok | 0 | 23.489s | steps/restore-native.txt |
| post-rollback-native-selftest | ok | 0 | 0.446s | steps/post-rollback-native-selftest.txt |
