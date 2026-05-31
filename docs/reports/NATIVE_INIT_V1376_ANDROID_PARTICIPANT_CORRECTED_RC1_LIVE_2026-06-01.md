# Native Init V1376 Android Participant Corrected RC1 Live

## Summary

- Cycle: `V1376`
- Type: bounded live lower Android participant + corrected RC1 enumerate gate
- Decision: `v1376-corrected-rc1-not-triggered`
- Result: FAIL
- Script: `scripts/revalidation/native_wifi_android_participant_corrected_rc1_live_v1376.py`
- Helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v282`)
- Evidence:
  - `tmp/wifi/v1376-android-participant-corrected-rc1-live/manifest.json`
  - `tmp/wifi/v1376-android-participant-corrected-rc1-live/summary.md`

## Key Observations

| field | value |
| --- | --- |
| private_flag_in_child_script | 1 |
| precondition_flag_in_child_script | 1 |
| corrected_rc1_flag_in_child_script | 1 |
| corrected_triggered | False |
| corrected_phase |  |
| corrected_gate_per_mgr_subsys_esoc0_count | -1 |
| corrected_rc_sel_rc | 999 |
| corrected_case_rc | 999 |
| debugfs_control_write_executed | False |
| timing_sample_count | 120 |
| timing_pm_service_powerup_seen | True |
| timing_pcie_rc1_transition_seen | False |
| timing_gpio142_irq_delta | 0 |
| timing_errfatal_irq_delta | 0 |
| timing_pci_dev_max | 0 |
| timing_mhi_bus_max | 0 |
| timing_mhi_pipe_seen | False |
| timing_ks_process_max | 0 |
| timing_wlfw_kmsg_max | 0 |
| timing_wlan0_seen | False |
| pre_last_checkpoint | cnss-netlink-only |
| safety_clear | True |

## Decision

corrected RC1 enumerate skipped: per_mgr_subsys_esoc0_not_observed

## Safety Scope

V1376 remains below Wi-Fi bring-up. It does not start Wi-Fi HAL, scan, connect, credential handling, DHCP/routes, or external ping. The intentional live mutation is limited to pci-msm debugfs `rc_sel=2` and `case=11` after the Android participant lower gate is observed.

## Next

repair late per_proxy/pm-service /dev/subsys_esoc0 gate before retry
