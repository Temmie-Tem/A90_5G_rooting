# Native Init V1626 pm-service Shutdown-list Artifact Sanity

## Summary

- Cycle: `V1626`
- Type: local-only artifact sanity verifier
- Decision: `v1626-pm-service-shutdown-list-artifact-sanity-pass`
- Result: PASS
- V1625 manifest: `tmp/wifi/v1625-pm-service-shutdown-list-test-boot/manifest.json`
- V1625 boot image: `tmp/wifi/v1625-pm-service-shutdown-list-test-boot/boot_linux_v1625_wifi_test.img`

## Checks

- manifest decision: `True`
- base boot exists: `True`
- init static: `True`
- helper static: `True`
- ramdisk entries: `True`
- boot shutdown-list markers: `True`
- helper shutdown-list markers: `True`
- init route: `True`
- route contract: `True`
- header parity: `True`
- kernel parity: `True`
- forbidden credential-like bytes absent: `True`
- private modes: `True`

## Artifact

- boot image: `tmp/wifi/v1625-pm-service-shutdown-list-test-boot/boot_linux_v1625_wifi_test.img`
- boot sha256: `8a9370fe4ed60f30eed044bd7b6d79d428106033856934b7d27c9e102939757b`
- ramdisk sha256: `cf263c778a28b3a63d7971499897a0bb1be1786c7a74b87add520d41d429998e`
- init sha256: `f20fb78c5e0891b593cc2f22e828c99ed380282b4a02f4725b24f2fbefd93642`
- helper sha256: `d58f637ce53b12f16f7143b388b20007553fe8d47bd6ed06379bde96a69c8798`
- helper marker: `a90_android_execns_probe v303`

## Safety Scope

No device command, flash, reboot, boot partition write, partition write, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC direct write, blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind was performed by this verifier.

## Next

A later rollbackable live handoff may flash only the V1625 image, verify shutdown-critical-list requests are accepted by the property shim, collect `pm_service_system_info_surface.*`, then roll back to `stage3/boot_linux_v724.img` and verify selftest `fail=0`.
