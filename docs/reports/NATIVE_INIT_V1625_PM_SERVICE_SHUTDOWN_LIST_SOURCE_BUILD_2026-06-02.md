# Native Init V1625 pm-service Shutdown-list Source Build

## Summary

- Cycle: `V1625`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1625-pm-service-shutdown-list-test-boot-source-build-pass`
- Result: PASS
- Reason: built the V1621 route with helper v303 and android service-window shutdown-critical-list allowlist repair
- Manifest: `tmp/wifi/v1625-pm-service-shutdown-list-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1625-pm-service-shutdown-list-test-boot/boot_linux_v1625_wifi_test.img`
- Boot SHA256: `8a9370fe4ed60f30eed044bd7b6d79d428106033856934b7d27c9e102939757b`
- Init: `A90 Linux init 0.9.111 (v1625-pm-service-shutdown-list)`
- Init SHA256: `f20fb78c5e0891b593cc2f22e828c99ed380282b4a02f4725b24f2fbefd93642`
- Helper marker: `a90_android_execns_probe v303`
- Helper SHA256: `d58f637ce53b12f16f7143b388b20007553fe8d47bd6ed06379bde96a69c8798`

## Delta From V1621/V1624

- Bumps `a90_android_execns_probe` to v303.
- Preserves the PM-first late-per-proxy PPH-gated lower-marker route.
- Keeps private property-root materialization for android service-window modes.
- Enables the existing property-shim `vendor.peripheral.shutdown_critical_list` allowlist only for android service-window mode with `--allow-android-wifi-service-window`.
- Keeps scan/connect, credential handling, DHCP/routes, and external ping disabled.

## Test-Boot Contract

- Log path: `/cache/native-init-wifi-test-boot-v1625.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1625.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1625-helper.result`
- Supervisor timeout sec: `130`
- Helper runtime mode: `wifi-companion-android-wifi-service-window-subsys-trigger-capture`
- Firmware mounts: `True`
- Android service window: `True`

## Safety Scope

This build script was source/build-only. It did not issue device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan/platform bind-unbind, or write device partitions.

## Next

V1626 should run local artifact sanity over this exact manifest. If it passes, V1627 can perform a rollbackable live handoff to verify whether the shutdown-critical-list requests are accepted and whether `pm-service` advances beyond the OFFLINE-only path.
