# Native Init V1533 V1532 Queue Pair Classifier

- Generated: `2026-06-01T16:50:11.291867+00:00`
- Decision: `v1533-icnss-queue-pair-is-hdd-register-path-not-first-l0-trigger`
- Pass: `True`
- Reason: V1532 pairs icnss_driver_event_work queue/execute to macloader WLAN driver load, before pm-service esoc0 and QMI; this visible ICNSS workqueue signal is not the Android first-L0 trigger

## Checks

| check | value |
| --- | --- |
| v1532_pass | True |
| v1532_rollback_pass | True |
| queue_event_available | True |
| icnss_queue_execute_pair_captured | True |
| queue_function_is_icnss_driver_event_work | True |
| queue_pid_is_macloader | True |
| queue_before_pm_service_esoc0 | True |
| queue_before_qmi_server | True |
| android_lower_progress_present | True |
| v1531_register_event_source_known | True |

## Timeline

| event | timestamp_s |
| --- | --- |
| macloader_exec | 40.872653 |
| wlan_loading | 40.879046 |
| icnss_queue | 40.882429 |
| icnss_activate | 40.88243 |
| icnss_execute | 40.882441 |
| wlan_hdd_state | 40.883722 |
| mac_assign | 41.382969 |
| pm_service_exec | None |
| pm_service_modem_get | 42.998748 |
| mdm_helper_start | 43.411061 |
| wlfw_start | 43.553074 |
| pm_service_esoc0_get | 43.66351 |
| qmi_server_connected | 44.423626 |
| bdf_regdb | 44.492714 |
| fw_ready | 49.391141 |
| wlan0 | 49.72519 |

## Deltas

| delta | ms |
| --- | --- |
| macloader_exec_to_icnss_queue | 9.776 |
| wlan_loading_to_icnss_queue | 3.383 |
| icnss_queue_to_execute | 0.012 |
| icnss_queue_to_mac_assign | 500.54 |
| icnss_queue_to_pm_esoc0_get | 2781.081 |
| icnss_queue_to_qmi | 3541.197 |
| pm_esoc0_get_to_qmi | 760.116 |
| qmi_to_bdf_regdb | 69.088 |
| fw_ready_to_wlan0 | 334.049 |

## Workqueue Pairing

| field | value |
| --- | --- |
| work | 0000000068d40497 |
| queue_time | 40.882429 |
| execute_time | 40.882441 |
| queue_line | <...>-933   [007] d..1    40.882429: workqueue_queue_work: work struct=0000000068d40497 function=icnss_driver_event_work workqueue=0000000077ff1494 req_cpu=8 cpu=4294967295 |
| execute_line | <...>-297   [006] ....    40.882441: workqueue_execute_start: work struct 0000000068d40497: function icnss_driver_event_work |

## Interpretation

- V1532 captured the missing `workqueue_queue_work` event and paired it with the existing `workqueue_execute_start` for the same `icnss_driver_event_work` work item.
- The queueing thread is the `macloader` process immediately after WLAN driver load, and the event executes roughly 0.012 ms later.
- That ICNSS event is more than 2.7 s before pm-service opens `esoc0` and more than 3.5 s before the QMI server connects, so it is not the first-L0 trigger and not WLFW server-arrive evidence.
- This closes the visible ICNSS workqueue signal as a lead for the native no-L0 blocker; the next useful target is pm-service Binder/QMI voter behavior that opens `subsys_esoc0` and the immediate pci-msm first-L0 path.

## Excerpts

### ICNSS Pair Context

- `<...>-933   [006] ....    40.872653: sched_process_exec: filename=/vendor/bin/hw/macloader pid=933 old_pid=933`
- `<...>-933   [007] d..1    40.879046: console: [   40.879042]  [7:      macloader:  933] wlan: Loading driver v5.2.022.3Q-HL210630A +PANIC_ON_BUG; 2023-01-12T09:49:35Z; cld:; cmn:;`
- `<...>-933   [007] d..1    40.882429: workqueue_queue_work: work struct=0000000068d40497 function=icnss_driver_event_work workqueue=0000000077ff1494 req_cpu=8 cpu=4294967295`
- `<...>-297   [006] ....    40.882441: workqueue_execute_start: work struct 0000000068d40497: function icnss_driver_event_work`
- `<...>-580   [005] d..1    40.883722: console: [   40.882419]  [5:   logd.control:  580] wlan_hdd_state wlan major(478) initialized`

### PM Service Context

- `[   42.998748]  [4:  Binder:1144_2: 1178] subsys-restart: __subsystem_get(): __subsystem_get: modem count:1`
- `[   43.411061]  [4:           init:    1] init: starting service 'vendor.mdm_helper'...`
- `[   43.417324]  [3:           init:    1] init: Control message: Processed ctl.start for 'vendor.mdm_helper' from pid: 1358 (start vendor.mdm_helper)`
- `[   43.553074]  [7:             sh: 1454] cnss-daemon wlfw_start: Starting`
- `[   43.663510]  [6:  Binder:1144_2: 1178] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[   44.423626]  [7:  kworker/u16:9:  297] icnss_qmi: QMI Server Connected: state: 0x980`
- `[   44.492714]  [3:             sh: 1784] cnss-daemon wlfw_send_bdf_download_req: BDF file : regdb.bin`
- `[   44.507763]  [7:             sh: 1789] cnss-daemon wlfw_send_bdf_download_req: BDF file : bdwlan.bin`
- `[   49.512521]  [7:  kworker/u16:3:  245] [kworke][0x4d92033e][01:42:32.679422] wlan: [245:I:WMA] wma_wait_for_ready_event: 6926: FW ready event received`
- `[   49.725190]  [5:  kworker/u16:3:  245] dev : wlan0 : event : 16`
- `[   49.739966]  [5:  kworker/u16:3:  245] icnss 18800000.qcom,icnss wlan0: set_features() failed (-11); wanted 0x0000000000004000, left 0x0000000000004800`
- `[   49.740047]  [5:  kworker/u16:3:  245] dev : wlan0 : event : 5`
- `[   42.998748] subsys-restart: __subsystem_get(): __subsystem_get: modem count:1`
- `[   43.553074] cnss-daemon wlfw_start: Starting`
- `[   43.663510] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[   44.423626] icnss_qmi: QMI Server Connected: state: 0x980`
- `[   44.492714] cnss-daemon wlfw_send_bdf_download_req: BDF file : regdb.bin`
- `[   44.507763] cnss-daemon wlfw_send_bdf_download_req: BDF file : bdwlan.bin`
- `[   49.512521] [kworke][0x4d92033e][01:42:32.679422] wlan: [245:I:WMA] wma_wait_for_ready_event: 6926: FW ready event received`
- `[   49.725190] dev : wlan0 : event : 16`
- `[   49.739966] icnss 18800000.qcom,icnss wlan0: set_features() failed (-11); wanted 0x0000000000004000, left 0x0000000000004800`
- `[   49.740047] dev : wlan0 : event : 5`

## Safety

Host-only classifier. It reads already captured V1532 evidence and performs no device command, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, or external ping.

## Next Gate

- Cycle: `V1534`
- Summary: target pm-service Binder/esoc0 subsystem_get and immediate pci-msm first-L0 path, not ICNSS workqueue or firmware/MHI
- Candidate: Android host-only/source classifier for pm-service Binder request that causes subsystem_get(esoc0)
- Candidate: bounded Android trace/u(ret)probe design around pm-service QMI/Binder voter callsite if symbols or safe offsets are available
- Candidate: native pre-L0 gate only after the pm-service/esoc0 trigger semantics are mapped
