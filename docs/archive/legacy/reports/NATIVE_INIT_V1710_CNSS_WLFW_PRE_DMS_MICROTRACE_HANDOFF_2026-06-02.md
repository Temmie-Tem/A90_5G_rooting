# Native Init V1710 CNSS WLFW Pre-DMS Microtrace Handoff

## Summary

- Cycle: `V1710`
- Type: one-run rollbackable CNSS `wlfw_start` pre-DMS tracefs uprobe classifier
- Decision: `v1710-wlfw-start-pthread-create-not-reached-rollback-pass`
- Result: `PASS`
- Evidence: `tmp/wifi/v1710-cnss-wlfw-pre-dms-microtrace-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`

## Gate Label

- output label: `cnss-output-still-invisible`
- microtrace non-log label: `wlfw-start-pthread-create-not-reached`
- legacy firmware-serve label: `firmware-not-requested`
- property lookup all_match: `1`
- cnss-daemon running: `1`
- tftp running: `1`
- companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,cnss_daemon,cnss-output-visibility-summary`

## Microtrace Targets

- `wlfw_start` offset `0xec00` hit_count `1` registered/enabled `1` / `1`
  first_hit: `cnss-daemon-558   [002] ....     3.438180: wlfw_start: (0x557e183c00)`
- `wlfw_service_request` offset `0xd9fc` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_ind_register_qmi` offset `0xf32c` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `wlfw_cap_qmi` offset `0xf460` hit_count `0` registered/enabled `1` / `1`
  first_hit: `none`
- `dms_service_request` offset `0xe808` hit_count `0` registered/enabled `1` / `1`
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

## Control Evidence

- tracefs path/available: `/sys/kernel/debug/tracing` / `1`
- aggregate wlfw_start hit count: `1`
- aggregate first hit line: `cnss-daemon-558   [002] ....     3.438180: wlfw_start: (0x557e183c00)`
- maps text seen / runtime PC: `1` / `0x557e183c00`
- socket/kmsg fd counts: `10` / `0`
- MHI pipe fd count / ks process count: `0` / `0`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- service-manager, PM trio, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Interpretation

- This V1710 run narrows V1708's `wlfw_start` entry-only result to the exact pre-DMS pthread init boundary.
- WLFW QMI/BDF remains downstream unless this run reaches `dms_initialize`, worker creation, or later QMI call targets.
- Any `call-no-return` label means the traced pthread init call did not return within the observation window.
- Any `retcheck-no-*` label means that return check executed but the next expected call target did not fire.
- This classifier does not start Wi-Fi HAL, scan, connect, or external network tests.
