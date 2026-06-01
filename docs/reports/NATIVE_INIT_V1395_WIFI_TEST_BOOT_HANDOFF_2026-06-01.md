# Native Init V1395 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1395`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1395-test-boot-provider-trigger-no-downstream-rollback-pass`
- Result: PASS
- Reason: test boot reached the esoc0 provider trigger and rollback verified, but no RC1/MHI/WLFW/wlan0 progress marker appeared
- Evidence: `tmp/wifi/v1395-wifi-test-boot-handoff`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner. Device mutation was limited to flashing the
V1393 test boot image and rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1393-wifi-test-boot/boot_linux_v1393_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Key Evidence

- Test boot verified as `A90 Linux init 0.9.69 (v1393-wifitest)`.
- PID1 test hook spawned the ramdisk helper and wrote
  `/cache/native-init-wifi-test-boot-v1393.log`.
- Dmesg showed `pm_proxy_helper` opening `subsys_modem` and Binder reaching
  `__subsystem_get: esoc0`.
- Dmesg did not show RC1 L0, MHI pipe/device, WLFW `FW ready`, BDF, or `wlan0`
  progress.
- `/sys/class/net/wlan0` was absent.
- Rollback to `A90 Linux init 0.9.68 (v724)` verified through `version/status`.

## Interpretation

The test boot moves the helper into early PID1 flow and reaches the eSoC
provider path, but V1395 collected and rolled back immediately after bridge
verification. Because the helper timeout window is `30s`, the next live gate
should hold the V1393 test boot longer before collecting evidence and rollback.

## Next

V1396 should rerun the same test boot with an explicit post-boot hold window
before rollback. It must still avoid Wi-Fi scan/connect, credential handling,
DHCP/routes, and external ping.
