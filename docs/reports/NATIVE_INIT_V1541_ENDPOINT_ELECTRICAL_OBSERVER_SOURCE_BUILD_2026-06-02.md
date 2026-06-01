# Native Init V1541 Endpoint Electrical Observer Source Build

## Summary

- Cycle: `V1541`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1541-endpoint-electrical-observer-test-boot-source-build-pass`
- Result: PASS
- Reason: built a credential-free test boot that keeps the V1536 sysfs/client enumerate trigger and adds micro-focused endpoint electrical sampling
- Manifest: `tmp/wifi/v1541-endpoint-electrical-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1541-endpoint-electrical-observer-test-boot/boot_linux_v1541_wifi_test.img`
- Boot SHA256: `fc3439f71811422d6152d0d35a54afa74a438dc11ad578704486e25150adeb33`
- Init: `A90 Linux init 0.9.99 (v1541-wifitest)`
- Init SHA256: `df254f4bf0f630e9196bc73cd6dc8121ecce3649223ac1fe19ee7b51b9789104`
- Helper marker: `a90_android_execns_probe v287`
- Helper SHA256: `660d88fc9e0ebdf6c95e495d9dd659c09321feb407fe6a7f77213f3b5c2bb411`

## Delta From V1536/V1540

- Keeps the V1536 targeted sysfs/client enumerate trigger at `/sys/devices/platform/soc/1c08000.qcom,pcie/debug/enumerate`.
- Keeps the critical-fast sampler for `/proc/interrupts`, `/sys/kernel/debug/gpio`, regulator summary, and pinmux.
- Adds the existing micro-focused sampler so each case-aligned micro sample also attempts exact-match reads for `micro_focused_clk`, `micro_focused_pinconf`, `micro_focused_pinmux`, `micro_focused_debug_gpio`, and focused regulator lines.
- Targets the V1540 observables: GPIO102/PERST, GPIO103/CLKREQ, GPIO104/WAKE, GPIO135/AP2MDM, GPIO142/MDM2AP, `pcie_1_gdsc`, `gcc_pcie_1_*`, clkref/refgen, and pinconf state in the RC1 link-training window.
- Does not add new live mutation beyond the already bounded sysfs/client enumerate trigger. No PMIC/GPIO/GDSC direct write, eSoC notify/BOOT_DONE spoof, global PCI rescan, platform bind/unbind, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Test-Boot Contract

- Log path: `/cache/native-init-wifi-test-boot-v1541.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1541.summary`
- RC1 watcher result path: `/cache/native-init-wifi-test-boot-v1541-rc1-watcher.result`
- Endpoint electrical result path: `/cache/native-init-wifi-test-boot-v1541-endpoint-electrical.result`
- Supervisor timeout sec: `70`
- sysfs/client enumerate trigger: `True`
- micro source timestamped sampler: `True`
- micro critical fast endpoint sampler: `True`
- micro focused endpoint sampler: `True`
- case-aligned micro sampler: `True`

## Safety Scope

This build script was source/build-only. It did not issue device commands,
flash, reboot, start Wi-Fi HAL, scan/connect, use credentials, configure
DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform
global PCI rescan/platform bind-unbind, or write device partitions.

## Verification

- Static init and helper verification passed.
- Ramdisk entries include `/init`, `/bin/a90_android_execns_probe`, `/bin/a90_tcpctl`, and `/bin/a90_rshell`.
- Boot image marker verification passed, including sysfs/client enumerate, auto-readiness, PID1 RC1 watcher, endpoint, focused, case-aligned micro, source-timestamped, critical-fast, and micro-focused sampler markers.
- Forbidden credential-like byte scan over init/helper/ramdisk/boot image passed.

## Next

V1542 should run local artifact sanity over the exact V1541 manifest before
any rollbackable live handoff. If sanity passes, V1543 may flash only this
test image, collect the V1541 log, summary, RC1 watcher result, endpoint
electrical result, focused dmesg, and `wlan0` state, then roll back to v724
and verify native selftest `fail=0`.
