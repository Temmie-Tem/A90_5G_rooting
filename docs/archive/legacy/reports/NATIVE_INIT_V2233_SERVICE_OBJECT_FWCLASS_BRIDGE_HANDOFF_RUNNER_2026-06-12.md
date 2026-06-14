# Native Init V2233 Service-Object FWClass Bridge Handoff Runner

## Summary

- Cycle: `V2233`
- Type: rollbackable service-object fwclass bridge handoff runner; default execution is host-only dry-run.
- Decision: `v2233-service-object-fwclass-bridge-helper-parsed-rollback-pass`
- Result: `PASS`
- Reason: V2232 helper artifacts were collected, parsed by V2220, and rollback selftest fail=0
- Execute mode: `True`
- Evidence: `workspace/private/runs/kernel/v2233-live-20260612-083738`

## Images

- Test image: `workspace/private/inputs/boot_images/boot_linux_v2232_service_object_fwclass_bridge.img`
- Test SHA256: `dd56aa2dd8c0d9b2bafd1c12e23a3db6ba7095bea5e632ab03c5785fac69786c`
- Test version: `A90 Linux init 0.9.266 (v2232-service-object-fwclass-bridge)`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2189_security_p0_stage_fix.img`
- Rollback SHA256: `f54becb2b720ad198413c2a0089912626ca295c79a96f13e0921cf4f05b39f51`
- Rollback version: `A90 Linux init 0.9.261 (v2189-security-p0-stage-fix)`

## Live Contract

- Live mode requires `--execute` plus the exact confirmation token.
- Live sequence: V2222 preflight -> flash V2232 -> collect `/cache/native-init-wifi-test-boot-v2232-*` -> V2220 parser -> rollback V2189 -> selftest fail=0.
- Collection is read-only after boot; it uses `cat` over the native bridge and the helper-owned trace output.

## Live Evidence

- Rollback OK: `True`
- Rollback selftest fail=0: `True`
- Parser decision: `v2220-helper-summary-parser-validated-existing-hit-current-nohit`
- Parser pass: `True`
- Parser hits: total=`671` hit_events=`121` key_hit_events=`8`
- Helper diagnosis: `helper-artifacts-present`
- Helper result: supervisor=`wlan0-ready` exit=`0` timed_out=`0` wlan0_present=`1`

## Nonlog Control-Flow Summary

- Classifier: `wlfw-worker-thread-started-qmi-cap-sent`
- `pm_init_pm_client_register_call`: hits=`1`
- `pm_init_pm_client_register_retcheck`: hits=`1`
- `periph_default_service_manager_call`: hits=`1`
- `periph_manager_name_string16_call`: hits=`1`
- `wlfw_bdf_send_ret`: hits=`9`
- `wlfw_bdf_result_log`: hits=`2`
- `wlfw_worker_done_signal`: hits=`1`

## Service-Object Snapshot

- Classifier: `provider-visible-modem-holder-regression`
- Service readiness: vnd=`1` pm_proxy=`1` per_mgr=`1` provider_seen=`1`
- Runtime children: tftp=`1` cnss_daemon=`1` modem_holder_opened=`0`
- Request snapshot: wlfw_start=`1` wlfw_service_request=`1` service69=`0` requested_wlanmdsp=`0` wlan0=`1`

## Post-FW_READY Boot WLAN Trigger

- Begin: `1`
- FW_READY processed: pre=`0` final=`1`
- Register-driver counters: posted=`0` processed=`0`
- Path: exists=`1` writable=`1` gate_ready=`1`
- Write: executed=`1` rc=`0` errno=`0` reason=`boot-wlan-write-ok`

## QCACLD Firmware-Class Feeder

- `after_boot_wlan_trigger`: seen=`1` fed=`1` timed_out=`1` r0=`1/1` r1=`0/0` r2=`0/0`

## ICNSS After Boot-WLAN Long Window

- FW_READY processed: `1`
- REGISTER_DRIVER: posted=`1` processed=`1`
- CFG: req=`1` resp=`1`
- MODE: req=`2` resp=`2`
- INI: req=`1` resp=`1`
- State: `0xd8d` `State: 0xd8d(FW CONN | FW READY | DRIVER PROBED | SSR REGISTERED | PDR REGISTERED | MSA0 ASSIGNED | WLAN FW EXISTS)`

## WLFW Edge Summary

- `uprobe:wlfw_start`: hits=`1` first_ts=`6.761794`
- `uprobe:wlfw_service_request`: hits=`1` first_ts=`6.787543`
- `uprobe:wlfw_cap_qmi`: hits=`1` first_ts=`67.47455`
- `uprobe:wlfw_bdf_entry`: hits=`2` first_ts=`67.519332`
- `uprobe:wlfw_bdf_send_ret`: hits=`9` first_ts=`67.534553`
- `uprobe:wlfw_bdf_result_log`: hits=`2` first_ts=`67.536301`
- `uprobe:wlfw_worker_done_signal`: hits=`1` first_ts=`67.552239`
- `uprobe:wlfw_worker_post_done_wait`: hits=`1` first_ts=`67.552244`
- `libqmi_uprobe:libqmi_loop_client_init_ret`: hits=`2` first_ts=`67.284186`

## Live Diagnosis

- V2232 crossed the V2231 post-BDF wall: helper supervisor ended `wlan0-ready` and `wlan0_present=1`.
- Required missing tail was confirmed: post-FW_READY `/sys/kernel/boot_wlan/boot_wlan` executed=`1` with reason=`boot-wlan-write-ok` and write_rc=`0`.
- QCACLD firmware_class feeder supplied the first observed request after the trigger: phases=`after_boot_wlan_trigger`.
- ICNSS long-window state reached REGISTER_DRIVER processed=`1` and state=`0xd8d`.
- This localizes V2231 failure to the missing post-FW_READY driver-start/firmware_class tail in the service-object-visible route, not service-manager/PM registration, WLFW cap/BDF QMI, or post-BDF wait length.

## Safety Scope

- Dry-run does not flash, reboot, write device partitions, scan/connect Wi-Fi, use credentials, configure DHCP/routes, ping, attach BPF, execute `probe_write_user`, or write tracefs controls.
- Live mode flashes only the approved rollbackable V2232 test boot and V2189 rollback image.
- It does not use Wi-Fi HAL scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC/eSoC/PCI paths, platform bind/unbind, or `sda29` writes.
