# Native Init V1937 ICNSS IPC Service69 Integration

## Summary

- Cycle: `V1937`
- Decision: `v1937-native-icnss-ipc-pd-registration-no-wlfw-arrive-rollback-pass`
- Label: `native-icnss-ipc-pd-registration-no-wlfw-arrive`
- Pass: `True`
- Reason: native ICNSS IPC records wlan_pd domain/PD notification progress, but no WLFW server-arrive edge reaches libqmi service69
- Evidence: `tmp/wifi/v1937-icnss-ipc-service69-integration`
- Inner handoff: `tmp/wifi/v1937-icnss-ipc-service69-integration/v1936-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | native-icnss-ipc-pd-registration-no-wlfw-arrive | native ICNSS IPC records wlan_pd domain/PD notification progress, but no WLFW server-arrive edge reaches libqmi service69 |
| base_label | wlfw-service69-not-published-libqmi | libqmi=qmi-client-init-instance-returned |
| combined | True | service74=True service180=True pm_open=True holder=True |
| publication | False | wlfw69=False wlan_pd=False wlanmdsp=False wlan0=False |
| service69 | True | wait_outstanding=True wait_return=False new_server69=False |
| icnss_ipc | True | notify=True pd=True reg=True arrive=False |

## ICNSS IPC / Debugfs

| source | readability | markers | first focus |
| --- | --- | --- | --- |
| after_holder_start/debugfs_ipc_logging | exists=True readable=115 lines=3317 focus=33 | notify=True pd=True reg=True arrive=False svc69=False | [     4.841290014/        0x1a724cca] icnss: Modem-Notify: event 2 |
| after_holder_start/proc_ipc_logging | exists=False readable=0 lines=0 focus=0 | notify=False pd=False reg=False arrive=False svc69=False | missing |
| after_early_listener/debugfs_ipc_logging | exists=True readable=115 lines=3089 focus=0 | notify=False pd=False reg=False arrive=False svc69=False | missing |
| after_early_listener/proc_ipc_logging | exists=False readable=0 lines=0 focus=0 | notify=False pd=False reg=False arrive=False svc69=False | missing |
| after_post_listener_window/debugfs_ipc_logging | exists=True readable=115 lines=2223 focus=0 | notify=False pd=False reg=False arrive=False svc69=False | missing |
| after_post_listener_window/proc_ipc_logging | exists=False readable=0 lines=0 focus=0 | notify=False pd=False reg=False arrive=False svc69=False | missing |
| after_holder_start/icnss_stats | open=True lines=68 error=none | ind=True cap=True msa_ready=True mode=True |  |
| after_early_listener/icnss_stats | open=True lines=68 error=none | ind=True cap=True msa_ready=True mode=True |  |
| after_post_listener_window/icnss_stats | open=True lines=68 error=none | ind=True cap=True msa_ready=True mode=True |  |

## Libqmi Events

| event | registered/enabled/hits | first hit |
| --- | --- | --- |
| libqmi_get_service_list_entry | 1/1/7 | cnss-daemon-634   [002] ....     6.681523: libqmi_get_service_list_entry: (0x7fa4aace08) svc_obj=0x558f2b9f90 list=0x7f1ba45ae0 capacity=0x7f1ba45a14 count=0x7f1ba45a10 |
| libqmi_get_service_list_lookup_call | 1/1/7 | cnss-daemon-634   [002] ....     6.681533: libqmi_get_service_list_lookup_call: (0x7fa4aaceec) xport=0x0 xport_id=0x0 svc_id=0x45 idl_version=0x1 capacity_ptr=0x7f1ba4599c list_ptr=0x7f1ba45ae0 lookup_fn=0x7fa4ab0a30 |
| libqmi_get_service_list_lookup_ret | 1/1/7 | cnss-daemon-634   [002] ....     6.682540: libqmi_get_service_list_lookup_ret: (0x7fa4aacef0) found=0x0 list=0x7f1ba45ae0 capacity_ptr=0x7f1ba45a14 count_ptr=0x7f1ba45a10 offset=0x0 xport_index=0x0 |
| libqmi_client_init_instance_entry | 1/1/2 | cnss-daemon-634   [002] ....     6.681516: libqmi_client_init_instance_entry: (0x7fa4aae824) svc=0x558f2b9f90 instance=0xffff ind_cb=0x558f2b1100 ind_data=0x0 os_params=0x7f1ba45b90 timeout=0x0 handle=0x7f1ba45b68 |
| libqmi_initial_get_service_instance_ret | 1/1/2 | cnss-daemon-634   [002] ....     6.682547: libqmi_initial_get_service_instance_ret: (0x7fa4aae8a0) rc=0xfffffffe |
| libqmi_initial_client_init_ret | 1/1/0 | none |
| libqmi_notifier_init_call | 1/1/2 | cnss-daemon-634   [002] ....     6.682551: libqmi_notifier_init_call: (0x7fa4aae8ec) svc=0x558f2b9f90 signal=0x7f1ba45a70 handle_out=0x7f1ba45a68 |
| libqmi_notifier_init_ret | 1/1/2 | cnss-daemon-634   [001] ....     6.683747: libqmi_notifier_init_ret: (0x7fa4aae8f0) rc=0x0 |
| libqmi_wait_call | 1/1/2 | cnss-daemon-634   [001] ....     6.684643: libqmi_wait_call: (0x7fa4aae904) signal=0x7f1ba45a70 timeout=0x0 |
| libqmi_wait_return | 1/1/1 | cnss-daemon-633   [003] ....     7.738428: libqmi_wait_return: (0x7fa4aae908) |
| libqmi_loop_get_service_instance_ret | 1/1/3 | cnss-daemon-634   [001] ....     6.684639: libqmi_loop_get_service_instance_ret: (0x7fa4aae924) rc=0xfffffffe |
| libqmi_loop_client_init_ret | 1/1/1 | cnss-daemon-633   [003] ....     7.741902: libqmi_loop_client_init_ret: (0x7fa4aae944) rc=0x0 |
| libqmi_init_timeout_path | 1/1/0 | none |
| libqmi_init_return | 1/1/1 | cnss-daemon-633   [003] ....     7.741924: libqmi_init_return: (0x7fa4aae970) rc=0x0 |
| libqmi_signal_wait_entry | 1/1/6 | cnss-daemon-626   [001] ....     6.644433: libqmi_signal_wait_entry: (0x7fa4aaee74) signal=0x7f20bfbbb0 timeout=0x0 |
| libqmi_signal_wait_timedwait | 1/1/2 | cnss-daemon-633   [002] ....     6.688247: libqmi_signal_wait_timedwait: (0x7fa4aaefb8) |
| libqmi_signal_wait_timeout_store | 1/1/0 | none |
| libqmi_xport_new_server_entry | 1/1/1 | cnss-daemon-627   [002] ....     7.738347: libqmi_xport_new_server_entry: (0x7fa4aab8e8) xport=0xb400007fa1083c00 |
| libqmi_xport_new_server_service | 1/1/1 | cnss-daemon-627   [002] ....     7.738365: libqmi_xport_new_server_service: (0x7fa4aab910) xport=0xb400007fa1083c00 svc_id=3 state=0 addr=548220341088 notifier=545925632048 |
| libqmi_xport_new_server_signal | 1/1/1 | cnss-daemon-627   [002] ....     7.738372: libqmi_xport_new_server_signal: (0x7fa4aab96c) xport=0xb400007fa1083c00 svc_id=3 signal=0x7f1bb4103c waiter=0x7f1bb4103c |
| libqmi_xport_new_server_callback_call | 1/1/0 | none |

## WLFW Client Events

| event | registered/enabled/hits | first hit |
| --- | --- | --- |
| wlfw_start | 1/1/1 | cnss-daemon-623   [002] ....     6.675660: wlfw_start: (0x558f2b1c00) |
| dms_service_request | 1/1/1 | cnss-daemon-633   [003] ....     6.681211: dms_service_request: (0x558f2b1808) |
| wlfw_service_request | 1/1/1 | cnss-daemon-634   [002] ....     6.681462: wlfw_service_request: (0x558f2b09fc) |
| wlfw_worker_pthread_create_success | 1/1/1 | cnss-daemon-623   [002] ....     6.681275: wlfw_worker_pthread_create_success: (0x558f2b1da0) |
| wlfw_client_init_instance_call | 1/1/1 | cnss-daemon-634   [002] ....     6.681509: wlfw_client_init_instance_call: (0x558f2b0aa8) arg0=0x558f2b9f90 arg1=0xffff arg2=0x558f2b1100 arg3=0x0 |
| wlfw_client_init_instance_retcheck | 1/1/0 | none |
| wlfw_client_init_instance_fail_log | 1/1/0 | none |
| wlfw_register_error_cb_call | 1/1/0 | none |
| wlfw_register_error_cb_retcheck | 1/1/0 | none |
| wlfw_get_service_instance_call | 1/1/0 | none |
| wlfw_get_service_instance_retcheck | 1/1/0 | none |
| wlfw_get_instance_id_call | 1/1/0 | none |
| wlfw_get_instance_id_retcheck | 1/1/0 | none |
| wlfw_send_ind_register_entry | 1/1/0 | none |
| wlfw_fw_mem_cond_wait | 1/1/0 | none |
| wlfw_ind_register_qmi | 1/1/0 | none |
| wlfw_cap_qmi | 1/1/0 | none |

## Interpretation

- Android-good V1917 records ICNSS IPC `PD notification registration happened` followed by `WLFW server arrive`; Android-good V1934 then returns the WLFW service69 wait.
- This run keeps the internal-modem A1 route and classifies whether native reaches that ICNSS IPC edge before the known libqmi wait-return gap.
- Stop remains before Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping unless WLFW service69 and `wlan0` are proven.

## Steps

- `pre-version` rc `0` ok `True` evidence `host/pre-version.txt`
- `pre-selftest` rc `0` ok `True` evidence `host/pre-selftest.txt`
- `pre-flags` rc `0` ok `True` evidence `host/pre-flags.txt`
- `arm-clean-dsp-flag` rc `0` ok `True` evidence `host/arm-clean-dsp-flag.txt`
- `cleanup-leftover-clean-dsp-flag` rc `0` ok `True` evidence `host/cleanup-leftover-clean-dsp-flag.txt`
- `post-selftest` rc `0` ok `True` evidence `host/post-selftest.txt`
- `post-status` rc `0` ok `True` evidence `host/post-status.txt`
- `post-flags` rc `0` ok `True` evidence `host/post-flags.txt`

## Safety

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
- No direct `/dev/subsys_esoc0` open/control, forced RC1/case, PMIC/GPIO/GDSC/regulator, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V1936 test-boot flash-handoff, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
