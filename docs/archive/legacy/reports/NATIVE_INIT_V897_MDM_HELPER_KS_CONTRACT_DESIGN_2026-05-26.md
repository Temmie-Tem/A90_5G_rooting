# V897 Native mdm_helper/ks Contract Design Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v897-mdm-helper-ks-contract-design/manifest.json` | `v897-mdm-helper-ks-contract-build-needed` |

V897 confirms that the current native helper only has old service-gated
`mdm_helper` start modes. It does not yet implement Android's required
pre-subsys `mdm_helper`/`ks` image/link contract.

## Implementation

- Added classifier:
  `scripts/revalidation/native_wifi_mdm_helper_ks_contract_design_v897.py`
- Evidence:
  `tmp/wifi/v897-mdm-helper-ks-contract-design/summary.md`
- Latest pointer:
  `tmp/wifi/latest-v897-mdm-helper-ks-contract-design.txt`
- The classifier is host-only. It does not contact the device.

## Findings

- V896 is the positive-control contract:
  Android reaches `mdm3=ONLINE`, WLFW/BDF/`wlan0`, and GPIO 142 IRQ count `1`
  while `mdm_helper` plus `ks` hold `/dev/esoc-0`.
- V895 is the negative control:
  native observed `ESOC_REQ_IMG`, sent `ESOC_IMG_XFER_DONE`, kept
  `GET_STATUS=0`, withheld `BOOT_DONE`, and saw GPIO 142 IRQ delta `0`.
- V764 proves the old service-gated `mdm_helper` start did not advance lower
  state.
- V855 proves node parity for `/dev/esoc-0`, `/dev/subsys_esoc0`, and
  `/dev/subsys_modem` is available as a building block.
- V867 proves PeripheralManager alone is not sufficient and can leave residual
  actor cleanup risk.
- Current helper `v143` has service-gated `mdm_helper` modes and the
  conditional eSoC response mode, but lacks:
  - a distinct `mdm_helper` image-contract mode;
  - explicit `/vendor/bin/ks` execution/observation logic;
  - `/dev/mhi_0305_01.01.00_pipe_10` visibility handling;
  - enforced `mdm_helper` before `/dev/subsys_esoc0` ordering.

## Interpretation

The next implementation should not retry blind `IMG_XFER_DONE`, blind
`BOOT_DONE`, service-gated `mdm_helper`, or generic command-engine expansion.
The Android order is more specific: node parity, `mdm_helper` first, subsystem
open second, then observe whether `ks` and MHI pipe/image handling appear.

Existing Android dmesg/IRQ evidence already answered the Magisk-module style
question for V896. No new Android handoff is required before implementing the
V898 source/build-only helper mode.

## Guardrails

- No device contact, Android boot, ADB command, Magisk module, live eSoC ioctl,
  subsystem open, actor start, `mdm_helper` start, `ks` start, daemon start,
  Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping,
  GPIO/sysfs/debugfs write, boot image write, partition write, firmware
  mutation, module load/unload, or Wi-Fi link-up occurred in V897.

## Next

V898 should add source/build-only helper support for a fail-closed
`mdm_helper`/`ks` image-contract mode. Deploy-only and bounded live proof must
remain separate cycles.
