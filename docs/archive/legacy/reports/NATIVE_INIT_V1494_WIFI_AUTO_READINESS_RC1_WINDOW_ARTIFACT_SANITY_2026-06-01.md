# Native Init V1494 Wi-Fi Auto-readiness RC1 Window Artifact Sanity

## Summary

- Cycle: `V1494`
- Type: local-only artifact sanity verifier
- Decision: `v1494-wifi-auto-readiness-rc1-window-artifact-sanity-pass`
- Result: PASS
- V1493 manifest: `tmp/wifi/v1493-wifi-auto-readiness-rc1-window-test-boot/manifest.json`
- V1493 boot image: `tmp/wifi/v1493-wifi-auto-readiness-rc1-window-test-boot/boot_linux_v1493_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot markers: `True`
- AP2MDM hold marker absence: `True`
- RC1 auto-readiness contract: `True`
- RC1 watcher contract includes bounded pci-msm debugfs writes:
  `/sys/kernel/debug/pci-msm/rc_sel=2` then
  `/sys/kernel/debug/pci-msm/case=11`.
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1493-wifi-auto-readiness-rc1-window-test-boot/boot_linux_v1493_wifi_test.img`
- boot sha256: `bc1a6484eb8786323b2a534b099839db32ad627d7688395265c63b647ed56c8e`
- ramdisk sha256: `104d6df9c2512b612d2fc1dd1393f5cc124bf78abe4793a1f167ed24c7a0d56f`
- helper sha256: `660d88fc9e0ebdf6c95e495d9dd659c09321feb407fe6a7f77213f3b5c2bb411`
- marker: `auto-v1485-wifi-readiness-test`
- helper marker: `a90_android_execns_probe v287`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write,
Wi-Fi HAL, scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global
PCI rescan, or platform bind/unbind was performed by this verifier. The
verified test image itself is not observation-only: if booted, its PID1 watcher
may issue the bounded corrected RC1 enumerate debugfs writes listed above.

## Next

V1495 may perform a rollbackable live handoff for only the V1493 test
image, expect `A90 Linux init 0.9.92 (v1493-wifitest)`, collect the
V1493 log, summary, RC1 watcher/window, focused dmesg, and `wlan0` state, then roll back to
`stage3/boot_linux_v724.img` and verify selftest `fail=0`.
