# Native Init V1604 per_mgr Startup Trace Source Build

## Summary

- Cycle: `V1604`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1604-per-mgr-startup-trace-test-boot-source-build-pass`
- Result: PASS
- Reason: built the V1602 route with helper v298 and a bounded `per_mgr` startup trace after the proven PPH modem-fd gate
- Manifest: `tmp/wifi/v1604-per-mgr-startup-trace-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1604-per-mgr-startup-trace-test-boot/boot_linux_v1604_wifi_test.img`
- Boot SHA256: `eb8d1dc11656a8380180b96239d9fe9c8ba160f55f1ca3ff34a8552a6438cca8`
- Init: `A90 Linux init 0.9.106 (v1604-per-mgr-startup-trace)`
- Init SHA256: `c3b3d850cba6d71363b479a8bd0b53dce356df3f908f06b741de237a6abaa80d`
- Helper marker: `a90_android_execns_probe v298`
- Helper SHA256: `6a56b15650fe5c7785a878e7f86ade8e9c323e33cfb8c049952388022592d898`

## Delta From V1600

- Bumps `a90_android_execns_probe` to v298.
- Preserves the V1600 PM-first late-per-proxy PPH-gated lower-marker route.
- Adds `--allow-android-wifi-service-window-per-mgr-startup-trace`.
- Samples `per_mgr` every 20ms for 1s after spawn, recording liveness, state, cmdline, cwd, wchan, exit timing, and fd counts for `/dev/subsys_modem`, `/dev/subsys_esoc0`, binder nodes, sockets, and `/dev/socket`.
- Keeps Wi-Fi HAL/`wificond`, direct scoped `/dev/subsys_esoc0`, credentials, scan/connect, DHCP/routes, external ping, PMIC/GPIO/GDSC writes, blind eSoC notify/`BOOT_DONE`, global PCI rescan, and platform bind/unbind disabled.

## Test-Boot Contract

- Log path: `/cache/native-init-wifi-test-boot-v1604.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1604.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1604-helper.result`
- Supervisor timeout sec: `130`
- Helper runtime mode: `wifi-companion-android-wifi-service-window-subsys-trigger-capture`
- Firmware mounts: `True`
- Android service window: `True`

## Verification

- Static init and helper verification passed.
- Ramdisk entries include `/init`, `/bin/a90_android_execns_probe`, `/bin/a90_tcpctl`, and `/bin/a90_rshell`.
- Boot image marker verification passed, including the V1604 per_mgr startup trace markers.
- Forbidden credential-like byte scan over init/helper/ramdisk/boot image passed.

## Safety Scope

This build script was source/build-only. It did not issue device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan/platform bind-unbind, or write device partitions.

## Next

V1605 should run local artifact sanity over this exact manifest.  If it passes, V1606 can perform a rollbackable live handoff that flashes only the V1604 image, collects helper result/lower markers/dmesg/`wlan0`, rolls back to `stage3/boot_linux_v724.img`, and verifies native selftest `fail=0`.
