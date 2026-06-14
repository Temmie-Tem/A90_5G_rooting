# Native Init V1473 Wi-Fi Test Boot Effective-Level Artifact Sanity

## Summary

- Cycle: `V1473`
- Type: local-only artifact sanity verifier
- Decision: `v1473-wifi-test-boot-effective-level-artifact-sanity-pass`
- Result: PASS
- V1472 manifest: `tmp/wifi/v1472-wifi-test-boot-exact-provider-effective-level-sampler/manifest.json`
- V1472 boot image: `tmp/wifi/v1472-wifi-test-boot-exact-provider-effective-level-sampler/boot_linux_v1472_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot markers: `True`
- retry/legacy/case-writer markers absent: `True`
- effective-level contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1472-wifi-test-boot-exact-provider-effective-level-sampler/boot_linux_v1472_wifi_test.img`
- boot sha256: `2835568c31f9a9a25dac6e7830cdb51d666bdd050bf16646fa1518b8d7ed1e02`
- ramdisk sha256: `dadef407114d50358682ae40d7157b31d63e072ecc7298da6d43dca0b4a61ee4`
- helper sha256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`
- RC1 watcher result path: `/cache/native-init-wifi-test-boot-v1472-rc1-watcher.result`
- RC1 window result path: `/cache/native-init-wifi-test-boot-v1472-rc1-window.result`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write,
Wi-Fi HAL, scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global
PCI rescan, or platform bind/unbind was performed.

## Next

V1474 may perform a rollbackable live handoff for only the V1472 test
image, expect `A90 Linux init 0.9.88 (v1472-wifitest)`, collect the
V1472 log, summary, RC1 watcher result, effective-level window result,
dmesg markers, and `wlan0` state, then roll back to
`stage3/boot_linux_v724.img`.
