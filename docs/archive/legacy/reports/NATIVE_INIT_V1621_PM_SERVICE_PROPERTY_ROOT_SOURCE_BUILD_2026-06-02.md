# Native Init V1621 pm-service Property-root Source Build

## Summary

- Cycle: `V1621`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1621-pm-service-property-root-test-boot-source-build-pass`
- Result: PASS
- Reason: built the V1617 route with helper v302 and private property-root materialization repair
- Manifest: `tmp/wifi/v1621-pm-service-property-root-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1621-pm-service-property-root-test-boot/boot_linux_v1621_wifi_test.img`
- Boot SHA256: `52a56bc02787f2f72c44fad60aae6d8e4ca619135393798425e9d802f7d1c635`
- Init: `A90 Linux init 0.9.110 (v1621-pm-service-property-root)`
- Init SHA256: `0e951f5839fd450610cad6e6026bd243ab87c178fd9e4c339b7d1f1977afe700`
- Helper marker: `a90_android_execns_probe v302`
- Helper SHA256: `09732d4469d963e3c14ecb50f6f01341e92adfd3370c614d2ce779a71510230c`

## Delta From V1617/V1620

- Bumps `a90_android_execns_probe` to v302.
- Preserves the PM-first late-per-proxy PPH-gated lower-marker route.
- Keeps the non-ptrace `per_mgr` startup/context branch.
- Keeps `--allow-android-wifi-service-window-per-mgr-system-info-surface` and repairs private property-root materialization for android service-window modes.
- Captures read-only `pm_service_system_info_surface.*` snapshots before and after `per_mgr` startup tracing.

## Materialized Surface

- `/sys/bus/msm_subsys/devices`
- `/sys/bus/esoc/devices`
- `/sys/class/esoc-dev`
- `/dev/subsys_*`, `/dev/esoc-*`, `/dev/vndbinder`, `/dev/binder`, `/dev/hwbinder`
- private property root, property-service socket, and service-manager sockets

## Test-Boot Contract

- Log path: `/cache/native-init-wifi-test-boot-v1621.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1621.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1621-helper.result`
- Supervisor timeout sec: `130`
- Helper runtime mode: `wifi-companion-android-wifi-service-window-subsys-trigger-capture`
- Firmware mounts: `True`
- Android service window: `True`

## Safety Scope

This build script was source/build-only. It did not issue device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan/platform bind-unbind, or write device partitions.

## Next

V1622 should run local artifact sanity over this exact manifest. If it passes, V1623 can perform a rollbackable live handoff to verify `/dev/__properties__` is present in the private namespace and reclassify the `pm-service` OFFLINE-only boundary.
