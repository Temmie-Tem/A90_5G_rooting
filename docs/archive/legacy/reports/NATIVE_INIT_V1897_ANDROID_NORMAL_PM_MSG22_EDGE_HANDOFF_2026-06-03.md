# V1897 Android Normal pm-service Msg22 Edge Handoff

- generated: `2026-06-03T10:40:28.275977+00:00`
- command: `run`
- decision: `v1897-android-stateup-msg22-uprobe-observability-gap-rollback-pass`
- label: `android-stateup-msg22-uprobe-observability-gap`
- pass: `True`
- reason: normal Android state-up was captured and uprobe fallback ran or was checked, but msg22/pending-client remained unobserved
- evidence: `/home/temmie/dev/A90_5G_rooting/tmp/wifi/v1897-android-normal-pm-msg22-edge-handoff-live3-20260603-193411`

## Android Trigger Window

| field | value |
| --- | --- |
| android_dir | tmp/wifi/v1897-android-normal-pm-msg22-edge-handoff-live3-20260603-193411/android-postfs-evidence/a90-v1897-pm-edge |
| PM vote/WLFW request/wlan_pd/wlanmdsp/wlan0 | 2/3/2/20/14.881999 |
| contamination pcie-mhi/esoc/degraded257 | 0/0/False |
| pm_msg22/pending-client/restart-ind | 0/0/0 |
| first msg22 |  |
| first pending-client |  |
| request_summary | {"cnss_trace_lines": "283", "pending_qmi_client_seen": "0", "pm_msg22_seen": "0", "requested_pd_image": "1", "requested_wlanmdsp": "1", "rmt_storage_trace_lines": "15", "tftp_trace_lines": "60", "uprobe_trace_lines": "0", "wlan0_seen": "0", "wlfw_seen": "1"} |
| trace_lines | {"cnss_daemon": 283, "pm_service_uprobe": 0, "rmt_storage": 15, "tftp_server": 60} |
| uprobe_summary | {"armed": "1", "event.pm_msg22_dispatch_entry.enable": "ok", "event.pm_msg22_dispatch_entry.register": "ok line=p:a90pm1897/pm_msg22_dispatch_entry /vendor/bin/pm-service:0x716c msg_id=%x2 client=%x1 req=%x3 mgr=%x4", "event.pm_msg22_dispatch_ssid.enable": "ok", "event.pm_msg22_dispatch_ssid.register": "ok line=p:a90pm1897/pm_msg22_dispatch_ssid /vendor/bin/pm-service:0x71ac msg_id=%x19 req_ssid=%x22", "event.pm_msg22_pending_helper_call.enable": "ok", "event.pm_msg22_pending_helper_call.register": "ok line=p:a90pm1897/pm_msg22_pending_helper_call /vendor/bin/pm-service:0x72c0 pending_client=%x17 req=%x21 mgr=%x15", "event.pm_msg22_send_resp.enable": "ok", "event.pm_msg22_send_resp.register": "ok line=p:a90pm1897/pm_msg22_send_resp /vendor/bin/pm-service:0x725c msg_id=%x1 resp=%x2 client=%x0", "hit_count": "0", "msg22_hit_count": "0", "pm_service": "/vendor/bin/pm-service", "result": "uprobe_attempted_after_zero_log_msg22", "tracefs": "/sys/kernel/tracing"} |

## Parser Chain

| parser | decision | label | pass | out_dir |
| --- | --- | --- | --- | --- |
| V1894 | v1894-android-stateup-pending-client-observability-gap-host-pass | android-stateup-pending-client-observability-gap | True | tmp/wifi/v1897-android-normal-pm-msg22-edge-handoff-live3-20260603-193411/v1894-parser |
| V1888 | v1888-android-stateup-msg22-observability-gap-host-pass | android-stateup-without-msg22-log-observability-gap | True | tmp/wifi/v1897-android-normal-pm-msg22-edge-handoff-live3-20260603-193411/v1888-parser |

## Rollback Gate

- native rollback selftest fail=0: `True`
- base handoff decision/pass: `v1521-magisk-postfs-partial-android-lower-no-pre-window-rollback-pass` / `True`

## Steps

| step | status | rc | duration | file |
| --- | --- | --- | --- | --- |
| prepare-v1897-magisk-module | ok | 0 | 0.001s | steps/prepare-v1897-magisk-module.txt |
| native-version-redacted | ok | 0 | 0.502s | steps/native-version-redacted.txt |
| native-status-redacted | ok | 0 | 0.542s | steps/native-status-redacted.txt |
| hide-menu | ok | 0 | 0.002s | steps/hide-menu.txt |
| native-recovery | ok | 0 | 0.103s | steps/native-recovery.txt |
| wait-recovery | ok | 0 | 27.126s | steps/wait-recovery.txt |
| push-android-boot | ok | 0 | 0.663s | steps/push-android-boot.txt |
| remote-android-sha | ok | 0 | 0.108s | steps/remote-android-sha.txt |
| flash-android-boot | ok | 0 | 0.474s | steps/flash-android-boot.txt |
| readback-android-boot | ok | 0 | 0.390s | steps/readback-android-boot.txt |
| reboot-android | ok | 0 | 0.365s | steps/reboot-android.txt |
| wait-android | ok | 0 | 33.156s | steps/wait-android.txt |
| wait-android-boot-complete-for-install | ok | 0 | 1.654s | steps/wait-android-boot-complete-for-install.txt |
| wait-android-ready-for-module-push | ok | 0 | 2.012s | steps/wait-android-ready-for-module-push.txt |
| push-v1897-module-prop-android | ok | 0 | 0.035s | steps/push-v1897-module-prop-android.txt |
| push-v1897-post-fs-data-android | ok | 0 | 0.011s | steps/push-v1897-post-fs-data-android.txt |
| push-v1897-sepolicy-android | ok | 0 | 0.010s | steps/push-v1897-sepolicy-android.txt |
| push-v1897-strace-android | ok | 0 | 0.026s | steps/push-v1897-strace-android.txt |
| install-v1897-module-android-su | ok | 0 | 0.532s | steps/install-v1897-module-android-su.txt |
| reboot-android-with-v1521-module | ok | 0 | 3.979s | steps/reboot-android-with-v1521-module.txt |
| wait-android-second | ok | 0 | 56.258s | steps/wait-android-second.txt |
| wait-v1521-sampler-done | fail | 1 | 172.043s | steps/wait-v1521-sampler-done.txt |
| capture-android-dmesg-filtered | ok | 0 | 0.416s | steps/capture-android-dmesg-filtered.txt |
| pull-v1521-sampler-evidence | ok | 0 | 0.070s | steps/pull-v1521-sampler-evidence.txt |
| cleanup-v1521-module-android | ok | 0 | 0.099s | steps/cleanup-v1521-module-android.txt |
| reboot-recovery-for-rollback | ok | 0 | 4.008s | steps/reboot-recovery-for-rollback.txt |
| wait-rollback-recovery | ok | 0 | 36.171s | steps/wait-rollback-recovery.txt |
| cleanup-v1521-module-recovery-best-effort | ok | 0 | 0.091s | steps/cleanup-v1521-module-recovery-best-effort.txt |
| restore-native | ok | 0 | 35.337s | steps/restore-native.txt |
| post-rollback-native-status-redacted | ok | 0 | 0.532s | steps/post-rollback-native-status-redacted.txt |
| run-v1894-pending-client-parser | ok | 0 | 0.063s | steps/run-v1894-pending-client-parser.txt |
| run-v1888-msgid-diff-parser | ok | 0 | 0.063s | steps/run-v1888-msgid-diff-parser.txt |

## Safety

Rollbackable Android-handoff to native v724 only. Android-side writes are limited to the temporary Magisk module, bounded evidence directory, and bounded tracefs uprobe controls when logcat lacks msg22. No Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC/regulator write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, or partition write beyond declared boot-image handoff/rollback.

## Next

- Use the selected label as the handoff result; do not pivot to SDX50M/pcie1/eSoC/GDSC.
- Do not attempt Wi-Fi connect or ping until native init proves WLFW service 69 and `wlan0` are both present.
