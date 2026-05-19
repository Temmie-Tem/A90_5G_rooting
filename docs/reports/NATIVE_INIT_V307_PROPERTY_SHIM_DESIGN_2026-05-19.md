# Native Init v307 Property Shim Design Report

- date: `2026-05-19`
- scope: host-only property shim design model from Android-backed seed
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V307_PROPERTY_SHIM_DESIGN_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_property_shim_design.py`

## Summary

v307 consumes the Android-backed property seed produced after the v300 live
capture and produces a design matrix for future property shim work. The model is
host-only and does not create property runtime nodes or start Android services.

## Evidence

| item | path | result |
| --- | --- | --- |
| design model | `tmp/wifi/v307-property-shim-design/` | `property-shim-design-model-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_property_shim_design.py
python3 scripts/revalidation/wifi_property_shim_design.py \
  --out-dir tmp/wifi/v307-property-shim-design \
  run
git diff --check
```

Result: PASS.

## Seed Checks

| key | state | source |
| --- | --- | --- |
| `ro.build.version.sdk` | ready | static+android-match |
| `ro.product.name` | ready | android-capture |
| `ro.hardware` | ready | android-capture |
| `ro.vendor.build.version.sdk` | ready | android-capture |

## Candidate Decision

| candidate | status | risk | interpretation |
| --- | --- | --- | --- |
| `analysis-only-seed` | ready | low | usable for host-side decisions but cannot satisfy bionic runtime reads |
| `private-readonly-property-area` | preferred-next-prototype | medium | closest to bionic read path without global device mutation |
| `ld-preload-property-get-shim` | defer | medium-high | ABI/linker/preload behavior is unproven |
| `minimal-property-service-socket` | blocked | high | broader than current Wi-Fi start-only need |

Selected next prototype: `private-readonly-property-area`.

## Proof Requirements

- Prove expected bionic property area/property info file layout for this Android
  userspace.
- Keep property files inside a private helper namespace, not global native
  `/dev`.
- Read-only keys only; no `persist.*`, `ctl.*`, or property writes.
- No service-manager/HAL/Wi-Fi daemon execution during format proof.
- Separate explicit approval before any runtime node creation or daemon retry.

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
