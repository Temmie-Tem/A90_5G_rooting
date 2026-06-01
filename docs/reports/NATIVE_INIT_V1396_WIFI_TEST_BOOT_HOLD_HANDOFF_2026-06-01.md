# Native Init V1396 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1396`
- Type: bounded live test-boot handoff with explicit post-boot hold and rollback
- Decision: `v1396-test-boot-provider-trigger-no-downstream-rollback-pass`
- Result: PASS
- Reason: test boot reached the esoc0 provider trigger and rollback verified, but no RC1/MHI/WLFW/wlan0 progress marker appeared
- Evidence: `tmp/wifi/v1396-wifi-test-boot-hold-handoff`

V1396 reran the V1393 Wi-Fi test boot with a `40s` post-boot hold before
collecting evidence. This closes the main V1395 ambiguity: the absence of RC1,
MHI, WLFW/BDF, and `wlan0` is not explained by immediate collection/rollback
cutting off the helper's boot window.

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner. Device mutation was limited to flashing the
V1393 test boot image and rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1393-wifi-test-boot/boot_linux_v1393_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Observations

- Test boot reached `A90 Linux init 0.9.69 (v1393-wifitest)`.
- PID1 started the ramdisk-bundled helper early; dmesg showed
  `a90_android_exe` at about `1.956s`.
- The Android participant path reached `subsys_modem` at about `3.353s`.
- Binder reached `__subsystem_get: esoc0` at about `9.201s`.
- After the explicit hold, no `PCIe RC1`, `LTSSM`, `MHI`, `FW ready`, `BDF`, or
  `wlan0` marker appeared.
- `/sys/class/net/wlan0` remained absent.
- Rollback returned the device to `A90 Linux init 0.9.68 (v724)`.

## Interpretation

The test-boot approach is still useful: it removes host-side deploy/command
latency and proves the boot image can safely exercise the same lower provider
path and roll back. However, V1396 shows that moving the helper into PID1/ramdisk
does not by itself produce the downstream RC1/MHI/WLFW transition.

The next blocker is observability inside the PID1-launched helper path. The
current `/cache/native-init-wifi-test-boot-v1393.log` is append-only and does
not preserve a clean per-boot helper transcript. The next source/build cycle
should make the test boot write a fresh per-boot log or summary so the helper's
own decision keys can be compared against the external-helper runs.

## Next

V1397 should be source/build-only: improve the V1393 test-boot hook logging by
truncating or rotating the per-boot log, capturing helper stdout/stderr or a
dedicated summary, and recording helper exit/completion without blocking PID1
long term. Do not proceed to Wi-Fi scan/connect, credentials, DHCP/routes, or
external ping until `wlan0`/WLFW progress is proven.
