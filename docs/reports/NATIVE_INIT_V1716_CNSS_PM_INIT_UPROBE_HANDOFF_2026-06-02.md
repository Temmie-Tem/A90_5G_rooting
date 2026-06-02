# Native Init V1716 CNSS pm_init Uprobe Handoff

## Summary

- Cycle: `V1716`
- Type: one-run rollbackable CNSS `pm_init` tracefs uprobe classifier
- Decision: `v1716-pm-init-register-call-no-return-rollback-pass`
- Result: `PASS`
- Evidence: `tmp/wifi/v1716-cnss-pm-init-uprobe-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`

## Gate Label

- output label: `cnss-output-still-invisible`
- pm_init non-log label: `pm-init-register-call-no-return`
- legacy firmware-serve label: `firmware-not-requested`
- property lookup all_match: `1`
- cnss-daemon running: `1`
- tftp running: `1`
- companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,cnss_daemon,cnss-output-visibility-summary`

## Result Interpretation

- `wlfw_start` is reached and returns from the unconditional log wrapper.
- `pm_init(1, NULL)` enters the null-peripheral scan, reaches `pm_client_register@0xc624`, and does not hit the return check at `0xc628`.
- `get_system_info` is not the blocker: both `pm_init_get_system_info_call@0xc444` and `pm_init_system_info_ok@0xc470` hit.
- `pm_client_connect` is not reached: `pm_init_pm_client_connect_call@0xc650` hit count is `0`.
- The next blocker is inside `pm_client_register`, still without requiring service-manager, PM trio, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.

## pm_init Trace Targets

- `wlfw_start` offset `0xec00` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.468316: wlfw_start: (0x5565b44c00)`
- `wlfw_service_request` offset `0xd9fc` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_ind_register_qmi` offset `0xf32c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cap_qmi` offset `0xf460` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `dms_service_request` offset `0xe808` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_log_arg_severity` offset `0xec20` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.468342: wlfw_log_arg_severity: (0x5565b44c20)`
- `wlfw_log_call` offset `0xec24` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.468348: wlfw_log_call: (0x5565b44c24)`
- `wlfw_post_log_branch` offset `0xec28` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.479241: wlfw_post_log_branch: (0x5565b44c28)`
- `wlfw_optional_pm_init1_call` offset `0xec34` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.479248: wlfw_optional_pm_init1_call: (0x5565b44c34)`
- `wlfw_optional_pm_init1_return` offset `0xec38` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_optional_pm_init2_call` offset `0xec44` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_common_state_base` offset `0xec48` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cal_mutex_arg` offset `0xec50` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cal_mutex_null_attr` offset `0xec54` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cal_mutex_call` offset `0xec58` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cal_mutex_retcheck` offset `0xec5c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cal_mutex_fail` offset `0xec60` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_mutex_call` offset `0xec78` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_mutex_retcheck` offset `0xec7c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_mutex_fail` offset `0xec80` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_call` offset `0xec9c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_retcheck` offset `0xeca0` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_fail` offset `0xeca4` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_rsp_call` offset `0xecbc` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_rsp_retcheck` offset `0xecc0` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cond_rsp_fail` offset `0xecc4` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_dms_initialize_call` offset `0xecd4` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_dms_initialize_retcheck` offset `0xecd8` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_worker_pthread_create_call` offset `0xecf0` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_worker_pthread_create_failure` offset `0xecf8` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_worker_pthread_create_success` offset `0xeda0` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `pm_init_entry` offset `0xc39c` hit_count `2` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.479252: pm_init_entry: (0x5565b4239c)`
- `pm_init_entry_log_call` offset `0xc400` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [002] ....     3.479263: pm_init_entry_log_call: (0x5565b42400)`
- `pm_init_type_check` offset `0xc404` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [000] ....     3.491405: pm_init_type_check: (0x5565b42404)`
- `pm_init_get_system_info_call` offset `0xc444` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [000] ....     3.491418: pm_init_get_system_info_call: (0x5565b42444)`
- `pm_init_system_info_ok` offset `0xc470` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [000] ....     3.492354: pm_init_system_info_ok: (0x5565b42470)`
- `pm_init_null_peripheral_branch` offset `0xc49c` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [003] ....     3.504041: pm_init_null_peripheral_branch: (0x5565b4249c)`
- `pm_init_null_peripheral_loop_entry` offset `0xc58c` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [003] ....     3.504047: pm_init_null_peripheral_loop_entry: (0x5565b4258c)`
- `pm_init_null_loop_type_check` offset `0xc5e0` hit_count `2` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [003] ....     3.504054: pm_init_null_loop_type_check: (0x5565b425e0)`
- `pm_init_pm_client_register_call` offset `0xc624` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-560   [003] ....     3.515460: pm_init_pm_client_register_call: (0x5565b42624)`
- `pm_init_pm_client_register_retcheck` offset `0xc628` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `pm_init_handle_load` offset `0xc62c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `pm_init_pm_client_connect_call` offset `0xc650` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `pm_init_pm_client_connect_retcheck` offset `0xc654` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `pm_init_return_path` offset `0xc554` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`

## Control Evidence

- tracefs path/available: `/sys/kernel/debug/tracing` / `1`
- aggregate hit count: `1`
- aggregate first hit line: `cnss-daemon-560   [002] ....     3.468316: wlfw_start: (0x5565b44c00)`
- maps text seen / runtime PC: `1` / `0x5565b44c00`
- socket/kmsg fd counts: `10` / `0`
- MHI pipe fd count / ks process count: `0` / `0`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- service-manager, PM trio, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Interpretation

- This V1716 run distinguishes whether `pm_init(1, NULL)` blocks in `get_system_info`, the null-peripheral scan, `pm_client_register`, or `pm_client_connect`.
- If `pm-init-connect-call-no-return` appears, the next blocker is inside `pm_client_connect` without adding PM/service-window actors.
- If `pm-init-register-call-no-return` appears, the blocker is earlier in the PM client registration path.
- This classifier does not start Wi-Fi HAL, scan, connect, or external network tests.
