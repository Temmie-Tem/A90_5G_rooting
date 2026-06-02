# V1753 Android-good WLAN-PD Firmware-request Handoff

- generated: `2026-06-02T19:21:36.134217+00:00`
- command: `run`
- decision: `v1753-android-good-firmware-request-observed-rollback-pass`
- pass: `True`
- reason: Android-good boot produced visible WLAN-PD firmware-request evidence and native rollback completed
- evidence: `/home/temmie/dev/A90_5G_rooting/tmp/wifi/v1753-android-good-wlan-pd-firmware-request`

## Firmware-request Analysis

| field | value |
| --- | --- |
| requested_wlanmdsp | 1 |
| requested_pd_image | 1 |
| request_summary | {"cnss_trace_lines": "18", "requested_pd_image": "1", "requested_wlanmdsp": "1", "rmt_storage_trace_lines": "126", "tftp_trace_lines": "890", "wlan0_seen": "0", "wlfw_seen": "1"} |
| trace_lines | {"cnss_daemon": 18, "rmt_storage": 126, "tftp_server": 890} |
| served_path_candidates | ["/data/local/tmp/a90-v1753-wlan-pd-fwreq/tftp_server.strace.txt", "/data/local/tmp/a90-v1753-wlan-pd-fwreq/rmt_storage.strace.txt"] |
| wlfw/bdf/wlan0 lines | 26/6/7 |
| files | {"cnss_trace": true, "dmesg": true, "done": false, "props": true, "request_summary": true, "rmt_storage_trace": true, "samples": true, "status": true, "tftp_trace": true} |

## Steps

| step | status | rc | duration | file |
| --- | --- | --- | --- | --- |
| prepare-v1753-magisk-module | ok | 0 | 0.001s | steps/prepare-v1753-magisk-module.txt |
| native-version | ok | 0 | 0.437s | steps/native-version.txt |
| native-status | ok | 0 | 0.476s | steps/native-status.txt |
| hide-menu | ok | 0 | 0.003s | steps/hide-menu.txt |
| native-recovery | ok | 0 | 0.101s | steps/native-recovery.txt |
| wait-recovery | ok | 0 | 28.136s | steps/wait-recovery.txt |
| push-android-boot | ok | 0 | 0.659s | steps/push-android-boot.txt |
| remote-android-sha | ok | 0 | 0.108s | steps/remote-android-sha.txt |
| flash-android-boot | ok | 0 | 0.453s | steps/flash-android-boot.txt |
| readback-android-boot | ok | 0 | 0.348s | steps/readback-android-boot.txt |
| reboot-android | ok | 0 | 0.651s | steps/reboot-android.txt |
| wait-android | ok | 0 | 32.159s | steps/wait-android.txt |
| wait-android-boot-complete-for-install | ok | 0 | 2.377s | steps/wait-android-boot-complete-for-install.txt |
| wait-android-ready-for-module-push | ok | 0 | 2.009s | steps/wait-android-ready-for-module-push.txt |
| push-v1753-module-prop-android | ok | 0 | 0.041s | steps/push-v1753-module-prop-android.txt |
| push-v1753-post-fs-data-android | ok | 0 | 0.012s | steps/push-v1753-post-fs-data-android.txt |
| push-v1753-sepolicy-android | ok | 0 | 0.013s | steps/push-v1753-sepolicy-android.txt |
| push-v1753-strace-android | ok | 0 | 0.036s | steps/push-v1753-strace-android.txt |
| install-v1753-module-android-su | ok | 0 | 0.599s | steps/install-v1753-module-android-su.txt |
| reboot-android-with-v1521-module | ok | 0 | 4.024s | steps/reboot-android-with-v1521-module.txt |
| wait-android-second | ok | 0 | 55.250s | steps/wait-android-second.txt |
| wait-v1521-sampler-done | fail | 1 | 171.748s | steps/wait-v1521-sampler-done.txt |
| capture-android-dmesg-filtered | ok | 0 | 0.366s | steps/capture-android-dmesg-filtered.txt |
| pull-v1521-sampler-evidence | ok | 0 | 0.121s | steps/pull-v1521-sampler-evidence.txt |
| cleanup-v1521-module-android | ok | 0 | 0.123s | steps/cleanup-v1521-module-android.txt |
| reboot-recovery-for-rollback | ok | 0 | 4.212s | steps/reboot-recovery-for-rollback.txt |
| wait-rollback-recovery | ok | 0 | 37.189s | steps/wait-rollback-recovery.txt |
| cleanup-v1521-module-recovery-best-effort | ok | 0 | 0.096s | steps/cleanup-v1521-module-recovery-best-effort.txt |
| restore-native | ok | 0 | 35.390s | steps/restore-native.txt |

## Safety

Bounded Android handoff with a temporary Magisk module and native rollback. The module writes only to `/data/local/tmp/a90-v1753-wlan-pd-fwreq`; cleanup removes that path and `/data/adb/modules/a90_v1753_fwreq` before restoring native v724. No Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify, global PCI rescan, platform bind/unbind, or partition write beyond the declared boot image handoff/rollback is performed.

## Next

- If this pass captures Android-good firmware-request evidence, diff it against the V1736 service-manager native route.
- Stop after the diff label; do not autonomously patch served paths or trigger restart-PD.
