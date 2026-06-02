# Native Init V1622 pm-service Property-root Artifact Sanity

## Summary

- Cycle: `V1622`
- Type: local-only artifact sanity verifier
- Decision: `v1622-pm-service-property-root-artifact-sanity-pass`
- Result: PASS
- V1621 manifest: `tmp/wifi/v1621-pm-service-property-root-test-boot/manifest.json`
- V1621 boot image: `tmp/wifi/v1621-pm-service-property-root-test-boot/boot_linux_v1621_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot property-root markers: `True`
- helper property-root markers: `True`
- init route: `True`
- route contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1621-pm-service-property-root-test-boot/boot_linux_v1621_wifi_test.img`
- boot sha256: `52a56bc02787f2f72c44fad60aae6d8e4ca619135393798425e9d802f7d1c635`
- ramdisk sha256: `9cf21c19023609e1c0223f9ba68902f24653299f085de4a47fe0df71fbb54c95`
- init sha256: `0e951f5839fd450610cad6e6026bd243ab87c178fd9e4c339b7d1f1977afe700`
- helper sha256: `09732d4469d963e3c14ecb50f6f01341e92adfd3370c614d2ce779a71510230c`
- helper marker: `a90_android_execns_probe v302`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind was performed by this verifier.

## Next

A later rollbackable live handoff may flash only the V1621 image, collect `pm_service_system_info_surface.*` snapshots with `/dev/__properties__` materialized, then roll back to `stage3/boot_linux_v724.img` and verify selftest `fail=0`.
