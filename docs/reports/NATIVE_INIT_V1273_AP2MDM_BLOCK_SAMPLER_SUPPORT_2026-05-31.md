# V1273 AP2MDM Block Sampler Support

## Result

- decision: `v1273-block-sampler-build-pass`
- evidence: `tmp/wifi/v1273-execns-helper-v266-build/manifest.json`
- helper: `a90_android_execns_probe v266`
- helper SHA256: `3bf4105d685f023ccdeb75ae28d7d104ca005fc9f70870dc6f402a9ea4038ed4`
- output: `stage3/linux_init/helpers/a90_android_execns_probe_v266`
- output size: `1319408`
- scope: source/build-only; no deploy, live command, GPIO line request, PMIC write, eSoC ioctl, Wi-Fi action, flash, boot image write, or partition write

## Changes

- Bump `stage3/linux_init/helpers/a90_android_execns_probe.c` to helper v266.
- Extend the existing late `per_proxy` / PM-service response sampler with
  compact read-only block snapshots:
  - PM8150L debugfs GPIO block around the gpiochip range containing global
    GPIO1270.
  - TLMM GPIO135/GPIO142 debugfs GPIO blocks if the kernel exposes exact lines.
  - PMIC GPIO9 pinconf surrounding block.
  - TLMM GPIO135/GPIO142 pinconf surrounding blocks.
- Keep existing GPIO142 IRQ, `mdm3`, PCI/MHI, MHI pipe, `wlan0`, PMIC GPIO9
  line-info, and PCIe GDSC samples.

## Validation

- Static aarch64 build passed through
  `scripts/revalidation/build_android_execns_probe_helper.sh`.
- `readelf -l` shows no `INTERP` segment.
- `readelf -d` reports no dynamic section.
- Binary strings include helper v266 marker and all new `*_block_seen` response
  fields.

## Safety

The helper adds read-only text capture only.  It does not request or hold GPIO
lines, write PMIC/debugfs/regulator state, issue direct eSoC ioctl, start new
daemon/HAL paths beyond the existing bounded PM-service response path, perform
Wi-Fi scan/connect, use credentials, run DHCP/routes, send external ping, flash,
write a boot image, or write partitions.

## Next

V1274 should deploy helper v266 only.  V1275 should run the bounded AP2MDM block
sampler with the same late `per_proxy` / PM-service `/dev/subsys_esoc0`
response window.
