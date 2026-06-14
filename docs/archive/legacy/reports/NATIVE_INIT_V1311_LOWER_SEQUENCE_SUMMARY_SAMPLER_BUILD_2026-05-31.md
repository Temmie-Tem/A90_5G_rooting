# Native Init V1311 Lower-Sequence Summary Sampler Build

## Summary

- Cycle: `V1311`
- Type: source/build-only helper support
- Decision: `v1311-lower-sequence-summary-sampler-build-pass`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1311-execns-helper-v275-build/manifest.json`
  - `tmp/wifi/v1311-execns-helper-v275-build/summary.md`
- Script: `scripts/revalidation/native_wifi_lower_sequence_summary_sampler_support_v1311.py`
- Helper: `a90_android_execns_probe v275`
- Built artifact: `stage3/linux_init/helpers/a90_android_execns_probe_v275`
- SHA256: `66e52e7507dd07bcb4071afd04bc60e51d1c6bb7b9cb7363205f1eb4f44d4677`
- Size: `1319408`

V1311 adds helper-side support for a stdout-reduced full-window lower-sequence sampler. It is not deployed and does not run on the device in this cycle.

## Added Helper Surface

| surface | value |
| --- | --- |
| helper marker | `a90_android_execns_probe v275` |
| new flag | `--pm-observer-late-per-proxy-lower-sequence-summary-sampler` |
| response mode | `late-per-proxy-lower-sequence-summary` |
| intended cadence | `80` samples at `50ms` |
| output contract | aggregate `response_summary.*` keys |

The new mode keeps the existing bounded late-`per_proxy` route, but avoids repeated per-sample PMIC/GDSC blocks that hit the `1MiB` helper stdout cap in V1309. It records aggregate lower-surface state:

- sample count and `mdm_subsys_powerup` presence;
- max MDM status IRQ, PCI, MHI, MHI pipe fd, and `ks` counts;
- `wlan0` presence;
- PCIe0/PCIe1 GDSC zero/nonzero status and first observed lines;
- PMIC soft-reset and TLMM GPIO135/GPIO142 first observed lines;
- safety markers proving no GPIO line request, PMIC write, or direct eSoC ioctl.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_lower_sequence_summary_sampler_support_v1311.py
python3 scripts/revalidation/native_wifi_lower_sequence_summary_sampler_support_v1311.py run
file stage3/linux_init/helpers/a90_android_execns_probe_v275
sha256sum stage3/linux_init/helpers/a90_android_execns_probe_v275
aarch64-linux-gnu-readelf -d stage3/linux_init/helpers/a90_android_execns_probe_v275
```

Build output is static aarch64 and has no dynamic section. The build log still contains existing old observer truncation warnings, but the build returned `rc=0`.

## Next

V1312 should deploy helper `v275` only. V1313 should run the bounded lower-sequence summary sampler live and verify the full 80-sample window completes without stdout truncation.

## Safety

- Source/build-only; no deploy or device command.
- No PMIC write, userspace GPIO request/hold, direct eSoC ioctl, PM/CNSS actor start, Wi-Fi HAL, scan/connect, credential use, DHCP/routes, external ping, flash, boot image write, or partition write occurred.
