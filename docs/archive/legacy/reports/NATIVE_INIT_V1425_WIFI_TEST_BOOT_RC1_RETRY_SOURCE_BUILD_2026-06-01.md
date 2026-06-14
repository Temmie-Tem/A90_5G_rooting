# Native Init V1425 Wi-Fi Test Boot RC1 Retry Source Build

## Summary

- Cycle: `V1425`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1425-wifi-test-boot-rc1-retry-source-build-pass`
- Result: PASS
- Artifact:
  - `tmp/wifi/v1425-wifi-test-boot-rc1-retry/boot_linux_v1425_wifi_test.img`
  - `tmp/wifi/v1425-wifi-test-boot-rc1-retry/manifest.json`

## Build Identity

- Native init marker: `A90 Linux init 0.9.77 (v1425-wifitest)`
- Helper: `tmp/wifi/v1425-wifi-test-boot-rc1-retry/a90_android_execns_probe_v286`
- Init SHA256: `776c14662a56c7667e35bc2af0f32ee493315445f6c1c7d40c4bc59fc1b8b2ce`
- Helper SHA256: `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f`
- Ramdisk SHA256: `395e71c3abc97b053601e1349f547c2747afe61359cc07f3cebe08db1324318e`
- Boot image SHA256: `1d1b0cc73e0b32fee7081d7cc545220561932bfff6da4ac9cad5ccec2d9c1379`

## Change

V1425 preserves the V1420 delayed corrected-RC1 path and adds a bounded retry
policy after the first corrected RC1 write:

- initial corrected RC1 write after the existing `250ms` delay;
- retry count: `2`;
- retry delay: `500ms`;
- retry result fields appended to the PID1 RC1 watcher result;
- retry log lines appended to the Wi-Fi test boot log.

This is still below Wi-Fi connect. The intent is to test whether the endpoint
appears later after the first post-PERST link failure, without changing
credentials, scan/connect, DHCP/routes, or external ping behavior.

## Contract

Manifest `wifi_test` confirms:

- `label`: `v1425`
- `pid1_rc1_watcher`: `true`
- `rc1_watcher_delay_ms`: `250`
- `rc1_window_sampler`: `true`
- `rc1_retry_count`: `2`
- `rc1_retry_delay_ms`: `500`
- `rc1_watcher_result`: `/cache/native-init-wifi-test-boot-v1425-rc1-watcher.result`
- `rc1_window_result`: `/cache/native-init-wifi-test-boot-v1425-rc1-window.result`
- `mount_debugfs`: `true`
- `fresh_log`: `true`
- `supervise_helper`: `true`

## Validation

- Static aarch64 init and helper artifacts were produced.
- `readelf -d` showed no interpreter or dynamic dependency entries for the
  staged init/helper binaries.
- Boot image marker verification passed through the build script.
- Manifest was written with V1425 identity, hashes, and retry contract.

## Safety Scope

This was a host/source/build-only cycle. It did not run live device commands,
flash or reboot the device, write partitions, handle credentials, scan/connect
Wi-Fi, start Wi-Fi HAL, run DHCP/routes, perform external ping, write
PMIC/GPIO/GDSC controls, spoof eSoC notify/`BOOT_DONE`, run global PCI rescan,
or bind/unbind platform devices.

The generated artifact contains additional pci-msm corrected-RC1 test writes,
but they are staged only for a future explicit rollbackable test-boot handoff.

## Next Gate

V1426 should sanity-check this exact artifact before any live handoff. If V1426
passes, V1427 may run a rollbackable live handoff and classify whether the
second or third RC1 attempt reaches L0/MHI/WLFW/`wlan0`.
