# Native Init V1536 Wi-Fi Sysfs/Client Enumerate Source Build

## Summary

- Cycle: `V1536`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1536-wifi-sysfs-client-enumerate-test-boot-source-build-pass`
- Result: PASS
- Reason: built a credential-free test boot that replaces PID1 debugfs TEST:11 with targeted pci-msm sysfs/client enumerate
- Manifest: `tmp/wifi/v1536-wifi-sysfs-client-enumerate-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1536-wifi-sysfs-client-enumerate-test-boot/boot_linux_v1536_wifi_test.img`
- Boot SHA256: `9a8f10f9ae3cf6247faa49e78baa2fa9de5ce2539380893c8b7a777923b4e527`
- Init: `A90 Linux init 0.9.98 (v1536-wifitest)`
- Init SHA256: `4d5ae1e7c203eea0b2b26b462cfe2adc315eb441a7ce75921cea0db6e900e401`
- Helper marker: `a90_android_execns_probe v287`
- Helper SHA256: `660d88fc9e0ebdf6c95e495d9dd659c09321feb407fe6a7f77213f3b5c2bb411`

## Delta From V1515/V1535

- Keeps the V1515 critical-source, source-timestamped, case-aligned micro sampling contract.
- Changes only the PID1 first-L0 trigger write: `/sys/devices/platform/soc/1c08000.qcom,pcie/debug/enumerate` receives `1` instead of writing debugfs `rc_sel=2` and `case=11`.
- Records `trigger_mode=sysfs_client_enumerate` in the RC1 watcher result and `sysfs_client_enumerate=1` in the window result header.
- Preserves the hard exclusions: no Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC writes, eSoC notify/BOOT_DONE spoof, global PCI rescan, or platform bind/unbind.

## Test-Boot Contract

- Log path: `/cache/native-init-wifi-test-boot-v1536.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1536.summary`
- RC1 watcher result path: `/cache/native-init-wifi-test-boot-v1536-rc1-watcher.result`
- Sysfs/client enumerate result path: `/cache/native-init-wifi-test-boot-v1536-sysfs-client-enumerate.result`
- Supervisor timeout sec: `70`
- sysfs/client enumerate trigger: `True`
- micro source timestamped sampler: `True`
- micro critical fast endpoint sampler: `True`
- case-aligned micro sampler: `True`

## Safety Scope

This build script was source/build-only. It did not issue device commands,
flash, reboot, start Wi-Fi HAL, scan/connect, use credentials, configure
DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform
global PCI rescan/platform bind-unbind, or write device partitions.

## Verification

- Static init and helper verification passed.
- Ramdisk entries include `/init`, `/bin/a90_android_execns_probe`, `/bin/a90_tcpctl`, and `/bin/a90_rshell`.
- Boot image marker verification passed, including sysfs/client enumerate, auto-readiness, PID1 RC1 watcher, endpoint, focused, case-aligned micro, source-timestamped, and critical-fast sampler markers.
- Forbidden credential-like byte scan over init/helper/ramdisk/boot image passed.

## Next

V1537 should run local artifact sanity over the exact V1536 manifest before
any rollbackable live handoff. V1538 may then flash only this test image,
collect the V1536 log, summary, RC1 watcher result, sysfs-client enumerate
result, focused dmesg, and `wlan0` state, then roll back to v724 and verify
native selftest `fail=0`.
