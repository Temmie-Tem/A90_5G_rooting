# Native Init V1288 TLMM/PCIe Observer Support

- generated: 2026-05-31
- cycle: V1288
- command: source/build-only
- decision: `v1288-tlmm-pcie-observer-build-pass`
- pass: true
- helper: `a90_android_execns_probe v270`
- stage3 binary: `stage3/linux_init/helpers/a90_android_execns_probe_v270`
- sha256: `f1748fdc9c64a748c3270cd02a2b9bb796065b79632849e7384c2f37910f6e88`
- size: `1319408`

## Scope

V1288 adds no-write observer support for the next bounded PM-service response
sampler. V1287 showed that PMIC9 shape is no longer the shortest blocker; the
next run needs better visibility into TLMM GPIO135/GPIO142 and PCIe GDSC state
deltas before considering any PMIC/GPIO mutation gate.

## Changes

- Bumped `stage3/linux_init/helpers/a90_android_execns_probe.c` to
  `a90_android_execns_probe v270`.
- Added `read_debugfs_gpio_number_line()` and
  `read_debugfs_gpio_number_block()` to scan `/sys/kernel/debug/gpio` for exact
  `gpio135`/`gpio142` target lines instead of only capturing the start of the
  broad GPIO range.
- Added per-sample fields for exact TLMM target line and block captures.
- Extended `scripts/revalidation/native_wifi_late_per_proxy_response_sampler_live_v1242.py`
  to parse and summarize the new target fields.
- Added `scripts/revalidation/native_wifi_tlmm_pcie_observer_support_v1288.py`
  as the source/build-only gate.

## Validation

| check | result |
| --- | --- |
| V1287 input manifest | pass |
| Python compile | pass |
| helper build | pass |
| static aarch64 | pass |
| no interpreter | pass |
| no dynamic section | pass |
| required source strings | pass |
| required binary strings | pass |
| device commands | not executed |
| Wi-Fi bring-up | not executed |

Evidence:

- `tmp/wifi/v1288-execns-helper-v270-build/manifest.json`
- `tmp/wifi/v1288-execns-helper-v270-build/summary.md`
- `tmp/wifi/v1288-execns-helper-v270-build/logs/`

## Safety

No device command, deploy, PM actor, GPIO line request, PMIC write, direct eSoC
ioctl, Wi-Fi HAL start, scan/connect, credential use, DHCP/route change,
external ping, flash, boot image write, or partition write was executed by
V1288.

## Next

V1289 should deploy helper v270 only. V1290 should rerun the bounded no-write
TLMM/PCIe response sampler and classify whether `/sys/kernel/debug/gpio`
contains exact `gpio135`/`gpio142` target lines during the PM-service eSoC
window.
