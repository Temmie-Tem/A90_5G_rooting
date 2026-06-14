# Native Init V1433 Wi-Fi Test Boot Focused Endpoint Source Build

## Summary

- Cycle: `V1433`
- Type: source/build-only rollbackable Wi-Fi test boot artifact
- Decision: `v1433-wifi-test-boot-focused-endpoint-source-build-pass`
- Result: PASS
- Base boot: `stage3/boot_linux_v724.img`
- Test image: `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/boot_linux_v1433_wifi_test.img`
- Native init: `0.9.79 (v1433-wifitest)`
- Evidence: `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/manifest.json`

## Build Outputs

| Artifact | Path | SHA256 |
| --- | --- | --- |
| init | `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/init_v1433_wifi_test` | `9506ef3876e16ce55fa87289231dfcc4230c48d8c87c5cfffca284595f8d4392` |
| helper | `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/a90_android_execns_probe_v286` | `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f` |
| ramdisk | `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/ramdisk_v1433_wifi_test.cpio` | `5ba922e720e0dea6c31d880c236ab4e851bdf32452f20d12e59acc0bb0c7e89b` |
| boot image | `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/boot_linux_v1433_wifi_test.img` | `9093ac8d32d8189dbd754bd2152dd061bb30ac27c4a1d0a3abc5c9ca58b49c45` |

## Test-Boot Contract

| Field | Value |
| --- | --- |
| label | `v1433` |
| mount debugfs | `True` |
| PID1 RC1 watcher | `True` |
| watcher delay | `250ms` |
| window sampler | `True` |
| endpoint sampler | `True` |
| focused endpoint sampler | `True` |
| RC1 retry count | `0` |
| watcher result | `/cache/native-init-wifi-test-boot-v1433-rc1-watcher.result` |
| window result | `/cache/native-init-wifi-test-boot-v1433-rc1-window.result` |

V1433 keeps the V1429 rollbackable test-boot shape and adds focused exact-line
sampling for the endpoint prerequisite window. The broad sampler remains, but
additional `focused_*` records emit one exact line per pcie1 regulator, clock,
GPIO, pinmux, and pinconf needle. This is intended to remove the V1431
`clk_summary` truncation ambiguity before any new lower live mutation.

## Focused Surfaces

- `focused_regulator`: `pcie_1_gdsc`, `pcie_0_gdsc`, `pm8150l_l3`, `pm8150_l5`, `VDD_CX_LEVEL`
- `focused_clk`: `gcc_pcie_1_slv_q2a_axi_clk`, `gcc_pcie_1_slv_axi_clk`, `gcc_pcie_1_pipe_clk`, `gcc_pcie_1_mstr_axi_clk`, `gcc_pcie_1_clkref_clk`, `gcc_pcie_1_cfg_ahb_clk`, `gcc_pcie1_phy_refgen_clk`, `gcc_pcie_phy_refgen_clk_src`
- `focused_debug_gpio` / `focused_pinmux` / `focused_pinconf`: GPIO102/PERST, GPIO103/CLKREQ, GPIO104/WAKE, GPIO142/MDM2AP

## Safety Scope

This cycle was source/build-only. It did not contact the device, flash, reboot,
write partitions, handle credentials, scan/connect Wi-Fi, run DHCP/routes, ping
externally, write PMIC/GPIO/GDSC controls, spoof eSoC notify/`BOOT_DONE`, run
global PCI rescan, or bind/unbind platform devices.

## Validation

```bash
python3 -m py_compile scripts/revalidation/build_native_init_wifi_test_boot_v1393.py scripts/revalidation/build_native_init_wifi_test_boot_v1433.py
python3 scripts/revalidation/build_native_init_wifi_test_boot_v1433.py
```

The build verified static aarch64 init/helper binaries, required boot-image
markers, ramdisk entries including `/bin/a90_tcpctl`, and forbidden
credential-like byte absence.

## Next Gate

V1434 should perform local-only artifact sanity for this exact V1433 manifest
and focused marker contract before any rollbackable live handoff.
