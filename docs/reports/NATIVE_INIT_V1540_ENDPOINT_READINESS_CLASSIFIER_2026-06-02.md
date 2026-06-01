# Native Init V1540 Endpoint Readiness Classifier

## Summary

- Cycle: `V1540`
- Type: host-only evidence/source classifier
- Decision: `v1540-endpoint-readiness-gap-after-sysfs-enumerate`
- Result: PASS
- Reason: sysfs/client enumerate and RC1 software enable are proven, but the SDX50M endpoint still does not respond before L0; next focus is endpoint electrical/readiness parity

## Inputs

| input | path |
| --- | --- |
| v1539_manifest | tmp/wifi/v1539-sysfs-enumerate-result-classifier/manifest.json |
| v1538_dmesg | tmp/wifi/v1538-wifi-sysfs-client-enumerate-handoff/test-v1393-dmesg.stdout.txt |
| v1538_window | tmp/wifi/v1538-wifi-sysfs-client-enumerate-handoff/test-rc1-window-result.stdout.txt |
| android_v852_dmesg | tmp/wifi/v852-android-ext-mdm-provider-surface-handoff/v852-android-ext-mdm-provider-surface-run/android/commands/dmesg-focus.txt |
| android_v852_interrupts | tmp/wifi/v852-android-ext-mdm-provider-surface-handoff/v852-android-ext-mdm-provider-surface-run/android/commands/interrupts-focus.txt |
| pcie_dtsi | kernel_build/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/qcom/sm8150-pcie.dtsi |
| sdx50m_dtsi | kernel_build/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/qcom/sm8150-sdx50m.dtsi |
| external_soc_dtsi | kernel_build/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/qcom/sdx5xm-external-soc.dtsi |
| mhi_dtsi | kernel_build/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/qcom/sm8150-mhi.dtsi |
| pci_msm_source | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/pci/host/pci-msm.c |

## Fixed-Point Checks

| check | value |
| --- | --- |
| v1539-fixed-point-pass | True |
| pcie1-dts-contract-present | True |
| sdx50m-esoc-mhi-contract-present | True |
| pci-msm-enable-sequence-present | True |
| native-v1538-rc1-reaches-link-training | True |
| native-v1538-fails-before-l0 | True |
| native-v1538-no-endpoint-response | True |
| android-good-has-l0-and-downstream | True |

## Endpoint Candidate Classification

| candidate | status | basis |
| --- | --- | --- |
| AP-side enumerate caller | closed | V1538 sysfs/client enumerate write succeeded and still failed before L0. |
| RC1 software enable path | partially healthy | V1538 reaches PERST assert/release, PHY ready, and LTSSM polling/compliance. |
| SDX50M endpoint response | active blocker | No L0, no GPIO142 IRQ/level, no MHI/WLFW/BDF/wlan0 after RC1 link training starts. |
| PERST/refclk/GDSC/electrical parity | next focus | DTS ties RC1 to GPIO102 PERST, GPIO104 WAKE, pcie_1_gdsc, clkref/refgen; V1538 samples keep pcie1 GDSC at 0mV and GPIO102/135/142 low. |
| firmware/MHI/WLFW | deferred | No native L0 or PCI device exists, so these remain downstream. |
| Wi-Fi HAL / scan / connect | blocked downstream | wlan0 is absent; credentials, DHCP/routes, and external ping remain out of scope. |

## RC1 / SDX50M Source Contract

| fact | value |
| --- | --- |
| pcie1 node lines | 286-551 |
| PERST | perst-gpio = <&tlmm 102 0>; |
| WAKE | wake-gpio = <&tlmm 104 0>; |
| GDSC | gdsc-vdd-supply = <&pcie_1_gdsc>; |
| vreg 1.8 / 0.9 | vreg-1.8-supply = <&pm8150l_l3>; / vreg-0.9-supply = <&pm8150_l5>; |
| clkref/refgen/pipe | True/True/True |
| boot option / ep latency | qcom,boot-option = <0x1>; / qcom,ep-latency = <10>; |
| MHI endpoint | pci-ids = "17cb:0305", "17cb:0306", "17cb:0307", "17cb:0308"; / mhi,name = "esoc0"; |
| AP2MDM / MDM2AP / PON | qcom,ap2mdm-status-gpio   = <&tlmm 135 0x00>; / qcom,mdm2ap-status-gpio   = <&tlmm 142 0x00>; / qcom,ap2mdm-soft-reset-gpio = <&pm8150l_gpios 9 0>; |

## pci-msm Enable Order

| event | present |
| --- | --- |
| assert PERST | True |
| enable vreg | True |
| enable clk | True |
| init phy | True |
| enable pipe clock | True |
| wait PHY ready | True |
| release PERST | True |
| enable LTSSM | True |
| poll link | True |
| reassert PERST on fail | True |

## Android-Good vs Native-Fail

| field | Android V852 | Native V1538 |
| --- | --- | --- |
| esoc0 timestamp | 8.54144 | 9.113747 |
| RC1 assert | 8.796369 | 9.142666 |
| RC1 release | 8.803565 | 9.148485 |
| RC1 L0 | 8.820231 | False |
| Current GEN | 8.820459 |  |
| poll compliance |  | 9.190637 |
| link failed |  | 9.25745 |
| GPIO142 IRQ total/max | 1 | 0 |
| MHI/WLFW/BDF/wlan0 | 8.392748/9.489583/14.812872 | False |

## Native V1538 Window Signals

| signal | value |
| --- | --- |
| GPIO102/PERST sample max | 0 |
| GPIO103/CLKREQ sample max | 1 |
| GPIO104/WAKE sample max | 0 |
| GPIO104 IRQ max | 0 |
| GPIO135/AP2MDM sample max | 0 |
| GPIO142/MDM2AP sample max | 0 |
| GPIO142 IRQ max | 0 |
| pcie1 GDSC samples/nonzero | 11/False |

## Key Native V1538 Dmesg Lines

- `[    9.113747] [3:   Binder:591_3:  612] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[    9.113761] [3:   Binder:591_3:  612] subsys-restart: __subsystem_get(): Changing subsys fw_name to esoc0`
- `[    9.142666] [1:           init:  620] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.148471] [1:           init:  620] msm_pcie_enable: PCIe RC1 PHY is ready!`
- `[    9.148485] [1:           init:  620] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[    9.154660] [1:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.159796] [1:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.164934] [1:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.170072] [1:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.175208] [1:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.180364] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.185502] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.190637] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.195773] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.200910] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.206045] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.211184] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.216320] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.221458] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.226596] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.231732] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.236868] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.242008] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.247144] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.252281] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.257417] [2:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.257432] [2:           init:  620] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.257450] [2:           init:  620] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3)`
- `[    9.257755] [2:           init:  620] msm_pcie_enumerate: PCIe: failed to enable RC1.`

## Key Native V1538 Window Lines

- `rc1_micro_writer_summary pid=620 writer_wait_rc=0 status=0x0 micro_writer rc=0 errno=0 trigger_mode=sysfs_client_enumerate sysfs_path=/sys/devices/platform/soc/1c08000.qcom,pcie/debug/enumerate sysfs_rc=0 sysfs_elapsed_ms=7481 rc_sel_elapsed_ms=-1 case`
- `sample=case_aligned_micro_after_case_0ms source=micro_interrupts match_00=252: 0 0 0 0 0 0 0 0 msmgpio-dc 104 Edge msm_pcie_wake`
- `sample=case_aligned_micro_after_case_0ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_01= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_02= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_03= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_debug_gpio match_04= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_0ms source=micro_critical_regulator match_05= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_1ms source=micro_interrupts match_00=252: 0 0 0 0 0 0 0 0 msmgpio-dc 104 Edge msm_pcie_wake`
- `sample=case_aligned_micro_after_case_1ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_01= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_02= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_03= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_debug_gpio match_04= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_1ms source=micro_critical_regulator match_05= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_2ms source=micro_interrupts match_00=252: 0 0 0 0 0 0 0 0 msmgpio-dc 104 Edge msm_pcie_wake`
- `sample=case_aligned_micro_after_case_2ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_2ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`
- `sample=case_aligned_micro_after_case_2ms source=micro_debug_gpio match_01= gpio103 : in 1 2mA pull up`
- `sample=case_aligned_micro_after_case_2ms source=micro_debug_gpio match_02= gpio104 : in 0 2mA no pull`
- `sample=case_aligned_micro_after_case_2ms source=micro_debug_gpio match_03= gpio135 : out 0 16mA no pull`
- `sample=case_aligned_micro_after_case_2ms source=micro_debug_gpio match_04= gpio142 : in 0 8mA no pull`
- `sample=case_aligned_micro_after_case_2ms source=micro_critical_regulator match_05= pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV`
- `sample=case_aligned_micro_after_case_5ms source=micro_interrupts match_00=252: 0 0 0 0 0 0 0 0 msmgpio-dc 104 Edge msm_pcie_wake`
- `sample=case_aligned_micro_after_case_5ms source=micro_interrupts match_01=290: 0 0 0 0 0 0 0 0 msmgpio-dc 142 Edge mdm status`
- `sample=case_aligned_micro_after_case_5ms source=micro_debug_gpio match_00= gpio102 : out 0 2mA pull down`

## Key pci-msm Source Lines

| line | text |
| --- | --- |
| 84 | #define PCIE20_PARF_LTSSM              0x1B0 |
| 4606 | static int msm_pcie_enable(struct msm_pcie_dev_t *dev, u32 options) |
| 4632 | PCIE_INFO(dev, "PCIe: Assert the reset of endpoint of RC%d.\n", |
| 4642 | ret = msm_pcie_vreg_init(dev); |
| 4649 | ret = msm_pcie_clk_init(dev); |
| 4710 | pcie_phy_init(dev); |
| 4716 | ret = msm_pcie_pipe_clk_init(dev); |
| 4755 | PCIE_INFO(dev, "PCIe RC%d PHY is ready!\n", dev->rc_idx); |
| 4780 | PCIE_INFO(dev, "PCIe: Release the reset of endpoint of RC%d.\n", |
| 4827 | msm_pcie_write_mask(dev->parf + PCIE20_PARF_LTSSM, 0, BIT(8)); |
| 4840 | PCIE_INFO(dev, "PCIe RC%d: LTSSM_STATE: %s\n", |
| 4852 | PCIE_INFO(dev, "PCIe: Assert the reset of endpoint of RC%d.\n", |
| 4856 | PCIE_ERR(dev, "PCIe RC%d link initialization failed (LTSSM_STATE:0x%x)\n", |
| 5013 | PCIE_INFO(dev, "PCIe: Assert the reset of endpoint of RC%d.\n", |
| 7414 | while (((readl_relaxed(pcie_dev->parf + PCIE20_PARF_LTSSM) & |
| 8267 | ltssm_pre =  readl_relaxed(pcie_dev->parf + PCIE20_PARF_LTSSM); |
| 8268 | PCIE_INFO(pcie_dev, "PCIe RC%d: PARF LTSSM_STATE: %s\n", |
| 8294 | ltssm_post =  readl_relaxed(pcie_dev->parf + PCIE20_PARF_LTSSM); |
| 8295 | PCIE_INFO(pcie_dev, "PCIe RC%d: PARF LTSSM_STATE: %s\n", |

## Interpretation

V1540 fixes the active blocker below AP-side caller semantics. The kernel source shows `msm_pcie_enable()` asserts PERST, enables vregs/clocks/PHY/pipe clock, waits for PHY ready, releases PERST, enables LTSSM, then polls for link-up. V1538 reaches that sequence and fails at LTSSM poll/compliance without L0.

The next useful work is not another enumerate retry and not firmware/MHI/WLFW. The evidence now points at the endpoint readiness/electrical boundary: PERST/refclk/GDSC/CLKREQ/WAKE/AP2MDM/MDM2AP around the first RC1 link-training window. Until native L0 and PCI enumeration exist, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, firmware transfer, and MHI pipe work remain downstream.

## Next Gate

- Cycle: `V1541`
- Summary: source/build-only endpoint electrical observer design: sample PERST/refclk/GDSC/CLKREQ/WAKE/AP2MDM/MDM2AP in the exact RC1 link-training window without new writes
- Guardrail: do not repeat enumerate until a new endpoint input is identified
- Guardrail: no PMIC/GPIO/GDSC direct write
- Guardrail: no global PCI rescan or platform bind/unbind
- Guardrail: no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- Guardrail: no firmware/MHI/WLFW branch until native L0 and PCI enumeration exist

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind.
