# Native Init V1354 pcie1 RC Power Observer Live

## Summary

- Cycle: `V1354`
- Type: bounded live lower-response timing sampler
- Decision: `v1354-current-route-pcie1-rc-stayed-off`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1354-pcie1-rc-power-observer-live/manifest.json`
  - `tmp/wifi/v1354-pcie1-rc-power-observer-live/summary.md`
- Script: `scripts/revalidation/native_wifi_pcie1_rc_power_observer_live_v1354.py`
- Helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v281`)

## Key Observations

| field | value |
| --- | --- |
| private_flag_in_child_script | 1 |
| private_cnss_bind_rc | 0 |
| private_cnss_expected_c_string | SDX50M |
| timing_sample_count | 120 |
| timing_pm_service_powerup_seen | True |
| timing_gpio142_irq_delta | 0 |
| timing_errfatal_irq_delta | 0 |
| timing_pcie_rc1_transition_seen | False |
| timing_pcie1_gdsc_seen | True |
| timing_pcie1_gdsc_nonzero_seen | False |
| timing_pcie1_gdsc_initial | pcie_1_gdsc                      0    2      0     0mV     0mA     0mV     0mV |
| timing_pcie1_gdsc_last | pcie_1_gdsc                      0    2      0     0mV     0mA     0mV     0mV |
| timing_pcie1_clkref_seen | True |
| timing_pcie1_clkref_initial | gcc_pcie_1_clkref_clk                0        0        0           0          0 50000 |
| timing_pcie1_clkref_last | gcc_pcie_1_clkref_clk                0        0        0           0          0 50000 |
| timing_pcie1_phy_refgen_seen | True |
| timing_pcie1_phy_refgen_initial | gcc_pcie_phy_refgen_clk_src       0        0 19200000           0          0 50000 |
| timing_pcie1_phy_refgen_last | gcc_pcie_phy_refgen_clk_src       0        0 19200000           0          0 50000 |
| timing_pcie1_pipe_clk_seen | True |
| timing_pcie1_pipe_clk_initial | gcc_pcie_1_pipe_clk                  0        0        0           0          0 50000 |
| timing_pcie1_pipe_clk_last | gcc_pcie_1_pipe_clk                  0        0        0           0          0 50000 |
| timing_gpio102_perst_seen | True |
| timing_gpio102_perst_initial | gpio102 : out 0 2mA pull down |
| timing_gpio102_perst_last | gpio102 : out 0 2mA pull down |
| timing_gpio103_clkreq_seen | True |
| timing_gpio103_clkreq_initial | gpio103 : in  1 2mA pull up |
| timing_gpio103_clkreq_last | gpio103 : in  1 2mA pull up |
| timing_gpio104_wake_seen | True |
| timing_gpio104_wake_initial | gpio104 : in  0 2mA no pull |
| timing_gpio104_wake_last | gpio104 : in  0 2mA no pull |
| timing_pci_dev_max | 0 |
| timing_mhi_bus_max | 0 |
| timing_mhi_pipe_seen | False |
| timing_mhi_pipe_fd_max | 0 |
| timing_ks_process_max | 0 |
| timing_wlfw_kmsg_max | 0 |
| timing_wlan0_seen | False |
| timing_safety_clear | True |

## Cleanup And Health

| field | value |
| --- | --- |
| debugfs_mounted_before | False |
| debugfs_mounted_by_cycle | True |
| debugfs_cleanup_attempted | True |
| debugfs_mounted_after | False |
| reboot_cleanup_status_healthy | True |
| reboot_cleanup_version_seen | True |
| reboot_cleanup_wait_sec | 47.348 |
| post_status_ok | True |
| post_selftest_ok | True |
| post_selftest_payload | selftest: pass=11 warn=1 fail=0 duration=42ms entries=12 |

## Decision

current private SDX50M route reached mdm_subsys_powerup, but pcie1 RC stayed off: pcie_1_gdsc remained 0mV, PERST stayed low, and no PCI/MHI/WLFW/wlan0 transition appeared

V1354 remains below Wi-Fi bring-up. It does not start Wi-Fi HAL, scan,
connect, credential handling, DHCP/routes, or external ping.

## Next

classify PM8150L GPIO9 PON parity, then design a bounded pcie1 RC enable experiment only if PON parity is healthy
