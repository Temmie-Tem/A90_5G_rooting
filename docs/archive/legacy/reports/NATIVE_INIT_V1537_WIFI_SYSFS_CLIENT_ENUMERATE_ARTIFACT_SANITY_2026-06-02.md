# Native Init V1537 Wi-Fi Sysfs/Client Enumerate Artifact Sanity

## Summary

- Cycle: `V1537`
- Type: local-only artifact sanity verifier
- Decision: `v1537-wifi-sysfs-client-enumerate-artifact-sanity-pass`
- Result: PASS
- V1536 manifest: `tmp/wifi/v1536-wifi-sysfs-client-enumerate-test-boot/manifest.json`
- V1536 boot image: `tmp/wifi/v1536-wifi-sysfs-client-enumerate-test-boot/boot_linux_v1536_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot markers: `True`
- AP2MDM hold marker absence: `True`
- sysfs/client enumerate contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1536-wifi-sysfs-client-enumerate-test-boot/boot_linux_v1536_wifi_test.img`
- boot sha256: `9a8f10f9ae3cf6247faa49e78baa2fa9de5ce2539380893c8b7a777923b4e527`
- ramdisk sha256: `7fccc12c5c51b60ae29b1990fb63897fb226d0a3a9b3811c1cd6de7d88370872`
- init sha256: `4d5ae1e7c203eea0b2b26b462cfe2adc315eb441a7ce75921cea0db6e900e401`
- helper sha256: `660d88fc9e0ebdf6c95e495d9dd659c09321feb407fe6a7f77213f3b5c2bb411`
- helper marker: `a90_android_execns_probe v287`

## Verified Test Scope

- The test image keeps the proven PM/eSoC current route and PID1 RC1 watcher timing.
- The test image replaces debugfs TEST:11 with the targeted pci-msm sysfs/client enumerate attribute.
- The test image records case-aligned micro samples at 0/1/2/5/10/20/50/100/150ms after the sysfs enumerate write returns.
- The test image blocks Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, and external ping.

## Safety Scope

No device command, flash, reboot, boot partition write, partition write,
Wi-Fi HAL, scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global
PCI rescan, or platform bind/unbind was performed by this verifier. The
verified test image itself is not observation-only: if booted, its PID1 watcher
may issue the bounded targeted sysfs/client enumerate write listed above.

## Next

V1538 may perform a rollbackable live handoff for only the V1536 test image,
expect `A90 Linux init 0.9.98 (v1536-wifitest)`, collect the V1536 log,
summary, RC1 watcher result, sysfs-client enumerate result, focused dmesg,
and `wlan0` state, then roll back to `stage3/boot_linux_v724.img` and verify
native selftest `fail=0`.
