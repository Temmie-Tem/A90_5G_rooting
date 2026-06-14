# Native Init V1387 Android Participant Pre-Poll Corrected RC1 Live

## Summary

- Cycle: `V1387`
- Type: bounded live lower Android participant + pre-poll corrected RC1 enumerate gate
- Decision: `v1387-corrected-rc1-ltssm-no-downstream-clean`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_android_participant_prepoll_corrected_rc1_live_v1387.py`
- Helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v285`)
- Evidence:
  - `tmp/wifi/v1387-android-participant-prepoll-corrected-rc1-live/manifest.json`
  - `tmp/wifi/v1387-android-participant-prepoll-corrected-rc1-live/summary.md`

## Key Observations

| field | value |
| --- | --- |
| private_flag_in_child_script | 1 |
| precondition_flag_in_child_script | 1 |
| corrected_rc1_flag_in_child_script | 1 |
| corrected_triggered | True |
| corrected_phase | late_per_proxy_prepoll_000 |
| corrected_monotonic_ms | 1963286 |
| corrected_gate_per_mgr_subsys_esoc0_count | 0 |
| corrected_gate_pm_service_powerup_thread_count | 1 |
| corrected_rc_sel_rc | 0 |
| corrected_case_rc | 0 |
| debugfs_control_write_executed | True |
| prepoll_triggered | True |
| prepoll_poll_count | 0 |
| prepoll_elapsed_ms | 119 |
| prepoll_last_gate_per_mgr_subsys_esoc0_count | 0 |
| prepoll_last_gate_pm_service_powerup_thread_count | 1 |
| timing_sample_count | 120 |
| timing_pm_service_powerup_seen | True |
| timing_pcie_rc1_transition_seen | False |
| dmesg_pcie_rc1_transition_seen | True |
| dmesg_esoc0_to_assert_sec | 3.560846999999967 |
| dmesg_release_to_link_failed_sec | 0.10884900000019115 |
| dmesg_l0_seen | False |
| dmesg_link_failed_seen | True |
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

pre-poll corrected RC1 enumerate fired from the v285 pre-poll gate (esoc0-to-assert 3.561s); dmesg shows RC1 LTSSM activity before link failure, but no GPIO142/PCI/MHI/WLFW/wlan0 appeared

## Safety Scope

V1387 remains below Wi-Fi bring-up. It does not start Wi-Fi HAL, scan, connect, credential handling, DHCP/routes, or external ping. The intentional live mutation is limited to pci-msm debugfs `rc_sel=2` and `case=11` from the helper v285 pre-poll gate when the Android participant lower gate and powerup-thread gate are observed.

## Next

compare V1387 action timing and LTSSM phase against Android before any new participant or lower-branch mutation

## Dmesg RC1 Lines

- `line_esoc0`: [ 1959.611261] [3:  Binder:9245_1: 9280] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0
- `line_test11`: [ 1963.172090] [7:a90_android_exe: 1174] PCIe: TEST: 11
- `line_assert`: [ 1963.172108] [7:a90_android_exe: 1174] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.
- `line_phy_ready`: [ 1963.177544] [7:a90_android_exe: 1174] msm_pcie_enable: PCIe RC1 PHY is ready!
- `line_release`: [ 1963.177548] [7:a90_android_exe: 1174] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.
- `line_poll_compliance`: [ 1963.219517] [5:a90_android_exe: 1174] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE
- `line_link_failed`: [ 1963.286397] [1:a90_android_exe: 1174] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3)
