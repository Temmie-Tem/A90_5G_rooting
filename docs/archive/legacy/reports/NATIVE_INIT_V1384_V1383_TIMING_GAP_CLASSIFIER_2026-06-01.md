# Native Init V1384 V1383 Timing Gap Classifier

## Summary

- Cycle: `V1384`
- Type: host-only V1383 timing/gap classifier
- Decision: `v1384-immediate-flag-still-too-late-poll-entry-gap`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_v1383_timing_gap_classifier_v1384.py`
- Reason: V1383 fired corrected RC1 in the first v284 poll and the debugfs write itself reaches RC1 immediately, but RC1 assert still occurred 3.666s after esoc0 versus Android's 0.255s; this is only 0.456s faster than V1379 and still fails before L0 with no downstream progress.
- Next Step: V1385 source/build-only: move the RC1 trigger earlier than the late_per_proxy poll loop, or add tight timing instrumentation around per_proxy start and pm-service powerup-thread first observation

## Checks

| check | pass |
| --- | --- |
| v1381_helper_support_passed | true |
| v1382_deploy_passed | true |
| v1383_live_passed | true |
| v1383_immediate_flag_in_child | true |
| v1383_corrected_triggered | true |
| v1383_powerup_gate_positive | true |
| v1383_write_ok | true |
| v1383_dmesg_transition_seen | true |
| v1383_no_l0 | true |
| v1383_no_downstream | true |
| v1383_still_late_vs_android | true |
| v1383_not_substantially_better_than_v1379 | true |
| host_only | true |

## Timing

| field | value |
| --- | --- |
| android_esoc0_to_assert_sec | 0.254929 |
| android_release_to_l0_sec | 0.016666 |
| v1379_esoc0_to_assert_sec | 4.122735 |
| v1383_esoc0_to_assert_sec | 3.666356 |
| v1383_vs_android_ratio | 14.381871 |
| v1383_improvement_vs_v1379_sec | 0.456379 |
| v1383_test11_to_assert_sec | 0.000020 |
| v1383_assert_to_release_sec | 0.005460 |
| v1383_release_to_poll_compliance_sec | 0.042070 |
| v1383_release_to_link_failed_sec | 0.109080 |

## Interpretation

| field | value |
| --- | --- |
| debugfs_write_latency_is_not_primary | true |
| poll_loop_entry_or_per_proxy_ordering_is_primary | true |
| endpoint_l0_still_unproven | true |
| another_live_retry_without_reordering_is_low_value | true |

## Dmesg Evidence

- `esoc0`: [ 1704.113455] [2:  Binder:9304_4: 9928] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0
- `test11`: [ 1707.779791] [6:a90_android_exe: 1180] PCIe: TEST: 11
- `assert`: [ 1707.779811] [6:a90_android_exe: 1180] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.
- `release`: [ 1707.785271] [6:a90_android_exe: 1180] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.
- `poll_compliance`: [ 1707.827341] [3:a90_android_exe: 1180] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE
- `link_failed`: [ 1707.894351] [3:a90_android_exe: 1180] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3)

## Hard Exclusions

- host-only; no device command
- no debugfs/sysfs write, rc_sel/case write, or PCI rescan
- no PMIC/GPIO/GDSC direct write
- no eSoC notify or BOOT_DONE spoof
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping
- no flash, boot image write, or partition write
