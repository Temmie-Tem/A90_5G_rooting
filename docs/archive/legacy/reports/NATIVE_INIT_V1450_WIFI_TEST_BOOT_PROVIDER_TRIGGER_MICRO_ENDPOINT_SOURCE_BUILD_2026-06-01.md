# Native Init V1450 Wi-Fi Test Boot Provider-Trigger Micro Endpoint Source Build

## Summary

- Cycle: `V1450`
- Type: source/build-only Wi-Fi test boot artifact
- Decision: `v1450-wifi-test-boot-provider-trigger-micro-endpoint-source-build-pass`
- Result: PASS
- Reason: built a rollbackable test boot that samples endpoint state immediately around the provider-level `__subsystem_get: esoc0`/`mdm_subsys_powerup` trigger without issuing an explicit RC1 debugfs case write
- Manifest: `tmp/wifi/v1450-wifi-test-boot-provider-trigger-micro-endpoint-sampler/manifest.json`

## Artifact

- Boot image: `tmp/wifi/v1450-wifi-test-boot-provider-trigger-micro-endpoint-sampler/boot_linux_v1450_wifi_test.img`
- Native init: `0.9.83 (v1450-wifitest)`
- Init SHA256: `72bda9dd8ab613b9bc60423d271648fb6ee1509b03d38ace66a14ab65aa827d8`
- Helper marker: `a90_android_execns_probe v286`
- Helper SHA256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`
- Ramdisk SHA256: `917d06c8a3f77883872e94a9c12aeeea5c1f1a8884a542b6460e77693a7a91eb`
- Boot SHA256: `4b091310d8452473bfd5de8356a065f4b65b8b5fc84a4e6bb7ffa8d8e084eeed`

## Instrumentation Contract

- Adds `read-only-v1450-provider-trigger-micro-endpoint`.
- Keeps the RC1 endpoint sampler and micro sampler gates enabled.
- Watches the existing PID1 kmsg trigger for `__subsystem_get: esoc0`/`mdm_subsys_powerup`.
- Sets watcher delay to `0ms`.
- Does not write `/sys/kernel/debug/pci-msm/rc_sel` or `/sys/kernel/debug/pci-msm/case`.
- Samples selected interrupts, exact endpoint GPIOs, and pcie1 link-state files at `0ms`, `1ms`, `2ms`, `5ms`, `10ms`, `20ms`, `50ms`, `100ms`, and `150ms` after provider-trigger detection.
- Keeps a single slower `post_provider_micro_200ms` context sample after the active provider window.
- Does not add retries.

## Validation

- Static aarch64 init and helper build completed.
- Ramdisk and boot image repack completed from `stage3/boot_linux_v724.img`.
- Marker verification passed for `A90v1450`, `read-only-v1450-provider-trigger-micro-endpoint`, `provider_trigger_micro_endpoint_sampler_requested`, `provider_micro_after_trigger_%dms`, and `post_provider_micro_200ms`.
- Manifest records `provider_trigger_micro_endpoint_sampler=true`, `rc1_micro_endpoint_sampler=true`, `rc1_endpoint_sampler=true`, `rc1_case_aligned_micro_endpoint_sampler=false`, `rc1_immediate_endpoint_sampler=false`, `rc1_focused_endpoint_sampler=false`, `rc1_watcher_delay_ms=0`, and `rc1_retry_count=0`.
- No live command, flash, reboot, partition write, Wi-Fi scan/connect, credential handling, DHCP/routes, or external ping occurred.

## Next

V1451 should perform local-only artifact sanity over the exact V1450 manifest,
boot image, marker contract, v724 header/kernel parity, static binaries,
private modes, and forbidden credential-like byte absence before any live
handoff.
