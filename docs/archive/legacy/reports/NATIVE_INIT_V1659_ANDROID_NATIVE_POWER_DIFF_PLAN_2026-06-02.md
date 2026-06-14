# Native Init V1659 Android-good vs Native Power Diff Plan

## Summary

- Cycle: `V1659`
- Type: source/build-only Android-good vs native power/clock/sequence diff plan
- Decision: `v1659-android-native-power-diff-plan-ready`
- Result: PASS
- Contract: `docs/reports/ESOC_ANDROID_NATIVE_POWER_DIFF_CONTRACT_2026-06-02.md`
- Reason: V1657 fixed clean natural-path MDM2AP silence; a write gate still has no concrete target, so the next gate is the final AP-side read-only Android-vs-native diff.

## Evidence Checks

| check | value |
|---|---:|
| `contract_present` | `True` |
| `contract_labels_fixed` | `True` |
| `contract_both_sides` | `True` |
| `v1657_clean_silent` | `True` |
| `v1555_android_good` | `True` |
| `v1641_no_write_target` | `True` |
| `v1656_xbl_dead_end` | `True` |
| `pon_provider_no_regulator` | `True` |
| `dtb_parity` | `True` |
| `v1514_clk_summary_caution_or_contract` | `True` |

## Observables

| observable | Android-good | native | diff target |
|---|---|---|---|
| `regulator_summary_full` | read full `/sys/kernel/debug/regulator/regulator_summary` snapshots | read the same summary snapshots in the natural-provider window | rails enabled/used in Android but off/zero/absent in native |
| `targeted_named_clocks` | read only pcie1/refclk/modem-related named clock lines | read only the same targeted clock lines | clock prepared/enabled in Android but not native |
| `subsystem_sequence` | sample subsys0(mss), subsys9(esoc0), service/process timing around esoc0 | sample the same subsystem state/order in the V1657 natural PM-first route | Android-only pre-esoc0 subsystem bring-up or glink/SMP2P step |
| `gpio_irq` | GPIO135/142, msm_pcie_wake, mdm status, errfatal IRQ deltas | same GPIO/IRQ deltas with no forced RC1 and no spoof | positive Android response vs native silence |

## Fixed Labels

| label | meaning | action |
|---|---|---|
| `power-vote-gap` | Android enables a rail/clock that native does not. | STOP and hand back for separately authorized targeted write gate; do not write here. |
| `sequence-gap` | Power/clock parity, but Android brings up a subsystem/route before esoc0 that native omits. | STOP and design route fix; no PMIC/GPIO/GDSC write. |
| `full-power-parity-hardware-wall` | AP-side rails, clocks, and sequence match; remaining cause is below AP control. | Terminal PASS classification; STOP. Do not enter write gate autonomously. |

## Execution Plan

| cycle | side | type | implementation |
|---|---|---|---|
| `V1660` | Android-good | source/build-only then rollbackable handoff | reuse V1521/V1555 Magisk post-fs-data engine; add full regulator snapshot and targeted clock snapshot reads |
| `V1661` | native | source/build-only then rollbackable natural-path handoff | reuse V1657 natural PM-first route; add the same regulator/clock/subsys/GPIO/IRQ read-only sampler |
| `V1662` | host | host-only diff classifier | diff V1660 vs V1661 and emit exactly one fixed label |

## Hard Stops

- no regulator/PMIC/GPIO/GDSC writes
- no forced RC1/case writes
- no fake ONLINE/system-info spoof
- no eSoC notify/BOOT_DONE
- no PCI rescan
- no platform bind/unbind
- no Wi-Fi HAL/scan/connect
- no credentials
- no DHCP/routes
- no external ping
- one Android run plus one native run plus one diff only; no timing/window variants

## Honest Scope Limit

The SDX50M's own modem-side rail is not represented in the AP regulator tree. If that is the true blocker, this gate should produce `full-power-parity-hardware-wall`, not a write target. That is still a useful terminal classification for the native route.

## Safety Scope

V1659 is source/build-only planning. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, platform bind/unbind, Android handoff, or native test boot.
