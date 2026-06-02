# Native Init V1641 Rail / Control Inventory

## Summary

- Cycle: `V1641`
- Type: host-only rail/control inventory classifier
- Decision: `v1641-no-safe-live-write-target-host-inventory-pass`
- Result: PASS
- Reason: no named safe live write target is currently justified; the only remaining candidate is an unowned SDX50M main-rail / bootloader-PMIC prerequisite.

## Inventory

| candidate | class | write surface | allowed next action |
|---|---|---|---|
| PM8150L GPIO9/PON | closed-reject-direct-write | userspace GPIO line request/hold rejected | read-only/source only |
| GPIO135/AP2MDM | closed-reject-direct-write | reject direct TLMM GPIO write | observe only |
| GPIO142/MDM2AP | observe-only-response-input | none | observe IRQ/level only |
| GPIO141/errfatal | observe-only-response-input | none | observe IRQ only |
| pcie1 GDSC / clocks / refclk / PERST | diagnostic-not-primary-write-target | reject blind debugfs/sysfs enable or pci-msm case write | source/static ownership analysis or read-only snapshot only |
| unknown SDX50M main rail / bootloader PMIC default | candidate-unowned-not-writeable-yet | unknown; no safe live write target identified | host-only artifact/source owner search before any live preflight |

## Key Evidence

### PM8150L GPIO9/PON

- class: `closed-reject-direct-write`
- evidence: V1276/V1355/V1639 show parity-correct kernel-owned PON path; provider source drives it naturally.
- rollback risk: high if misused; can hold modem reset line incorrectly
- checks: `{"v1276_out_high_parity": true, "v1355_pulse_parity": true, "v1639_source_order": true}`

### GPIO135/AP2MDM

- class: `closed-reject-direct-write`
- evidence: Natural provider path reaches AP2MDM; direct write would bypass eSoC semantics.
- rollback risk: high; can invert provider ordering
- checks: `{"source_ap2mdm_after_sleep": true, "v1639_ap2mdm_seen": true}`

### GPIO142/MDM2AP

- class: `observe-only-response-input`
- evidence: V1638/V1639 collect IRQ delta 0; this is the discriminator, not a control.
- rollback risk: n/a
- checks: `{"v1244_android_positive_contrast": true, "v1639_gpio142_zero": true}`

### GPIO141/errfatal

- class: `observe-only-response-input`
- evidence: V1638/V1639 collect errfatal IRQ delta 0; it can identify modem crash/fatal response only.
- rollback risk: n/a
- checks: `{"v1639_errfatal_zero": true}`

### pcie1 GDSC / clocks / refclk / PERST

- class: `diagnostic-not-primary-write-target`
- evidence: Prior forced-RC1 work proves AP-side PCIe can move, but natural-path MDM2AP remains the current discriminator; blind GDSC/RC1 writes contaminate the contract.
- rollback risk: medium/high; can reset transport or train dead endpoint
- checks: `{"dtb_pcie1_present": true, "v1306_gdsc_gap": true, "v1640_reject_blind_gdsc": true}`

### unknown SDX50M main rail / bootloader PMIC default

- class: `candidate-unowned-not-writeable-yet`
- evidence: eSoC provider has no regulator code, DTB has no mdm3 regulator supply, and no repo bootloader/PMIC config artifact currently names the rail.
- rollback risk: high until owner and voltage constraints are known
- checks: `{"bootloader_pmic_binary_hits": [], "dtb_no_differential": true, "pon_report_no_regulator": true, "provider_regulator_code_absent": true}`

## Source / Artifact Notes

- eSoC provider has regulator code: `False`
- limited bootloader/PMIC binary artifact hits: `0`
- Artifact scan is intentionally bounded and excludes source subtrees to avoid broad/OOM-prone searches.

## Decision

No safe live PMIC/GPIO/GDSC write target is identified by current evidence. PMIC GPIO9/PON and GPIO135/AP2MDM are closed as direct userspace write targets; GPIO142 and errfatal are observe-only; pcie1 GDSC/clocks/refclk are diagnostic and must not be blind-enabled from this state. The remaining candidate is an unnamed SDX50M main rail or bootloader/PMIC default outside the eSoC provider source and current DTB contract.

## Next

V1642 should be host-only: classify bootloader/PMIC-owner artifacts and source references for the unknown SDX50M main-rail prerequisite. It should not perform live write, flash, reboot, PMIC/GPIO/GDSC mutation, Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, eSoC notify/BOOT_DONE, PCI rescan, or platform bind/unbind.

## Safety Scope

V1641 is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
