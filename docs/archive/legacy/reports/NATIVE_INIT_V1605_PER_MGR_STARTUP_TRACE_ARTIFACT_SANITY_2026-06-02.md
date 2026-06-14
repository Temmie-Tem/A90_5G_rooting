# Native Init V1605 per_mgr Startup Trace Artifact Sanity

## Summary

- Cycle: `V1605`
- Type: local-only artifact sanity verifier
- Decision: `v1605-per-mgr-startup-trace-artifact-sanity-pass`
- Result: PASS
- V1604 manifest: `tmp/wifi/v1604-per-mgr-startup-trace-test-boot/manifest.json`
- V1604 boot image: `tmp/wifi/v1604-per-mgr-startup-trace-test-boot/boot_linux_v1604_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot startup-trace markers: `True`
- helper startup-trace markers: `True`
- init route: `True`
- route contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1604-per-mgr-startup-trace-test-boot/boot_linux_v1604_wifi_test.img`
- boot sha256: `eb8d1dc11656a8380180b96239d9fe9c8ba160f55f1ca3ff34a8552a6438cca8`
- ramdisk sha256: `af41c877ae9f19a41e77b76e8ea90f4dc8c19f1a8dc6159870bf47d6eba082df`
- init sha256: `c3b3d850cba6d71363b479a8bd0b53dce356df3f908f06b741de237a6abaa80d`
- helper sha256: `6a56b15650fe5c7785a878e7f86ade8e9c323e33cfb8c049952388022592d898`
- helper marker: `a90_android_execns_probe v298`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind was performed by this verifier.

## Next

V1606 may run a rollbackable live handoff of only this V1604 image, collect the startup trace/helper result/lower markers/dmesg/`wlan0`, then roll back to `stage3/boot_linux_v724.img` and verify selftest `fail=0`.
