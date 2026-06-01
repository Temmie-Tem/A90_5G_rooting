# Native Init V1441 Wi-Fi Test Boot Micro Endpoint Source Build

## Summary

- Cycle: `V1441`
- Type: source/build-only Wi-Fi test boot artifact
- Decision: `v1441-wifi-test-boot-micro-endpoint-source-build-pass`
- Result: PASS
- Reason: built a rollbackable test boot that replaces active-window full debugfs summary scans with a micro endpoint sampler around the corrected RC1 write
- Manifest: `tmp/wifi/v1441-wifi-test-boot-micro-endpoint-sampler/manifest.json`

## Artifact

- Boot image: `tmp/wifi/v1441-wifi-test-boot-micro-endpoint-sampler/boot_linux_v1441_wifi_test.img`
- Native init: `0.9.81 (v1441-wifitest)`
- Init SHA256: `9b9e11aaa4d08bd41d6a80b4c27a1b236e1b1f47b12e29f60ef8116908854ec3`
- Helper marker: `a90_android_execns_probe v286`
- Helper SHA256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`
- Ramdisk SHA256: `418d73685515a4e113eeded6a559e369c2fc295a306410469c38cd61065bae30`
- Boot SHA256: `5977e2356322311c99d06cf0d2fdde266563ad41c6c11e4222a65edd33723bb0`

## Instrumentation Contract

- Adds `read-only-v1441-micro-endpoint` and keeps the RC1 endpoint sampler gate enabled.
- Writes micro samples to `/cache/native-init-wifi-test-boot-v1441-rc1-window.result`.
- Forks a writer child for corrected `rc_sel=2` and `case=11`, while the parent samples minimal fields at `0ms`, `1ms`, `2ms`, `5ms`, `10ms`, `20ms`, `50ms`, `100ms`, and `150ms` after the case write.
- Bounds the writer child with a `2000ms` wait/kill path before reading its pipe result so a stuck debugfs write cannot block result collection indefinitely.
- Samples only narrow active-window fields: selected `/proc/interrupts` needles, exact debug GPIO entries for GPIO102/GPIO103/GPIO104/GPIO135/GPIO142, and pcie1 link-state files.
- Avoids regulator and clock summary scans during the active RC1 window; a single slower `post_micro_200ms` sample remains after the active window for context.
- Preserves the existing `250ms` delay before corrected RC1 entry and does not add retries.

## Validation

- Static aarch64 init and helper build completed.
- Ramdisk and boot image repack completed from `stage3/boot_linux_v724.img`.
- Marker verification passed for `A90v1441`, `read-only-v1441-micro-endpoint`, `rc1_micro_sample`, `micro_*` fields, `micro_after_case_*` labels, and `post_micro_200ms`.
- Manifest records `rc1_micro_endpoint_sampler=true`, `rc1_endpoint_sampler=true`, `rc1_immediate_endpoint_sampler=false`, `rc1_focused_endpoint_sampler=false`, and `rc1_retry_count=0`.
- No live command, flash, reboot, partition write, Wi-Fi scan/connect, credential handling, DHCP/routes, or external ping occurred.

## Next

V1442 should perform local-only artifact sanity over the exact V1441 manifest,
boot image, marker contract, v724 header/kernel parity, static binaries,
private modes, and forbidden credential-like byte absence before any live
handoff.
