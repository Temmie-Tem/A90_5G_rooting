# Native Init v311 Property Context Mapping Report

- date: `2026-05-19`
- scope: host-only `property_contexts` mapping proof for selected seed keys
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V311_PROPERTY_CONTEXT_MAPPING_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_property_context_mapping_proof.py`

## Summary

v311 parsed captured Android `property_contexts`, mapped the selected
Android-backed seed keys to real context/type entries, generated a
context-aware `property_info` binary, and verified parser roundtrip.

The result is ready for a host-only private runtime layout package dry-run. It
does not authorize device install or daemon execution.

## Evidence

| item | path | result |
| --- | --- | --- |
| context mapping proof | `tmp/wifi/v311-property-context-mapping-proof/` | `property-context-mapping-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_property_context_mapping_proof.py
python3 scripts/revalidation/wifi_property_context_mapping_proof.py \
  --out-dir tmp/wifi/v311-property-context-mapping-proof \
  run
git diff --check
```

Result: PASS.

## Mappings

| key | context | type | source |
| --- | --- | --- | --- |
| `ro.build.version.sdk` | `u:object_r:build_prop:s0` | `int` | `plat_property_contexts:711` |
| `ro.product.name` | `u:object_r:build_prop:s0` | `string` | `plat_property_contexts:785` |
| `ro.hardware` | `u:object_r:bootloader_prop:s0` | `string` | `plat_property_contexts:680` |
| `ro.vendor.build.version.sdk` | `u:object_r:build_vendor_prop:s0` | `int` | `plat_property_contexts:855` |

## Checks

| check | result |
| --- | --- |
| captured context input | PASS |
| selected key mapping | PASS |
| context-aware `property_info` roundtrip | PASS |
| runtime safety gate | PASS |

## Decision

- decision: `property-context-mapping-ready`
- reason: selected seed keys map through captured `property_contexts`.
- next step: v312 private property runtime layout package dry-run.

## Safety

- No device command execution.
- No ADB command execution.
- No runtime property file installation.
- No property service socket creation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

