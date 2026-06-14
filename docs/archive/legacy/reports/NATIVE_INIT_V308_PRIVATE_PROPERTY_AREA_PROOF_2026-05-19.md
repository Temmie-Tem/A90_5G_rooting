# Native Init v308 Private Property Area Proof Report

- date: `2026-05-19`
- scope: host-only proof model for private read-only Android property area
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V308_PRIVATE_PROPERTY_AREA_PROOF_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_private_property_area_proof.py`

## Summary

v308 validates that the Android-backed property seed is usable as a read-only
model input, but blocks any runtime private property area prototype until the
exact property area and `property_info` formats are proven.

## Evidence

| item | path | result |
| --- | --- | --- |
| proof model | `tmp/wifi/v308-private-property-area-proof/` | `private-property-area-proof-needs-format-source` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_area_proof.py
python3 scripts/revalidation/wifi_private_property_area_proof.py \
  --out-dir tmp/wifi/v308-private-property-area-proof \
  run
git diff --check
```

Result: PASS.

## Seed Validation

| key | status | source | value length |
| --- | --- | --- | --- |
| `ro.build.version.sdk` | pass | static+android-match | `2` |
| `ro.product.name` | pass | android-capture | `5` |
| `ro.hardware` | pass | android-capture | `4` |
| `ro.vendor.build.version.sdk` | pass | android-capture | `2` |

## Proof Checks

| check | status | interpretation |
| --- | --- | --- |
| `android-backed-seed` | pass | selected seed keys are present, read-only, and within conservative value limits |
| `capture-provenance` | pass | v297 Android property capture is available |
| `design-selection` | pass | v307 selected `private-readonly-property-area` |
| `private-readonly-scope` | pass | model excludes mutable properties and global `/dev` mutation |
| `android-property-area-format` | not-proven | Android capture did not expose usable property area files |
| `property-info-compatibility` | not-proven | serialized `property_info` compatibility is not proven |
| `runtime-safety-gate` | pass | no runtime or device mutation was performed |

## Decision

- decision: `private-property-area-proof-needs-format-source`
- reason: seed is valid, but property area and `property_info` format proof is
  missing.
- next step: v309 AOSP property area/property info format extractor.

## Safety

- No device command execution.
- No ADB command execution.
- No property runtime node creation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## References

- <https://source.android.com/docs/core/architecture/configuration/sysprops-apis>
- <https://android.googlesource.com/platform/system/core.git/+/master/init/property_service.cpp>
- <https://android.googlesource.com/platform/bionic/+/master/libc/include/sys/system_properties.h>

