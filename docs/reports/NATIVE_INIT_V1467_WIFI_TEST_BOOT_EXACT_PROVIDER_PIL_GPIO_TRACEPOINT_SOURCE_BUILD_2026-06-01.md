# Native Init V1467 Wi-Fi Test Boot Exact Provider PIL+GPIO Tracepoint Source Build

## Summary

- Cycle: `V1467`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1467-wifi-test-boot-exact-provider-pil-gpio-tracepoint-source-build-pass`
- Result: PASS
- Reason: built an exact-provider PIL+GPIO tracepoint sampler without contacting or flashing the device
- Manifest: `tmp/wifi/v1467-wifi-test-boot-exact-provider-pil-gpio-tracepoint-sampler/manifest.json`
- Boot image: `tmp/wifi/v1467-wifi-test-boot-exact-provider-pil-gpio-tracepoint-sampler/boot_linux_v1467_wifi_test.img`
- Boot SHA256: `e9fd747a483f9d5d22126ddda0f99c0a4b5b4b5343f20094d1d5d8cf3adb359e`
- Init: `A90 Linux init 0.9.87 (v1467-wifitest)`
- Init SHA256: `ff4a8869ed6bf53a2ebee4a772a1cdc8ae17a729bce73802b2d95cfccc779846`
- Helper marker: `a90_android_execns_probe v286`
- Helper SHA256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`

## Test-Boot Contract

- Keeps the exact provider trigger and thread-state sampler.
- Arms `gpio_value`, `gpio_direction`, and `msm_pil_event:pil_notif` tracepoints before helper start.
- Samples GPIO tracepoint output for GPIO1270, GPIO135, GPIO142, GPIO141, plus `fw=esoc0` PIL notifications.
- Samples endpoint state through `1000ms` plus a `1200ms` context sample.
- Does not issue an explicit RC1 debugfs `rc_sel`/`case` write.
- Does not write PMIC/GPIO/GDSC controls, eSoC notify/`BOOT_DONE`, or Wi-Fi HAL state.
- Sampler marker: `read-only-v1467-exact-provider-pil-gpio-tracepoint`.
- Log path: `/cache/native-init-wifi-test-boot-v1467.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1467.summary`
- Watcher result path: `/cache/native-init-wifi-test-boot-v1467-rc1-watcher.result`
- Window result path: `/cache/native-init-wifi-test-boot-v1467-rc1-window.result`

## Safety Scope

This build script was source/build-only. It did not issue device commands,
flash, reboot, start Wi-Fi HAL, scan/connect, use credentials, configure
DHCP/routes, perform external ping, or write device partitions.

## Verification

- Static init and helper verification passed.
- Ramdisk entries include `/init`, `/bin/a90_android_execns_probe`, `/bin/a90_tcpctl`, and `/bin/a90_rshell`.
- Boot image marker verification passed, including the PIL tracepoint contract.
- Forbidden credential-like byte scan over init/helper/ramdisk/boot image passed.

## Next

V1468 should be local-only artifact sanity over the exact V1467 manifest
before any rollbackable live handoff.
