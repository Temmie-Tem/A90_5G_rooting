# Native Init V1658 Post-MDM2AP Silence Next-Gate Selector

## Summary

- Cycle: `V1658`
- Type: host-only post-MDM2AP-silence next-gate selector
- Decision: `v1658-select-android-good-rail-reference-next`
- Result: PASS
- Selected next gate: `Android-good rail/reference capture`
- Reason: V1657 fixed the lower blocker at clean natural-path MDM2AP silence, but prior rail/owner classifiers still do not identify a safe AP-native write target.

## Evidence Checks

| check | value |
|---|---:|
| `v1657_clean_natural_silent` | `True` |
| `v1657_gpio142_zero` | `True` |
| `v1657_errfatal_zero` | `True` |
| `v1657_rollback_ok` | `True` |
| `contract_stop_after_silent` | `True` |
| `v1641_no_safe_write_target` | `True` |
| `v1642_owner_outside_ap_source` | `True` |
| `v1656_xbl_no_mutation_target` | `True` |
| `v1555_android_good_reference` | `True` |
| `pon_provider_no_regulator` | `True` |
| `dtb_non_differential` | `True` |
| `local_esoc_no_regulator_code` | `True` |

## Gate Matrix

| gate | class | reason | next |
|---|---|---|---|
| repeat natural-path timing/window variant | `reject` | V1657 already produced the fixed contract label; repeating this recreates the V1370-V1559 drift mode. | none |
| forced RC1 enumerate / pci-msm case write | `reject` | downstream and contaminating; it cannot prove natural MDM2AP response. | none |
| fake ONLINE / system-info spoof | `reject` | inverts causality below the provider; does not power SDX50M. | none |
| direct PMIC/GPIO/GDSC write | `reject-for-now` | no named owner, voltage/sequence constraints, or rollbackable AP-native write surface exists. | requires separate bounded hypothesis after a concrete target is identified |
| Android-good rail/reference capture | `selected-next` | non-mutating reference capture can identify which regulator/PMIC/clock/IRQ surfaces differ when Android-good reaches GPIO142, WLFW, and wlan0. | V1659 plan/source-build for a minimal Android-good rail snapshot handoff |
| additional bootloader/XBL context expansion | `secondary` | useful only if Android-good rail reference still cannot name a target; current XBL context is informative but not causal. | bounded private artifact context only, not a live write |

## Interpretation

V1657 removes the forced-RC1 caveat: the natural provider/PON/AP2MDM path ran and MDM2AP/GPIO142 plus errfatal IRQ deltas stayed zero. The next step toward actual Wi-Fi connectivity is not credentials, HAL, firmware transfer, or another timing retry. It is to name the missing lower power prerequisite.

A direct PMIC/GPIO/GDSC write remains unjustified because V1641/V1642/V1656 still lack a concrete AP-native target with owner, voltage/sequence constraints, and rollbackable control surface. The shortest useful non-mutating step is an Android-good reference capture that preserves the known-good lower path while recording read-only regulator/PMIC/GPIO/IRQ summaries around esoc0/provider trigger and `wlan0` creation.

## V1659 Contract Sketch

- Type: source/build-only plan first, then separate rollbackable Android-good handoff.
- Capture: filtered dmesg, GPIO135/142/141/104/102 IRQ and level summaries, `/sys/class/regulator` names/states/voltages, pcie1 GDSC/refclk/pipe summaries, and module status.
- Timing: pre-esoc0 baseline, esoc0/AP2MDM window, first GPIO142/MDM status response, BDF/FW-ready/`wlan0`, and final post-good snapshot.
- Rollback: restore `stage3/boot_linux_v724.img`; verify `A90 Linux init 0.9.68 (v724)` and selftest `fail=0`.
- Hard stops: no PMIC/GPIO/GDSC writes, no PCI rescan, no platform bind/unbind, no eSoC notify/`BOOT_DONE`, no native Wi-Fi HAL/scan/connect, no credentials, no DHCP/routes, and no external ping in this reference gate.

## Public Source Notes

Public Qualcomm kernel sources match the local source model: external MDM devices are GPIO-controlled, `ap2mdm-pmic-pwr-en-gpio` is optional, and MDM readiness is represented by MDM2AP status/interrupt handling. A90's local DTS/source evidence still lacks an AP-side PMIC power-enable or mdm3 regulator property, so these sources support observation and target discovery, not blind mutation.

| source | used for |
|---|---|
| https://android.googlesource.com/kernel/msm/+/ed2365b00f56c064b561b008659e2a5e5afd79a8/Documentation/devicetree/bindings/arm/msm/mdm-modem.txt | external modem GPIO model and optional AP2MDM PMIC power-enable property |
| https://android.googlesource.com/kernel/msm/+/android-wear-6.0.1_r0.114/drivers/esoc/esoc-mdm-4x.c | AP2MDM/MDM2AP GPIO map and status IRQ readiness model |

## Safety Scope

V1658 is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
