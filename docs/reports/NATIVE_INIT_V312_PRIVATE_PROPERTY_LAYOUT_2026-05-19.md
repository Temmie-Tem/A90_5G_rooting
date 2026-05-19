# Native Init v312 Private Property Runtime Layout Report

- date: `2026-05-19`
- scope: host-only private `/dev/__properties__` layout dry-run
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V312_PRIVATE_PROPERTY_LAYOUT_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_private_property_layout_dryrun.py`

## Summary

v312 generated a local private property runtime layout and verified that the
selected Android-backed seed keys roundtrip through context-aware
`property_info` plus per-context `prop_area` files.

This remains host-only. No generated file was installed on the device.

## Evidence

| item | path | result |
| --- | --- | --- |
| layout dry-run | `tmp/wifi/v312-private-property-runtime-layout/` | `private-property-layout-dryrun-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_layout_dryrun.py
python3 scripts/revalidation/wifi_private_property_layout_dryrun.py \
  --out-dir tmp/wifi/v312-private-property-runtime-layout \
  run
git diff --check
```

Result: PASS.

## Generated Layout

| role | relative path | size |
| --- | --- | --- |
| `property_info` | `layout/dev/__properties__/property_info` | `700` bytes |
| `properties_serial` | `layout/dev/__properties__/properties_serial` | `131072` bytes |
| `prop_area` | `layout/dev/__properties__/u:object_r:bootloader_prop:s0` | `131072` bytes |
| `prop_area` | `layout/dev/__properties__/u:object_r:build_prop:s0` | `131072` bytes |
| `prop_area` | `layout/dev/__properties__/u:object_r:build_vendor_prop:s0` | `131072` bytes |

## Checks

| check | result |
| --- | --- |
| v311 prerequisite | PASS |
| context filenames | PASS |
| layout roundtrip | PASS |
| runtime safety gate | PASS |

## Decision

- decision: `private-property-layout-dryrun-ready`
- reason: private property runtime layout generated and roundtripped on host.
- next step: v313 private property runtime materialization approval packet.

## Safety

- No device command execution.
- No ADB command execution.
- No generated runtime file installation.
- No bind mount over `/dev/__properties__`.
- No property service socket creation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

