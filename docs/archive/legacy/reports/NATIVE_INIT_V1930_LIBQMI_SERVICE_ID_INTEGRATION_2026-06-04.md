# Native Init V1930 Libqmi CCI Service-ID Integration

## Summary

- Cycle: `V1930`
- Decision: `v1930-wlfw-service69-not-published-libqmi-rollback-pass`
- Label: `wlfw-service69-not-published-libqmi`
- Pass: `True`
- Reason: WLFW lookup requested QMI service 69, but libqmi observed only non-WLFW new-server services ['0x3']
- Evidence: `tmp/wifi/v1930-libqmi-service-id-integration`
- Inner handoff: `tmp/wifi/v1930-libqmi-service-id-integration/v1929-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | wlfw-service69-not-published-libqmi | WLFW lookup requested QMI service 69, but libqmi observed only non-WLFW new-server services ['0x3'] |
| combined | True | service74=True pm_open=True holder=True |
| publication | False | wlfw69=False wlan_pd=False wlanmdsp=False wlan0=False |
| libqmi | qmi-client-init-instance-returned | target=/tmp/a90-v231-548/root/vendor/lib64/libqmi_cci.so hits=48 wlfw_thread=637 wait_outstanding=True |
| service_ids | ['0x2', '0x45'] | new_server=['0x3'] lookup69=True new_server69=False |
| servnotif | uninit | indication=0 qrtr69=0,0 |

## Libqmi Events

| event | registered/enabled/hits | first hit |
| --- | --- | --- |
| libqmi_get_service_list_entry | 1/1/7 | cnss-daemon-637   [003] ....     6.783717: libqmi_get_service_list_entry: (0x7fa9f6de08) svc_obj=0x557d29df90 list=0x7f1f4e1ae0 capacity=0x7f1f4e1a14 count=0x7f1f4e1a10 |
| libqmi_get_service_list_lookup_call | 1/1/7 | cnss-daemon-637   [003] ....     6.783727: libqmi_get_service_list_lookup_call: (0x7fa9f6deec) xport=0x0 xport_id=0x0 svc_id=0x45 idl_version=0x1 capacity_ptr=0x7f1f4e199c list_ptr=0x7f1f4e1ae0 lookup_fn=0x7fa9f71a30 |
| libqmi_get_service_list_lookup_ret | 1/1/7 | cnss-daemon-637   [003] ....     6.784757: libqmi_get_service_list_lookup_ret: (0x7fa9f6def0) found=0x0 list=0x7f1f4e1ae0 capacity_ptr=0x7f1f4e1a14 count_ptr=0x7f1f4e1a10 offset=0x0 xport_index=0x0 |
| libqmi_client_init_instance_entry | 1/1/2 | cnss-daemon-637   [003] ....     6.783710: libqmi_client_init_instance_entry: (0x7fa9f6f824) svc=0x557d29df90 instance=0xffff ind_cb=0x557d295100 ind_data=0x0 os_params=0x7f1f4e1b90 timeout=0x0 handle=0x7f1f4e1b68 |
| libqmi_initial_get_service_instance_ret | 1/1/2 | cnss-daemon-637   [003] ....     6.784777: libqmi_initial_get_service_instance_ret: (0x7fa9f6f8a0) rc=0xfffffffe |
| libqmi_initial_client_init_ret | 1/1/0 | none |
| libqmi_notifier_init_call | 1/1/2 | cnss-daemon-637   [003] ....     6.784781: libqmi_notifier_init_call: (0x7fa9f6f8ec) svc=0x557d29df90 signal=0x7f1f4e1a70 handle_out=0x7f1f4e1a68 |
| libqmi_notifier_init_ret | 1/1/2 | cnss-daemon-637   [003] ....     6.785891: libqmi_notifier_init_ret: (0x7fa9f6f8f0) rc=0x0 |
| libqmi_wait_call | 1/1/2 | cnss-daemon-637   [003] ....     6.786756: libqmi_wait_call: (0x7fa9f6f904) signal=0x7f1f4e1a70 timeout=0x0 |
| libqmi_wait_return | 1/1/1 | cnss-daemon-636   [000] ....     7.694082: libqmi_wait_return: (0x7fa9f6f908) |
| libqmi_loop_get_service_instance_ret | 1/1/3 | cnss-daemon-637   [003] ....     6.786751: libqmi_loop_get_service_instance_ret: (0x7fa9f6f924) rc=0xfffffffe |
| libqmi_loop_client_init_ret | 1/1/1 | cnss-daemon-636   [001] ....     7.696263: libqmi_loop_client_init_ret: (0x7fa9f6f944) rc=0x0 |
| libqmi_init_timeout_path | 1/1/0 | none |
| libqmi_init_return | 1/1/1 | cnss-daemon-636   [001] ....     7.696284: libqmi_init_return: (0x7fa9f6f970) rc=0x0 |
| libqmi_signal_wait_entry | 1/1/6 | cnss-daemon-629   [002] ....     6.745491: libqmi_signal_wait_entry: (0x7fa9f6fe74) signal=0x7f25dfbbb0 timeout=0x0 |
| libqmi_signal_wait_timedwait | 1/1/2 | cnss-daemon-636   [000] ....     6.791573: libqmi_signal_wait_timedwait: (0x7fa9f6ffb8) |
| libqmi_signal_wait_timeout_store | 1/1/0 | none |
| libqmi_xport_new_server_entry | 1/1/1 | cnss-daemon-630   [003] ....     7.694013: libqmi_xport_new_server_entry: (0x7fa9f6c8e8) xport=0xb400007fa6283c00 |
| libqmi_xport_new_server_service | 1/1/1 | cnss-daemon-630   [003] ....     7.694030: libqmi_xport_new_server_service: (0x7fa9f6c910) xport=0xb400007fa6283c00 svc_id=3 state=0 addr=548315802464 notifier=545987088432 |
| libqmi_xport_new_server_signal | 1/1/1 | cnss-daemon-630   [003] ....     7.694038: libqmi_xport_new_server_signal: (0x7fa9f6c96c) xport=0xb400007fa6283c00 svc_id=3 signal=0x7f1f5dd03c waiter=0x7f1f5dd03c |
| libqmi_xport_new_server_callback_call | 1/1/0 | none |

## Service-ID Decode

- Lookup service IDs: `['0x2', '0x45']`
- New-server service IDs: `['0x3']`
- WLFW service 69 lookup seen: `True`
- WLFW service 69 new-server seen: `False`

## WLFW Client Events

| event | registered/enabled/hits | first hit |
| --- | --- | --- |
| wlfw_start | 1/1/1 | cnss-daemon-626   [000] ....     6.777996: wlfw_start: (0x557d295c00) |
| dms_service_request | 1/1/1 | cnss-daemon-636   [000] ....     6.783570: dms_service_request: (0x557d295808) |
| wlfw_service_request | 1/1/1 | cnss-daemon-637   [003] ....     6.783651: wlfw_service_request: (0x557d2949fc) |
| wlfw_worker_pthread_create_success | 1/1/1 | cnss-daemon-626   [001] ....     6.783619: wlfw_worker_pthread_create_success: (0x557d295da0) |
| wlfw_client_init_instance_call | 1/1/1 | cnss-daemon-637   [003] ....     6.783704: wlfw_client_init_instance_call: (0x557d294aa8) arg0=0x557d29df90 arg1=0xffff arg2=0x557d295100 arg3=0x0 |
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

## Route State

- PM open: `/dev/subsys_modem` fd `0x8`
- Holder fd: `27`
- Labels: `qmi-client-init-instance-returned` / `qmi-client-init-instance-returned` / `modem-holder-regression` / `provider-visible-modem-holder-regression`
- Servloc: `domain-list-response-success` domain `msm/modem/wlan_pd` instance `180`

## Remaining Blocker

- The combined native route now reaches clean-DSP service74, PM `/dev/subsys_modem` open, holder, CNSS WLFW worker, and WLFW service-list lookup for QMI service 69.
- The missing edge is service-69/WLAN-PD publication into libqmi/QRTR; only non-WLFW service `0x3` published during this window.
- Next candidate: read-only Android-normal versus native comparison of the service-69 publication edge, keeping the internal modem route and no HAL/scan/connect until `wlan0` exists.

## Steps

- `pre-version` rc `0` ok `True` evidence `host/pre-version.txt`
- `pre-selftest` rc `0` ok `True` evidence `host/pre-selftest.txt`
- `pre-flags` rc `0` ok `True` evidence `host/pre-flags.txt`
- `arm-clean-dsp-flag` rc `0` ok `True` evidence `host/arm-clean-dsp-flag.txt`
- `cleanup-leftover-clean-dsp-flag` rc `1` ok `False` evidence `host/cleanup-leftover-clean-dsp-flag.txt`
- `post-selftest` rc `0` ok `True` evidence `host/post-selftest.txt`
- `post-status` rc `0` ok `True` evidence `host/post-status.txt`
- `post-flags` rc `0` ok `True` evidence `host/post-flags.txt`

## Safety

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
- No direct `/dev/subsys_esoc0` open/control, forced RC1/case, PMIC/GPIO/GDSC/regulator, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V1929 test-boot flash-handoff, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
