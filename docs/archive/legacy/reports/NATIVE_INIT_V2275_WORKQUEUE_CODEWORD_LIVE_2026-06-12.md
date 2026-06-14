# Native Init V2275 Workqueue Codeword Live

## Summary

- Cycle: `V2275`
- Type: rollbackable live validation of the V2274 combined workqueue function-pointer and same-boot codeword observer.
- Decision: `v2275-workqueue-codeword-live-codeword-slide-unusable-rollback-pass`
- Result: `FAIL`
- Reason: V2274 booted and rollback passed, but the combined oracle did not produce classifiable paired workqueue/codeword evidence
- Execute mode: `True`
- Evidence: `workspace/private/runs/kernel/v2275-workqueue-codeword-live-20260612-172723`
- Track: T1 kernel observation; no downgrade to T2/T3.

## Images

- Test image: `workspace/private/inputs/boot_images/boot_linux_v2274_workqueue_codeword_combined.img`
- Test SHA256: `c389a7c423c752e02af4a73fa8d6f3365de53042e71763b16b7c2b011c59bb2f`
- Test version: `A90 Linux init 0.9.274 (v2274-workqueue-codeword-combined)`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Rollback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Rollback version: `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)`

## Live Evidence

- Preflight baseline verified: `True` selftest fail=0: `True`
- V2274 flash OK: `True`
- V2274 health: version=`True` status=`True` selftest_fail0=`True`
- Rollback OK: `True` via `manual-from-native-recovery-after-runner-parser-crash`
- Rollback health: version=`True` status=`True` selftest_fail0=`True`
- Classification: `codeword-slide-unusable`
- Workqueue samples: `2048` stats=`{'total': 12511, 'stored': 2048, 'queue_work': 6254, 'execute_start': 6257, 'overflow': 10463}`
- Codeword slide: accepted=`False` slide=`0xccef4` reason=`not_accepted`
- Target hit count: `0`
- Helper result: supervisor=`wlan0-ready` exit=`0` timed_out=`0` wlan0_present=`1`

## Workqueue Classification

- Workqueue sampler result: `v2273-workqueue-func-sample-ring-complete`
- Kind counts: `{'queue_work': 1018, 'execute_start': 1024, 'unknown': 6}`
- Top symbols: `[('proc_sys_call_handler', 856), ('msm_ssusb_qmp_clamp_enable', 356), ('diagchar_ioctl', 247), ('smb1390_cp_slave_get_prop', 124), ('register_notif_listener', 114), ('shmem_link', 42), ('tty_unregister_driver', 28), ('dma_find_channel', 24), ('blkcg_policy_unregister', 14), ('sdev_show_evt_lun_change_reported', 14), ('sdev_store_evt_lun_change_reported', 14), ('ufs_qcom_phy_clk_state', 13), ('autosuspend_delay_ms_store', 12), ('elv_requeue_request', 12), ('shmem_unlink', 12), ('usb_gadget_map_request_by_dev', 12), ('glink_spss_reset', 10), ('show_nr_prev_assist_thresh', 10), ('ufs_qcom_dump_dbg_regs', 10), ('update_req_stats', 10), ('_debug_stats_read', 8), ('ufshcd_system_suspend', 8), ('__dwc3_gadget_ep_enable', 6), ('dwc3_gadget_pullup', 6)]`
- Target hits: `[]`

## Safety Scope

- Flash path is limited to boot partition via `native_init_flash.py`.
- Rollback target is V2237, with post-rollback `version`/`status`/`selftest fail=0` verification.
- Collection uses read-only `cat` through the native bridge after the helper window.
- This run does not use Wi-Fi scan/connect, credentials, DHCP/routes, external ping, `probe_write_user`, tracefs control writes, eSoC/PCIe/GDSC/PMIC/GPIO paths, platform bind/unbind, or `sda29` writes.
- The only non-read-only target-side operation inside V2274 is the pre-existing bounded firmware_class userspace fallback feed for `WCNSS_qcom_cfg.ini`, `bdwlan.bin`, and `regdb.bin`.

## Orchestration Note

- The first V2275 runner execution crashed during host-side classification after all requested artifacts were collected and before its automatic rollback phase.
- Cause: the workqueue parser reused a list-valued key parser for scalar `stats`/`sample` fields. The runner source is patched to use a scalar parser.
- Safety action: V2237 rollback was executed immediately via `native_init_flash.py`; post-rollback `version`, `status`, and `selftest fail=0` were confirmed.
- Device outcome: no cascading flash was attempted; final device state is `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)` with selftest `fail=0`.
