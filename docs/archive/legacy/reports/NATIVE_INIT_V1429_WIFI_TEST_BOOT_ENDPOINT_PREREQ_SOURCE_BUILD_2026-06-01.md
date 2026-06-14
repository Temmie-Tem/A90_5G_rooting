# Native Init V1429 Wi-Fi Test Boot Endpoint Prerequisite Source Build

## Summary

- Cycle: `V1429`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1429-wifi-test-boot-endpoint-prereq-source-build-pass`
- Result: PASS
- Base boot: `stage3/boot_linux_v724.img`
- Test image: `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/boot_linux_v1429_wifi_test.img`
- Native init: `0.9.78 (v1429-wifitest)`
- Evidence: `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/manifest.json`

## Build Outputs

| Artifact | Path | SHA256 |
| --- | --- | --- |
| init | `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/init_v1429_wifi_test` | `ec378b1c6aa11ffe7707336caf46d27edef42ea1801bc847d67a5129b03a7e5b` |
| helper | `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/a90_android_execns_probe_v286` | `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f` |
| ramdisk | `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/ramdisk_v1429_wifi_test.cpio` | `123cf67fd74e88f306e017f750d880de2f64e950d9d2fc2e96a89ecec9c31f64` |
| boot image | `tmp/wifi/v1429-wifi-test-boot-endpoint-prereq-sampler/boot_linux_v1429_wifi_test.img` | `2b45f319d6b060ca7f65a17a839d34ee09b54f210a13ad9ca2f4d42bd334a9d4` |

## Test-Boot Contract

| Field | Value |
| --- | --- |
| label | `v1429` |
| mount debugfs | `True` |
| PID1 RC1 watcher | `True` |
| watcher delay | `250ms` |
| window sampler | `True` |
| endpoint sampler | `True` |
| RC1 retry count | `0` |
| watcher result | `/cache/native-init-wifi-test-boot-v1429-rc1-watcher.result` |
| window result | `/cache/native-init-wifi-test-boot-v1429-rc1-window.result` |

V1429 keeps the rollbackable Wi-Fi test boot shape but stops widening the RC1
retry count. The new endpoint sampler is read-only and records the surfaces
identified by V1428 around the corrected-RC1 window: GPIO102/PERST,
GPIO103/CLKREQ, GPIO104/WAKE, `pcie_1_gdsc`, pcie1 refclk/pipe clocks,
GPIO142/MDM2AP IRQ, pcie1 link state files, and LTSSM terminal state.

## Safety Scope

This cycle was source/build-only. It did not contact the device, flash, reboot,
write partitions, handle credentials, scan/connect Wi-Fi, run DHCP/routes, ping
externally, write PMIC/GPIO/GDSC controls, spoof eSoC notify/`BOOT_DONE`, run
global PCI rescan, or bind/unbind platform devices.

## Validation

```bash
python3 -m py_compile scripts/revalidation/build_native_init_wifi_test_boot_v1393.py scripts/revalidation/build_native_init_wifi_test_boot_v1429.py
python3 scripts/revalidation/build_native_init_wifi_test_boot_v1429.py
```

The build verified static aarch64 init/helper binaries, required boot-image
markers, ramdisk entries including `/bin/a90_tcpctl`, and forbidden
credential-like byte absence.

## Next Gate

V1430 should be local-only artifact sanity for this exact V1429 manifest and
marker contract before any rollbackable live handoff. V1431 may live-test only
after V1430 passes and must roll back to v724/selftest afterward.
