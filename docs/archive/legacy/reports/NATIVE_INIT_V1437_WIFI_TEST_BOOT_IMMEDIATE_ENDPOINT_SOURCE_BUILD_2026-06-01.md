# Native Init V1437 Wi-Fi Test Boot Immediate Endpoint Source Build

## Summary

- Cycle: `V1437`
- Type: source/build-only Wi-Fi test boot artifact
- Decision: `v1437-wifi-test-boot-immediate-endpoint-source-build-pass`
- Result: PASS
- Reason: built a rollbackable test boot that samples exact endpoint state immediately after the corrected RC1 `case=11` write
- Manifest: `tmp/wifi/v1437-wifi-test-boot-immediate-endpoint-sampler/manifest.json`

## Artifact

- Boot image: `tmp/wifi/v1437-wifi-test-boot-immediate-endpoint-sampler/boot_linux_v1437_wifi_test.img`
- Native init: `0.9.80 (v1437-wifitest)`
- Init SHA256: `3b6149a2f8ea1ed1c51248899e983ecb4b96e3d556552b8b3961e56918c9ef43`
- Helper marker: `a90_android_execns_probe v286`
- Helper SHA256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`
- Ramdisk SHA256: `08bdfdd23a2d1a6a9af992162cb603b2c3f7ad66c9049efb84980029b8730a66`
- Boot SHA256: `160603f17c0b15c4fa289049b26dd79baf87007356b0a746f18f0aec93cb95b0`

## Instrumentation Contract

- Keeps the V1433 focused endpoint sampler and adds `read-only-v1437-immediate-endpoint`.
- Writes immediate samples to `/cache/native-init-wifi-test-boot-v1437-rc1-window.result`.
- Samples exact pcie1 regulator, clock, GPIO, pinmux, pinconf, interrupt, and link-state fields after the corrected RC1 `case=11` write.
- Emits labels `after_case_0ms`, `after_case_1ms`, `after_case_5ms`, and `after_case_20ms`.
- Preserves the existing `250ms` delay before corrected RC1 entry and does not add retries.

## Validation

- Static aarch64 init and helper verification passed.
- Ramdisk and boot image repack completed from `stage3/boot_linux_v724.img`.
- Marker verification passed for `A90v1437`, `read-only-v1437-immediate-endpoint`, `rc1_immediate_sample`, `immediate_*` sources, and `after_case_*` labels.
- Forbidden credential-like byte scan passed for init, helper, ramdisk, and boot image.
- No device command, flash, reboot, partition write, Wi-Fi scan/connect, credential handling, DHCP/routes, or external ping occurred.

## Next

V1438 should perform local-only artifact sanity over the exact V1437 manifest,
boot image, marker contract, v724 header/kernel parity, static binaries,
private modes, and forbidden credential-like byte absence before any live
handoff.
