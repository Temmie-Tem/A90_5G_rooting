# Native Init V1618 pm-service System-info Surface Artifact Sanity

## Summary

- Cycle: `V1618`
- Type: local-only artifact sanity verifier
- Decision: `v1618-pm-service-system-info-surface-artifact-sanity-pass`
- Result: PASS
- V1617 manifest: `tmp/wifi/v1617-pm-service-system-info-surface-test-boot/manifest.json`
- V1617 boot image: `tmp/wifi/v1617-pm-service-system-info-surface-test-boot/boot_linux_v1617_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot system-info-surface markers: `True`
- helper system-info-surface markers: `True`
- init route: `True`
- route contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1617-pm-service-system-info-surface-test-boot/boot_linux_v1617_wifi_test.img`
- boot sha256: `7d9b60862a8eab04e0a0fe35b929ace255f0de669412a0cbe6262f6f0495419d`
- ramdisk sha256: `42064342941500e52706c85dbafb3894807249bc6a464892c1b59a389c7dca94`
- init sha256: `1cd6967d597a73e6b99b762f32e67fcaba11436c0b2697c1be10a4626ff209f6`
- helper sha256: `1b870e4244ba2794ee30bc113d6aa421f66dfea55a9c116139978b1b4b9e787e`
- helper marker: `a90_android_execns_probe v301`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind was performed by this verifier.

## Next

A later rollbackable live handoff may flash only the V1617 image, collect `pm_service_system_info_surface.*` snapshots, then roll back to `stage3/boot_linux_v724.img` and verify selftest `fail=0`.
