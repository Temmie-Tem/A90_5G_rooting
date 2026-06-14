# Native Init V1371 RC1 LTSSM Failure Classifier

## Summary

- Cycle: `V1371`
- Type: host-only RC1 LTSSM failure classifier
- Decision: `v1371-endpoint-readiness-gap-after-rc1-power-proven`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_rc1_ltssm_failure_classifier_v1371.py`
- Evidence:
  - `tmp/wifi/v1371-rc1-ltssm-failure-classifier/manifest.json`
  - `tmp/wifi/v1371-rc1-ltssm-failure-classifier/summary.md`

## Decision

V1370 proves the AP-side pcie1 RC path can execute corrected RC1 enumerate, enable power/clocks/PERST, reach PHY-ready, release endpoint reset, and enter LTSSM; unlike Android, it then stops in poll/compliance before L0 and creates no PCI/MHI device. Android reaches L0 only after the esoc0/provider path has started, so the next blocker is endpoint/SDX50M readiness at PERST release, not a missing pci-msm enumerate entry or upper Wi-Fi HAL path.

## Checks

| check | pass |
| --- | --- |
| android_esoc0_precedes_rc1_enable | true |
| android_reached_current_gen | true |
| android_reached_l0 | true |
| dts_mhi_esoc_link_present | true |
| dts_pcie1_contract_present | true |
| host_analysis_parks_upper_track | true |
| native_created_no_pci_or_mhi | true |
| native_device_health_clean | true |
| native_failed_before_l0 | true |
| native_no_esoc_provider_held_in_v1370 | true |
| native_reached_phy_ready | true |
| native_reached_poll_active_or_compliance | true |
| native_reached_rc1_enumerate | true |
| native_released_perst | true |
| source_case11_is_enumerate | true |
| source_enable_owns_perst_and_ltssm | true |
| source_enable_owns_pm_all | true |
| v1370_passed | true |

## Timeline Deltas

| field | seconds |
| --- | --- |
| android_esoc0_to_assert_sec | 0.254929 |
| android_assert_to_release_sec | 0.007196 |
| android_release_to_l0_sec | 0.016666 |
| native_assert_to_release_sec | 0.005788 |
| native_release_to_link_failed_sec | 0.109039 |
| native_release_to_poll_active_sec | 0.016445 |
| native_release_to_poll_compliance_sec | 0.042154 |

## Native V1370 Events

| event | time | text |
| --- | --- | --- |
| esoc0_get |  |  |
| test11 | 1394.038236 | [2:        busybox:  635] PCIe: TEST: 11 |
| assert_reset | 1394.038294 | [2:        busybox:  635] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1. |
| int_mask | 1394.041854 | [2:        busybox:  635] msm_pcie_enable: PCIe: RC1: PCIE20_PARF_INT_ALL_MASK: 0x7f80c202 |
| phy_ready | 1394.044068 | [2:        busybox:  635] msm_pcie_enable: PCIe RC1 PHY is ready! |
| release_reset | 1394.044082 | [2:        busybox:  635] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1. |
| detect_quiet_first | 1394.050256 | [2:        busybox:  635] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET |
| poll_active_first | 1394.060527 | [2:        busybox:  635] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE |
| poll_compliance_first | 1394.086236 | [2:        busybox:  635] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE |
| l0_first |  |  |
| link_initialized |  |  |
| current_gen |  |  |
| link_failed | 1394.153121 | [2:        busybox:  635] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3) |

## Android Reference Events

| event | time | text |
| --- | --- | --- |
| esoc0_get | 8.54144 | subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0 |
| test11 |  |  |
| assert_reset | 8.796369 | msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1. |
| int_mask | 8.801282 | msm_pcie_enable: PCIe: RC1: PCIE20_PARF_INT_ALL_MASK: 0x7f80c202 |
| phy_ready | 8.803556 | msm_pcie_enable: PCIe RC1 PHY is ready! |
| release_reset | 8.803565 | msm_pcie_enable: PCIe: Release the reset of endpoint of RC1. |
| detect_quiet_first | 8.809824 | msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET |
| poll_active_first |  |  |
| poll_compliance_first |  |  |
| l0_first | 8.820231 | msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_L0 |
| link_initialized | 8.820254 | msm_pcie_enable: PCIe RC1 link initialized |
| current_gen | 8.820459 | msm_pcie_enable: PCIe RC1 Current GEN2, 2 lanes |
| link_failed |  |  |

## pci-msm Source Map

| symbol | line |
| --- | --- |
| case11_calls_msm_pcie_enumerate | 1846 |
| msm_pcie_enumerate_calls_enable_pm_all | 5280 |
| msm_pcie_enable_entry | 4606 |
| assert_perst | 4632 |
| vreg_init | 4642 |
| clk_init | 4649 |
| pipe_clk_init | 4716 |
| release_perst | 4780 |
| enable_ltssm | 4827 |
| link_failed | 4856 |
| link_fail_cleanup | 4973 |

## DTS Facts

| fact | value |
| --- | --- |
| pcie1_node | qcom,pcie@1c08000 |
| pcie1_perst_gpio | TLMM102 |
| pcie1_wake_gpio | TLMM104 |
| pcie1_gdsc | pcie_1_gdsc |
| pcie1_vregs | pm8150l_l3, pm8150_l5, VDD_CX_LEVEL |
| pcie1_clocks | GCC_PCIE_1_* plus GCC_PCIE1_PHY_REFGEN_CLK |
| pcie1_ep_latency_ms | 10 |
| mdm3_provider | qcom,ext-sdx50m |
| mdm3_ap2mdm_status_gpio | TLMM135 |
| mdm3_mdm2ap_status_gpio | TLMM142 |
| mdm3_soft_reset_pon | PM8150L GPIO9 |
| mhi_esoc_link | mhi_0 esoc-0 -> mdm3 |

## V1372 Candidate

- Name: `provider-held-delayed-corrected-rc1-enumerate-proof`
- Scope: bounded live design candidate, not executed by V1371
- Rationale: match Android ordering: start/hold SDX50M provider path first, then trigger corrected RC1 enumerate after a short Android-derived delay

### Candidate Order

- preflight native selftest fail=0 and debugfs mount state
- start existing lower/provider path that holds /dev/subsys_esoc0 and toggles AP2MDM/PON
- wait near Android esoc0-to-RC1 interval or poll AP2MDM/PON readable state
- write only rc_sel=2 then case=11
- capture GPIO142, pcie1 LTSSM/L0, PCI/MHI, dmesg, cleanup and post-selftest

### Hard Stops

- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping
- no PERST assert/deassert debug cases
- no PMIC/GPIO/GDSC direct writes
- no eSoC notify or BOOT_DONE spoof
- no flash, boot image write, or partition write

## Safety

- V1371 is host-only and executes no device command.
- No debugfs write, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE`,
  Wi-Fi HAL, scan/connect, credential handling, DHCP/routes, external
  ping, flash, boot image write, or partition write occurred.

## Next

V1372 design a bounded provider-held plus delayed corrected-RC1 enumerate proof; do not start Wi-Fi HAL or network bring-up
