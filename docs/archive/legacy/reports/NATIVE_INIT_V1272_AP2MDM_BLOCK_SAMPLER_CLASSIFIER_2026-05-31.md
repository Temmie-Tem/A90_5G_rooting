# V1272 AP2MDM Block Sampler Classifier

## Result

- decision: `v1272-ap2mdm-block-sampler-selected`
- evidence: `tmp/wifi/v1272-ap2mdm-block-sampler-classifier/manifest.json`
- scope: host-only classifier; no live command, device mutation, GPIO line request, PMIC write, eSoC ioctl, Wi-Fi action, flash, boot image write, or partition write

## Purpose

V1271 proved that the relevant read-only debugfs surfaces are available in the
PM-service `/dev/subsys_esoc0` response window, but the exact debugfs GPIO value
lines for global GPIO1270 / TLMM GPIO135 / TLMM GPIO142 were not present in the
captured single-line lookups.

V1272 classifies whether the next step should be a broader read-only block
sampler rather than a write-side experiment.  The expected next gate is helper
v266 source/build-only.

## Classification

| field | result |
|---|---|
| V1271 sample count | `14` |
| PMIC GPIO9 line-info flags | `0x3` in all samples |
| PMIC GPIO9 line-info consumer | `AP2MDM_SOFT_RESET` in all samples |
| debugfs GPIO surface | present |
| pinctrl debugfs surface | present |
| regulator debugfs surface | present |
| exact debugfs value lines | absent for PMIC GPIO1270 / TLMM GPIO135 / TLMM GPIO142 |
| downstream response | absent: GPIO142 `0`, no PCI/MHI/MHI-pipe/`wlan0` |

V1272 therefore selects a read-only block sampler.  It does not justify direct
GPIO line request/hold, PMIC writes, direct eSoC ioctl, or Wi-Fi bring-up.

## Expected Next Gate

V1273 should add compact block capture to the existing late `per_proxy` /
PM-service response sampler:

- `/sys/kernel/debug/gpio` block for gpiochip ranges containing PM8150L global
  GPIO1270.
- `/sys/kernel/debug/gpio` block for TLMM GPIO135/GPIO142 if exposed.
- PM8150L GPIO9 pinmux and pinconf surrounding lines.
- TLMM GPIO135/GPIO142 pinmux and pinconf surrounding lines.
- PCIe RC1 debug/power/runtime state and `pcie_0_gdsc` / `pcie_1_gdsc`
  regulator lines.
- Existing GPIO142 IRQ, `mdm3`, PCI/MHI/MHI-pipe/`wlan0` counters.

Hard exclusions remain unchanged: no PMIC write, userspace GPIO line
request/hold, direct eSoC ioctl, new daemon/HAL start beyond the bounded
PM-service response path, Wi-Fi scan/connect, credentials, DHCP/routes, external
ping, flash, boot image write, or partition write.
