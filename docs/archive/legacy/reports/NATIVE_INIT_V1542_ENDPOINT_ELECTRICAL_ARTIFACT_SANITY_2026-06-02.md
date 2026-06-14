# Native Init V1542 Endpoint Electrical Artifact Sanity

## Summary

- Cycle: `V1542`
- Type: local-only artifact sanity verifier
- Decision: `v1542-endpoint-electrical-artifact-sanity-pass`
- Result: PASS
- V1541 manifest: `tmp/wifi/v1541-endpoint-electrical-observer-test-boot/manifest.json`
- V1541 boot image: `tmp/wifi/v1541-endpoint-electrical-observer-test-boot/boot_linux_v1541_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot markers: `True`
- absent unsafe/old markers: `True`
- endpoint electrical contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1541-endpoint-electrical-observer-test-boot/boot_linux_v1541_wifi_test.img`
- boot sha256: `fc3439f71811422d6152d0d35a54afa74a438dc11ad578704486e25150adeb33`
- ramdisk sha256: `973f4a76aee73affd9561067f4b1a18ca9c5f1797ff082b223282532687fb84d`
- init sha256: `df254f4bf0f630e9196bc73cd6dc8121ecce3649223ac1fe19ee7b51b9789104`
- helper sha256: `660d88fc9e0ebdf6c95e495d9dd659c09321feb407fe6a7f77213f3b5c2bb411`
- helper marker: `a90_android_execns_probe v287`

## Verified Test Scope

- The test image keeps the V1536 targeted sysfs/client enumerate trigger.
- The test image adds micro-focused endpoint electrical sampling for focused clock, regulator, GPIO, pinmux, and pinconf lines.
- The test image records case-aligned micro samples at 0/1/2/5/10/20/50/100/150ms after the sysfs enumerate write returns.
- The test image blocks Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, and external ping.

## Safety Scope

No device command, flash, reboot, boot partition write, partition write,
Wi-Fi HAL, scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global
PCI rescan, or platform bind/unbind was performed by this verifier. The
verified test image itself is not observation-only: if booted, its PID1
watcher may issue the bounded targeted sysfs/client enumerate write.

## Next

V1543 may perform a rollbackable live handoff for only the V1541 test
image, collect the V1541 log, summary, RC1 watcher result, endpoint
electrical result, focused dmesg, and `wlan0` state, then roll back to
`stage3/boot_linux_v724.img` and verify selftest `fail=0`.
