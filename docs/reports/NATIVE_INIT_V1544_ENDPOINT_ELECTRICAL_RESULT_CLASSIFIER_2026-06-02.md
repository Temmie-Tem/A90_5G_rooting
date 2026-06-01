# Native Init V1544 Endpoint Electrical Result Classifier

## Summary

- Cycle: `V1544`
- Type: host-only evidence classifier
- Decision: `v1544-endpoint-electrical-confirms-no-l0-gpio-gdsc-zero-clk-postfail`
- Result: PASS
- Reason: V1543 confirms the no-L0 endpoint gap and captures GPIO/GDSC/clock evidence; focused clk_summary lines are disabled but too slow to prove the pre-fail sub-120ms clock state

## Inputs

| input | path |
| --- | --- |
| manifest | tmp/wifi/v1543-endpoint-electrical-handoff/manifest.json |
| dmesg | tmp/wifi/v1543-endpoint-electrical-handoff/test-v1393-dmesg.stdout.txt |
| window | tmp/wifi/v1543-endpoint-electrical-handoff/test-rc1-window-result.stdout.txt |
| wlan0 | tmp/wifi/v1543-endpoint-electrical-handoff/test-wlan0.stdout.txt |
| v1542_manifest | tmp/wifi/v1542-endpoint-electrical-artifact-sanity/manifest.json |
| v1540_manifest | tmp/wifi/v1540-endpoint-readiness-classifier/manifest.json |

## Fixed-Point Checks

| check | value |
| --- | --- |
| v1542-artifact-sanity-pass | True |
| v1543-handoff-and-rollback-pass | True |
| v1543-sysfs-write-ok | True |
| v1543-fixed-rc1-no-l0 | True |
| v1543-no-downstream | True |
| v1543-fast-gpio-no-endpoint-response | True |
| v1543-gdsc-zero-observed | True |
| v1543-focused-clock-lines-present | True |
| v1543-focused-clock-lines-disabled | True |
| v1543-clk-summary-too-slow-for-pre-fail-proof | True |

## RC1 Outcome

| field | value |
| --- | --- |
| RC1 assert / PHY ready / release | 9.293641 / 9.299422 / 9.299437 |
| poll compliance / link failed | 9.341574 / 9.408385 |
| L0 | False |
| MHI/WLFW/wlan0 dmesg text | False |
| wlan0 absent output | True |

## Endpoint Electrical Summary

| field | value |
| --- | --- |
| GPIO102 max | 0 |
| GPIO103 max | 1 |
| GPIO104 max / IRQ max | 0 / 0 |
| GPIO135 max | 0 |
| GPIO142 max / IRQ max | 0 / 0 |
| pcie_1_gdsc zero lines | 20 |
| focused clk first begin micro ms | 117 |
| focused clk max duration ms | 2009 |

## Focused Clock Lines

| clock | lines | disabled | example |
| --- | --- | --- | --- |
| gcc_pcie_1_pipe_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_pipe_clk match= gcc_pcie_1_pipe_clk 0 0 0 0 0 50000 |
| gcc_pcie_1_clkref_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_clkref_clk match= gcc_pcie_1_clkref_clk 0 0 0 0 0 50000 |
| gcc_pcie_1_cfg_ahb_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_cfg_ahb_clk match= gcc_pcie_1_cfg_ahb_clk 0 0 0 0 0 50000 |
| gcc_pcie_1_mstr_axi_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_mstr_axi_clk match= gcc_pcie_1_mstr_axi_clk 0 0 0 0 0 50000 |
| gcc_pcie_1_slv_axi_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_slv_axi_clk match= gcc_pcie_1_slv_axi_clk 0 0 0 0 0 50000 |
| gcc_pcie_1_slv_q2a_axi_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_slv_q2a_axi_clk match= gcc_pcie_1_slv_q2a_axi_clk 0 0 0 0 0 50000 |
| gcc_pcie1_phy_refgen_clk | 10 | True | sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie1_phy_refgen_clk match= gcc_pcie1_phy_refgen_clk 0 0 19200000 0 0 50000 |

## Key Dmesg Lines

- `[    9.293641] [3:           init:  623] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.299422] [3:           init:  623] msm_pcie_enable: PCIe RC1 PHY is ready!`
- `[    9.299437] [3:           init:  623] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[    9.305617] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.310757] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.315893] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.321029] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.326163] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.331301] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.336437] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.341574] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.346710] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.351845] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.356981] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.362120] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.367257] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.372395] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.377532] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.382669] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.387806] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.392942] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.398078] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.403216] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.408352] [3:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.408367] [3:           init:  623] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.408385] [3:           init:  623] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3)`
- `[    9.408682] [3:           init:  623] msm_pcie_enumerate: PCIe: failed to enable RC1.`

## Key Window Lines

- `rc1_micro_writer_summary pid=623 writer_wait_rc=0 status=0x0 micro_writer rc=0 errno=0 trigger_mode=sysfs_client_enumerate sysfs_path=/sys/devices/platform/soc/1c08000.qcom,pcie/debug/enumerate sysfs_rc=0 sysfs_elapsed_ms=7542 rc_sel_elapsed_ms=-1 case`
- `sample=case_aligned_micro_after_case_0ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_01= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_02= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_03= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_04= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_critical_regulator match_05= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_regulator needle=pcie_1_gdsc match= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_clk source_timing=begin elapsed_ms=7661 micro_elapsed_ms=117 source_duration_ms=-1 path=/sys/kernel/debug/clk/clk_summary`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_pipe_clk match= gcc_pcie_1_pipe_clk 0 0 0 0 0 50000`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie_1_clkref_clk match= gcc_pcie_1_clkref_clk 0 0 0 0 0 50000`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_clk needle=gcc_pcie1_phy_refgen_clk match= gcc_pcie1_phy_refgen_clk 0 0 19200000 0 0 50000`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_clk source_timing=end elapsed_ms=8559 micro_elapsed_ms=1015 source_duration_ms=898 path=/sys/kernel/debug/clk/clk_summary`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_debug_gpio needle=gpio102 match= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_debug_gpio needle=gpio103 match= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_debug_gpio needle=gpio104 match= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_debug_gpio needle=gpio135 match= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_focused_debug_gpio needle=gpio142 match= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_01= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_02= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_03= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_04= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_critical_regulator match_05= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_regulator needle=pcie_1_gdsc match= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_clk source_timing=begin elapsed_ms=8672 micro_elapsed_ms=1128 source_duration_ms=-1 path=/sys/kernel/debug/clk/clk_summary`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_clk needle=gcc_pcie_1_pipe_clk match= gcc_pcie_1_pipe_clk 0 0 0 0 0 50000`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_clk needle=gcc_pcie_1_clkref_clk match= gcc_pcie_1_clkref_clk 0 0 0 0 0 50000`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_clk needle=gcc_pcie1_phy_refgen_clk match= gcc_pcie1_phy_refgen_clk 0 0 19200000 0 0 50000`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_clk source_timing=end elapsed_ms=9570 micro_elapsed_ms=2026 source_duration_ms=898 path=/sys/kernel/debug/clk/clk_summary`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_debug_gpio needle=gpio102 match= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_debug_gpio needle=gpio103 match= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_debug_gpio needle=gpio104 match= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_focused_debug_gpio needle=gpio135 match= gpio135 : out 0 16mA no pull`

## Interpretation

V1543 confirms the V1540 endpoint-readiness model under a live rollbackable handoff. The sysfs/client enumerate write still reaches RC1 PHY/LTSSM and fails before L0. GPIO104/WAKE and GPIO142/MDM2AP remain low with zero IRQ count, `pcie_1_gdsc` remains 0mV in captured regulator lines, and no MHI/WLFW/BDF/FW-ready/`wlan0` appears.

The new micro-focused `clk_summary` evidence is useful but not definitive for the sub-120ms pre-fail clock state: the first focused clock read begins at about +117ms and each full `clk_summary` read takes hundreds of milliseconds. Therefore it proves the captured/post-fail focused clock lines are disabled, but it should not be treated as a precise pre-fail clock transition trace.

## Next Gate

- Cycle: `V1545`
- Summary: host/source classifier for a low-overhead pre-fail endpoint-state observer that does not read full clk_summary inside the sub-120ms RC1 window
- Guardrail: no new enumerate retry until the observer contract is narrower than V1543
- Guardrail: no PMIC/GPIO/GDSC direct write
- Guardrail: no global PCI rescan or platform bind/unbind
- Guardrail: no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- Guardrail: no firmware/MHI/WLFW branch until native L0 and PCI enumeration exist

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind.
