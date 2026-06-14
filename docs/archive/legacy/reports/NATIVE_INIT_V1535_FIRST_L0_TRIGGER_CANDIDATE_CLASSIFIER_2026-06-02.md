# Native Init V1535 First-L0 Trigger Candidate Classifier

## Summary

- Cycle: `V1535`
- Type: host-only evidence/source classifier
- Decision: `v1535-first-l0-candidates-narrowed-to-client-enumerate-or-endpoint-readiness`
- Result: PASS
- Reason: PM route, MHI PM-resume, ICNSS workqueue, probe enumeration, and repeated TEST:11 are closed as immediate first-L0 leads; only sysfs/client enumerate remains as an AP-side empirical check before endpoint readiness/electrical focus

## Inputs

| input | path |
| --- | --- |
| v1496 | tmp/wifi/v1496-wifi-rc1-window-short-hold-handoff/manifest.json |
| v1517 | tmp/wifi/v1517-wifi-critical-source-pre-l0-handoff/manifest.json |
| v1523 | tmp/wifi/v1523-msm-pcie-test11-vs-normal-path-classifier/manifest.json |
| v1524 | tmp/wifi/v1524-endpoint-trigger-attribution-classifier/manifest.json |
| v1525 | tmp/wifi/v1525-mhi-pm-resume-position-classifier/manifest.json |
| v1527 | tmp/wifi/v1527-android-initial-rc1-trigger-handoff/manifest.json |
| v1529 | tmp/wifi/v1529-android-tracefs-rc1-event-handoff/manifest.json |
| v1532 | tmp/wifi/v1532-android-targeted-tracefs-queue-pair-handoff/manifest.json |
| v1533 | tmp/wifi/v1533-v1532-queue-pair-classifier/manifest.json |
| v1534 | tmp/wifi/v1534-pm-route-first-l0-focus-classifier/manifest.json |
| pcie_source | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/pci/host/pci-msm.c |
| android_v852_dmesg | tmp/wifi/v852-android-ext-mdm-provider-surface-handoff/v852-android-ext-mdm-provider-surface-run/android/commands/dmesg-focus.txt |
| native_v1496_dmesg | tmp/wifi/v1496-wifi-rc1-window-short-hold-handoff/test-v1393-dmesg.stdout.txt |
| native_v1517_dmesg | tmp/wifi/v1517-wifi-critical-source-pre-l0-handoff/test-v1393-dmesg.stdout.txt |
| android_v1527_gpio_samples | tmp/wifi/v1527-android-initial-rc1-trigger-handoff/android-postfs-evidence/a90-v1527-rc1-trigger-sampler/irq-gpio-samples.log |
| android_v1529_tracefs | tmp/wifi/v1529-android-tracefs-rc1-event-handoff/android-postfs-evidence/a90-v1529-tracefs-rc1-sampler/tracefs-events.txt |
| android_v1532_tracefs | tmp/wifi/v1532-android-targeted-tracefs-queue-pair-handoff/android-postfs-evidence/a90-v1532-tracefs-queue-pair-sampler/tracefs-events.txt |

## Fixed-Point Checks

| check | value |
| --- | --- |
| v1534-first-l0-focus-fixed | True |
| v1496-native-rc1-progress-no-l0 | True |
| v1517-native-rc1-progress-no-l0 | True |
| v1523-common-enumerate-fixed | True |
| v1525-mhi-pm-resume-closed | True |
| v1533-icnss-workqueue-closed | True |
| android-good-initial-l0-reference | True |
| native-test11-fails-before-l0 | True |
| source-normal-callers-present | True |
| android-wake-irq-not-proven | True |

## Candidate Classification

| candidate | status | basis |
| --- | --- | --- |
| current PM/eSoC route | closed as active gap | V1534 proves current route reaches pm-service/esoc0 and mdm_subsys_powerup; remaining failure is below provider entry. |
| debugfs TEST:11 enumerate | known native fail | V1496/V1517 reach RC1/LTSSM through TEST:11 but fail before L0. |
| MHI PM-resume | closed downstream | V1525 places MHI PM-resume after first L0/PCI device creation. |
| ICNSS workqueue | closed non-trigger | V1533 pairs visible icnss_driver_event_work with macloader driver load, not first L0. |
| probe-time enumeration | not active on this board | V1523/source shows pcie1 qcom,boot-option defers probe enumeration. |
| endpoint wake GPIO104 | source-valid but evidence-weak | pci-msm wake work can call msm_pcie_enumerate, but V1527 GPIO104 samples stay zero and V1529/V1532 tracefs exposes no IRQ/RC1 text. |
| sysfs/client enumerate | only remaining AP-side testable trigger | source-valid caller into the same msm_pcie_enumerate path; Android does not log the caller, so a bounded rollbackable test can empirically close it. |
| endpoint electrical/readiness | primary technical blocker if client enumerate also fails | Native can drive LTSSM to polling/compliance but endpoint never reaches L0. |

## Android-Good vs Native-Fail Evidence

| field | Android V852 | Native V1496 | Native V1517 |
| --- | --- | --- | --- |
| RC1 progress | 8.796369 | True | True |
| RC1 L0 | 8.820231 | False | False |
| link failed |  | True | True |
| debugfs TEST marker | False |  | True |
| MHI/WLFW/wlan0 | 9.489583/14.812872 |  | False |

## Android GPIO/Tracefs Visibility

| field | value |
| --- | --- |
| V1527 GPIO104 IRQ samples/max | 320/0 |
| V1527 GPIO142 IRQ samples/max | 320/0 |
| V1527 GPIO135 level samples/max | 320/0 |
| V1527 GPIO142 level samples/max | 320/0 |
| V1529 tracefs has RC1 text | False |
| V1532 tracefs has RC1 text | False |
| V1529 tracefs has IRQ events | False |
| V1532 tracefs has IRQ events | False |

## Source Facts

| fact | value |
| --- | --- |
| pcie source | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/pci/host/pci-msm.c |
| TEST:11 calls enumerate | True |
| enumerate calls PM_ALL enable | True |
| enumerate calls PCI scan | True |
| sysfs enumerate calls enumerate | True |
| endpoint wake work calls enumerate | True |
| probe checks no-probe enum | True |

## Key Android V852 Lines

- `[    8.392748] cnss-daemon wlfw_start: Starting`
- `[    8.541440] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[    8.541459] subsys-restart: __subsystem_get(): Changing subsys fw_name to esoc0`
- `[    8.796369] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    8.803565] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[    8.809824] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    8.815074] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    8.820231] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_L0`
- `[    8.820459] msm_pcie_enable: PCIe RC1 Current GEN2, 2 lanes`
- `[    9.489583] cnss-daemon wlfw_send_bdf_download_req: BDF file : regdb.bin`
- `[    9.510994] cnss-daemon wlfw_send_bdf_download_req: BDF file : bdwlan.bin`
- `[   11.420584] msm_pcie_pm_suspend: PCIe RC1: PARF LTSSM_STATE: LTSSM_L1_IDLE`
- `[   11.420808] msm_pcie_pm_suspend: PCIe RC1: PARF LTSSM_STATE: LTSSM_L2_IDLE`
- `[   11.420818] msm_pcie_disable: PCIe: Assert the reset of endpoint of RC1.`
- `[   11.421060] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[   11.426497] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[   11.432653] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[   11.437771] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[   11.442894] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_L0`
- `[   11.443015] msm_pcie_enable: PCIe RC1 Current GEN3, 2 lanes`
- `[   11.880634] msm_pcie_pm_suspend: PCIe RC1: PARF LTSSM_STATE: LTSSM_L1_IDLE`
- `[   11.890069] msm_pcie_pm_suspend: PCIe RC1: PARF LTSSM_STATE: LTSSM_L2_IDLE`
- `[   11.890085] msm_pcie_disable: PCIe: Assert the reset of endpoint of RC1.`
- `[   11.890822] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[   11.896704] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[   11.902913] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[   11.908063] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[   11.913218] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_L0`

## Key Native V1517 Lines

- `[    9.190933] [2:   Binder:594_3:  615] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[    9.190947] [2:   Binder:594_3:  615] subsys-restart: __subsystem_get(): Changing subsys fw_name to esoc0`
- `[    9.226916] [2:           init:  623] PCIe: TEST: 11`
- `[    9.226972] [2:           init:  623] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.230544] [2:           init:  623] msm_pcie_enable: PCIe: RC1: PCIE20_PARF_INT_ALL_MASK: 0x7f80c202`
- `[    9.232764] [2:           init:  623] msm_pcie_enable: PCIe RC1 PHY is ready!`
- `[    9.232779] [2:           init:  623] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[    9.238956] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.244097] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.249233] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.254369] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.259505] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.264644] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.269779] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.274917] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.280068] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.285203] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.290340] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.295476] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.300613] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.305749] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.310885] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.316049] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.321186] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.326323] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.331460] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.336596] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.341733] [2:           init:  623] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`

## Key pci-msm Callsite Lines

| line | text |
| --- | --- |
| 395 | MSM_PCIE_NO_PROBE_ENUMERATION = BIT(0), |
| 396 | MSM_PCIE_NO_WAKE_ENUMERATION = BIT(1) |
| 1846 | case MSM_PCIE_ENUMERATION: |
| 1853 | if (!msm_pcie_enumerate(dev->rc_idx)) |
| 2419 | msm_pcie_enumerate(pcie_dev->rc_idx); |
| 5424 | EXPORT_SYMBOL(msm_pcie_enumerate); |
| 5466 | "PCIe: Start enumeration for RC%d upon the wake from endpoint.\n", |
| 5469 | ret = msm_pcie_enumerate(dev->rc_idx); |
| 5878 | MSM_PCIE_NO_WAKE_ENUMERATION)) { |
| 7224 | MSM_PCIE_NO_PROBE_ENUMERATION) { |
| 7232 | ret = msm_pcie_enumerate(rc_idx); |

## Interpretation

V1535 keeps the active blocker at first L0. PM-service/eSoC actionability is no longer the lowest blocker, and MHI, WLFW, BDF, firmware inventory, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping remain downstream until native RC1 reaches L0 and a PCI device exists.

The only AP-side trigger still worth an empirical close-out is the targeted sysfs/client enumerate entry into `msm_pcie_enumerate()`. The source says it converges on the same common enumerate function as TEST:11, so a failure there would move the next focus away from AP-side caller semantics and toward endpoint readiness: PERST/refclk/reset/electrical response around the SDX50M endpoint.

## Next Gate

- Cycle: `V1536`
- Summary: source/build-only rollbackable test-boot variant that replaces debugfs TEST:11 with the targeted pci-msm sysfs/client enumerate entry, then samples the same RC1/LTSSM/L0 outcome
- Guardrail: target only the pci-msm RC1 enumerate sysfs/client entry; no global PCI rescan
- Guardrail: no platform bind/unbind
- Guardrail: no Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, or external ping
- Guardrail: no PMIC/GPIO/GDSC direct writes and no eSoC notify/BOOT_DONE spoof
- Guardrail: rollbackable handoff with native selftest verification before any live run

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
