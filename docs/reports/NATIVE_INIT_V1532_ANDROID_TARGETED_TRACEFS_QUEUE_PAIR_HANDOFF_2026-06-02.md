# V1532 Android Targeted Tracefs Queue Pair Handoff

- generated: `2026-06-01T16:45:36.302256+00:00`
- command: `run`
- decision: `v1532-targeted-tracefs-partial-rollback-pass`
- pass: `True`
- reason: partial targeted Android tracefs queue/execute evidence was pulled and native rollback completed
- base_decision: `v1521-magisk-postfs-partial-pre-lower-window-rollback-pass`
- evidence: `/home/temmie/dev/A90_5G_rooting/tmp/wifi/v1532-android-targeted-tracefs-queue-pair-handoff`

## Analysis

| field | value |
| --- | --- |
| sample_count | 92 |
| sample_first_uptime | 5.83 |
| sample_last_uptime | 140.12 |
| esoc0/wlfw/bdf/fw_ready/wlan0 | 43.66351/43.553074/44.492714/49.391141/49.72519 |
| tracefs_hint | targeted-workqueue-pairing-captured |
| trace_counts | {"esoc_lines": 23, "irq_entry": 0, "irq_exit": 0, "pil_event": 0, "pil_func": 0, "pil_notif": 34, "pm_service_lines": 4, "printk_console": 831, "sched_exec": 239, "total_lines": 34191, "workqueue_activate": 8253, "workqueue_end": 8284, "workqueue_queue": 8253, "workqueue_start": 8286} |
| workqueue_pairing | {"activate_count": 8253, "execute_start_count": 8286, "icnss_execute_count": 1, "icnss_paired_count": 1, "icnss_pairs": [{"execute_line": "<...>-297   [006] ....    40.882441: workqueue_execute_start: work struct 0000000068d40497: function icnss_driver_event_work", "execute_time": 40.882441, "prior_count": 2, "prior_events": [{"event": "workqueue_queue_work", "function": "icnss_driver_event_work", "line": "<...>-933   [007] d..1    40.882429: workqueue_queue_work: work struct=0000000068d40497 function=icnss_driver_event_work workqueue=0000000077ff1494 req_cpu=8 cpu=4294967295", "time": 40.882429, "work": "0000000068d40497"}, {"event": "workqueue_activate_work", "function": null, "line": "<...>-933   [007] d..1    40.882430: workqueue_activate_work: work struct 0000000068d40497", "time": 40.88243, "work": "0000000068d40497"}], "work": "0000000068d40497"}], "queue_count": 8253, "record_count": 33076} |
| files | {"available_events": true, "dmesg": true, "done": false, "formats": true, "host_dmesg": true, "module_dmesg": true, "props": true, "samples": true, "setup": true, "status": true, "targeted_excerpt": false, "trace": true, "trace_pipe": false} |

## Tracefs Excerpts

| signal | value |
| --- | --- |
| first_times | {"irq_entry": null, "pil_notif": 40.868692, "printk_console": 6.240071, "sched_exec": 5.835227, "workqueue_activate": 5.83394, "workqueue_queue": 5.833938, "workqueue_start": 5.833958} |
| available_workqueue_events | ["workqueue:workqueue_queue_work", "workqueue:workqueue_activate_work", "workqueue:workqueue_execute_start", "workqueue:workqueue_execute_end"] |
| pil_excerpt | ["<...>-931   [005] ....    40.868692: pil_notif: event_name=before_send_notif code=2 fw=modem", "<...>-931   [005] ....    40.868702: pil_notif: event_name=after_send_notif code=2 fw=modem", "<...>-931   [005] ....    40.870004: pil_notif: event_name=before_send_notif code=6 fw=modem", "<...>-931   [005] ....    40.870009: pil_notif: event_name=after_send_notif code=6 fw=modem", "<...>-178   [007] ....    41.384793: pil_notif: event_name=before_send_notif code=7 fw=modem", "<...>-178   [007] ....    41.384801: pil_notif: event_name=after_send_notif code=7 fw=modem", "<...>-931   [007] ....    41.384832: pil_notif: event_name=before_send_notif code=3 fw=modem", "<...>-931   [005] ....    41.389387: pil_notif: event_name=after_send_notif code=3 fw=modem", "<...>-86    [006] ....    41.449761: pil_notif: event_name=before_send_notif code=2 fw=adsp", "<...>-86    [006] ....    41.449768: pil_notif: event_name=after_send_notif code=2 fw=adsp", "<...>-545   [006] ....    41.450089: pil_notif: event_name=before_send_notif code=2 fw=cdsp", "<...>-545   [006] ....    41.450094: pil_notif: event_name=after_send_notif code=2 fw=cdsp", "<...>-86    [006] ....    41.450589: pil_notif: event_name=before_send_notif code=6 fw=adsp", "<...>-86    [006] ....    41.450593: pil_notif: event_name=after_send_notif code=6 fw=adsp", "<...>-545   [007] ....    41.450880: pil_notif: event_name=before_send_notif code=6 fw=cdsp", "<...>-545   [007] ....    41.450883: pil_notif: event_name=after_send_notif code=6 fw=cdsp", "<...>-181   [007] ....    41.543012: pil_notif: event_name=before_send_notif code=7 fw=cdsp", "<...>-181   [007] ....    41.543019: pil_notif: event_name=after_send_notif code=7 fw=cdsp", "<...>-545   [004] ....    41.543111: pil_notif: event_name=before_send_notif code=3 fw=cdsp", "<...>-545   [004] ....    41.544924: pil_notif: event_name=after_send_notif code=3 fw=cdsp"] |
| irq_excerpt | [] |
| workqueue_excerpt | ["busybox-695   [004] d..3     5.833938: workqueue_queue_work: work struct=00000000006ce2ea function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "busybox-695   [004] d..3     5.833940: workqueue_activate_work: work struct 00000000006ce2ea", "<...>-297   [006] ....     5.833958: workqueue_execute_start: work struct 00000000006ce2ea: function hook_handler", "<...>-297   [006] ....     5.833961: workqueue_execute_end: work struct 00000000006ce2ea", "busybox-717   [006] d..3     5.834408: workqueue_queue_work: work struct=0000000008e28718 function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "busybox-717   [006] d..3     5.834409: workqueue_activate_work: work struct 0000000008e28718", "<...>-297   [004] ....     5.834426: workqueue_execute_start: work struct 0000000008e28718: function hook_handler", "<...>-297   [004] ....     5.834428: workqueue_execute_end: work struct 0000000008e28718", "<...>-718   [005] d..3     5.834689: workqueue_queue_work: work struct=0000000086f120c6 function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-718   [005] d..3     5.834690: workqueue_activate_work: work struct 0000000086f120c6", "<...>-297   [004] ....     5.834701: workqueue_execute_start: work struct 0000000086f120c6: function hook_handler", "<...>-297   [004] ....     5.834701: workqueue_execute_end: work struct 0000000086f120c6", "<...>-719   [004] d..1     5.834896: workqueue_queue_work: work struct=00000000221e2d0b function=work_handler workqueue=000000005694c0b9 req_cpu=8 cpu=4", "<...>-719   [004] d..1     5.834896: workqueue_activate_work: work struct 00000000221e2d0b", "<...>-344   [004] ....     5.834906: workqueue_execute_start: work struct 00000000221e2d0b: function work_handler", "<...>-344   [004] d..1     5.834908: workqueue_queue_work: work struct=000000002836b79d function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-344   [004] d..1     5.834908: workqueue_activate_work: work struct 000000002836b79d", "<...>-718   [005] d..3     5.834917: workqueue_queue_work: work struct=00000000875c96f7 function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-344   [004] d..1     5.834918: workqueue_queue_work: work struct=000000000413244c function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-344   [004] ....     5.834920: workqueue_execute_end: work struct 00000000221e2d0b", "<...>-297   [006] ....     5.834921: workqueue_execute_start: work struct 000000002836b79d: function hook_handler", "<...>-297   [006] ....     5.834924: workqueue_execute_end: work struct 000000002836b79d", "<...>-297   [006] d..1     5.834924: workqueue_activate_work: work struct 00000000875c96f7", "<...>-297   [006] ....     5.834924: workqueue_execute_start: work struct 00000000875c96f7: function hook_handler", "<...>-297   [006] ....     5.834925: workqueue_execute_end: work struct 00000000875c96f7", "<...>-297   [006] d..1     5.834925: workqueue_activate_work: work struct 000000000413244c", "<...>-297   [006] ....     5.834925: workqueue_execute_start: work struct 000000000413244c: function hook_handler", "<...>-297   [006] ....     5.834926: workqueue_execute_end: work struct 000000000413244c", "<...>-720   [006] d..1     5.835109: workqueue_queue_work: work struct=000000001f2d44db function=work_handler workqueue=000000005694c0b9 req_cpu=8 cpu=6", "<...>-720   [006] d..1     5.835110: workqueue_activate_work: work struct 000000001f2d44db", "<...>-86    [006] ....     5.835120: workqueue_execute_start: work struct 000000001f2d44db: function work_handler", "<...>-86    [006] d..1     5.835121: workqueue_queue_work: work struct=0000000008e28718 function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-86    [006] d..1     5.835121: workqueue_activate_work: work struct 0000000008e28718", "<...>-86    [006] d..1     5.835142: workqueue_queue_work: work struct=00000000d2513d37 function=hook_handler workqueue=00000000d5dca6b0 req_cpu=8 cpu=4294967295", "<...>-86    [006] ....     5.835143: workqueue_execute_end: work struct 000000001f2d44db", "<...>-297   [007] ....     5.835144: workqueue_execute_start: work struct 0000000008e28718: function hook_handler", "<...>-297   [007] ....     5.835146: workqueue_execute_end: work struct 0000000008e28718", "<...>-297   [007] d..1     5.835146: workqueue_activate_work: work struct 00000000d2513d37", "<...>-297   [007] ....     5.835146: workqueue_execute_start: work struct 00000000d2513d37: function hook_handler", "<...>-297   [007] ....     5.835147: workqueue_execute_end: work struct 00000000d2513d37"] |
| targeted_excerpt | [] |
| pm_service_excerpt | ["<...>-972   [004] d..1    41.441930: console: [   41.441924]  [4:         statsd:  972] binder: 972:972 ioctl 40046210 7fdaa00f74 returned -22", "<...>-973   [005] d..1    41.564208: console: [   41.564201]  [5:           netd:  973] binder: 973:973 ioctl 40046210 7fdbc68924 returned -22", "<...>-973   [005] d..1    41.566110: console: [   41.566105]  [5:   Binder:973_4:  973] binder: 973:973 ioctl 40046210 7fdbc68b54 returned -22", "<...>-1028  [004] d..1    41.804482: console: [   41.804477]  [4:android.hidl.al: 1028] binder: 1028:1028 ioctl 40046210 7fe89985e4 returned -22"] |

## Steps

| step | status | rc | duration | file |
| --- | --- | --- | --- | --- |
| prepare-magisk-module | ok | 0 | 0.000s | steps/prepare-magisk-module.txt |
| native-selftest | ok | 0 | 0.436s | steps/native-selftest.txt |
| hide-menu | ok | 0 | 0.002s | steps/hide-menu.txt |
| native-recovery | ok | 0 | 0.101s | steps/native-recovery.txt |
| wait-recovery | ok | 0 | 28.129s | steps/wait-recovery.txt |
| push-android-boot | ok | 0 | 0.670s | steps/push-android-boot.txt |
| remote-android-sha | ok | 0 | 0.104s | steps/remote-android-sha.txt |
| flash-android-boot | ok | 0 | 0.466s | steps/flash-android-boot.txt |
| readback-android-boot | ok | 0 | 0.350s | steps/readback-android-boot.txt |
| reboot-android | ok | 0 | 1.006s | steps/reboot-android.txt |
| wait-android | ok | 0 | 33.141s | steps/wait-android.txt |
| wait-android-boot-complete-for-install | ok | 0 | 0.917s | steps/wait-android-boot-complete-for-install.txt |
| wait-android-ready-for-module-push | ok | 0 | 2.012s | steps/wait-android-ready-for-module-push.txt |
| push-v1521-module-prop-android | ok | 0 | 0.033s | steps/push-v1521-module-prop-android.txt |
| push-v1521-post-fs-data-android | ok | 0 | 0.013s | steps/push-v1521-post-fs-data-android.txt |
| install-v1521-module-android-su | ok | 0 | 0.503s | steps/install-v1521-module-android-su.txt |
| reboot-android-with-v1521-module | ok | 0 | 3.980s | steps/reboot-android-with-v1521-module.txt |
| wait-android-second | ok | 0 | 89.405s | steps/wait-android-second.txt |
| wait-v1521-sampler-done | ok | 0 | 102.896s | steps/wait-v1521-sampler-done.txt |
| capture-android-dmesg-filtered | ok | 0 | 0.367s | steps/capture-android-dmesg-filtered.txt |
| pull-v1521-sampler-evidence | ok | 0 | 0.152s | steps/pull-v1521-sampler-evidence.txt |
| cleanup-v1521-module-android | ok | 0 | 0.127s | steps/cleanup-v1521-module-android.txt |
| reboot-recovery-for-rollback | ok | 0 | 3.994s | steps/reboot-recovery-for-rollback.txt |
| wait-rollback-recovery | ok | 0 | 50.222s | steps/wait-rollback-recovery.txt |
| cleanup-v1521-module-recovery-best-effort | ok | 0 | 0.095s | steps/cleanup-v1521-module-recovery-best-effort.txt |
| restore-native | ok | 0 | 34.703s | steps/restore-native.txt |

## Safety

Bounded Android handoff with temporary Magisk module `a90_v1532_tracefs_queue_pair_sampler` and native rollback. Android-side mutation is limited to tracefs diagnostic controls, `/data/local/tmp/a90-v1532-tracefs-queue-pair-sampler`, and `/data/adb/modules/a90_v1532_tracefs_queue_pair_sampler` cleanup. The event set is bounded to sched exec, workqueue queue/activate/execute, PIL, and printk console signals. No Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC writes, eSoC notify, PCI rescan, platform bind/unbind, or partition writes beyond declared boot handoff/rollback.

## Next

- If ICNSS workqueue queue/execute pairing is captured, classify the queued event timing against pm-service Binder subsystem_get and WLFW start.
- If queue events are absent or unpaired, use the available tracefs format evidence to decide whether a lower-level Android uprobe or source-only classifier is needed; do not broaden IRQ tracing.
