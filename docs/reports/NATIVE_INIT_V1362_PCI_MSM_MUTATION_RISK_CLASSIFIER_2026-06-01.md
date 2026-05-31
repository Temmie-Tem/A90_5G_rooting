# Native Init V1362 pci-msm Mutation Risk Classifier

## Summary

- Cycle: `V1362`
- Type: host-only risk classifier
- Decision: `v1362-no-safe-userspace-pci-msm-mutation`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_pci_msm_mutation_risk_classifier_v1362.py`
- Evidence:
  - `tmp/wifi/v1362-pci-msm-mutation-risk-classifier/manifest.json`
  - `tmp/wifi/v1362-pci-msm-mutation-risk-classifier/summary.md`

## Decision

All remaining userspace mutations are either generic bus operations or proprietary pci-msm remove/probe lifecycles without source-level timeout/rollback proof. No RC1-specific, bounded, observable, rollback-safe userspace mutation is proven.

## Risk Table

| option | rc1_specific | risk | decision | reason |
| --- | --- | --- | --- | --- |
| platform unbind/bind pci-msm:1c08000 | partial | high | reject for live until a bounded rollback model exists | targets pcie1 device name but invokes proprietary pci-msm remove/probe lifecycle without source-level cleanup or timeout proof |
| platform drivers_probe for pci-msm | no | high | reject | generic bus reprobe; not tied to msm_pcie_enumerate(1) and cannot prove only pcie1 will be affected |
| global PCI rescan | no | high | reject | global PCI mutation with no RC1 scoping and no proof it powers pcie1 GDSC/refclk/PERST first |
| MHI client bind/unbind | no | closed | closed | V1361 proved MHI client drivers require existing mhi_device instances and are downstream of PCI enumeration |
| kernel-side msm_pcie_enumerate(1) shim | yes | unknown | next host-only feasibility track | matches the semantic operation but requires module/export/signing or kernel patch feasibility proof before live use |

## Checks

| check | pass |
| --- | --- |
| cnss2_calls_enumerate_but_wrong_branch | true |
| mhi_arch_needs_existing_pci_dev | true |
| msm_pcie_enumerate_declared_only | true |
| msm_pcie_enumerate_source_absent_from_osrc | true |
| pcie0_and_pcie1_share_pci_msm_driver | true |
| risk_table_has_no_live_mutation_selected | true |
| v1359_closed_icnss_dev_boot | true |
| v1360_live_has_pcie1_bound_no_pci_device | true |
| v1361_closed_mhi_client_surfaces | true |

## Source Facts

| fact | value |
| --- | --- |
| msm_pcie_enumerate_decl | int msm_pcie_enumerate(u32 rc_idx); |
| cnss2_enumerate_call | ret = msm_pcie_enumerate(rc_num); |
| pcie0_compatible | pcie0: qcom,pcie@1c00000 { |
| pcie1_compatible | pcie1: qcom,pcie@1c08000 { |
| mhi_pcie_resume | ret = msm_pcie_pm_control(MSM_PCIE_RESUME, pci_dev->bus->number, |

## Safety

- Host-only; no device command or live runtime access.
- No platform bind/unbind, PCI rescan, MHI bind/unbind, PMIC/GPIO/GDSC write,
  eSoC notify/`BOOT_DONE`, Wi-Fi HAL, scan/connect, credential handling,
  DHCP/routes, external ping, flash, boot image write, or partition write.

## Next

V1363 host-only kernel-side msm_pcie_enumerate(1) shim feasibility classifier
