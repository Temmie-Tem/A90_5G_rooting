# Native Init v295 Read-Only Property Snapshot Model Plan

- date: `2026-05-19`
- scope: read-only Android property snapshot model
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/wifi_property_snapshot_model.py`
- prerequisite: v294 decision `property-runtime-inputs-visible-runtime-absent`

## Summary

v294 proved that Android property input files are visible but live property
runtime paths are absent. v295 builds a host-side read-only property snapshot
from mounted Android input files. It answers whether there is enough static
property material to design a future property shim without running Android init's
property service.

v295 does not create `/dev/socket`, `/dev/__properties__`, or any serialized
property area. It does not mutate properties and does not execute
service-manager or Wi-Fi daemons.

## Inputs

- v294 property runtime feasibility manifest
- live read-only captures:
  - mounted `build.prop`, `default.prop`, and `prop.default` files
  - mounted `*_property_contexts` files

## Snapshot Content

- parsed property key/value pairs from readable property files
- counts for:
  - total properties
  - `ro.*`
  - `ro.vendor.*`
  - Wi-Fi/WLAN/CNSS/QCOM-related properties
- parsed property-context line count
- property-context files that are visible
- required/key baseline presence:
  - `ro.build.version.sdk`
  - `ro.product.name`
  - `ro.hardware`
  - `ro.vendor.build.version.sdk`

## Guardrails

- No property service creation.
- No `/dev/socket` or `/dev/__properties__` writes.
- No property value mutation.
- No service-manager execution.
- No Binder ioctl or Binder devnode creation.
- No Wi-Fi daemon execution.
- No QMI/QRTR packet.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No Android partition write.

## Expected Decisions

PASS decisions:

- `property-snapshot-model-ready`
- `property-snapshot-inputs-partial`

Failure decisions:

- `property-snapshot-input-missing`
- `property-snapshot-native-capture-failed`

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_property_snapshot_model.py \
  scripts/revalidation/wifi_property_runtime_feasibility.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Live read-only:

```bash
python3 scripts/revalidation/wifi_property_snapshot_model.py \
  --out-dir tmp/wifi/v295-property-snapshot-live-$(date +%Y%m%d-%H%M%S) \
  run
```

## Acceptance

- The tool parses static property files without writing to the device.
- The tool reports whether a future property shim has enough static inputs to
  seed read-only lookups.
- Runtime service-manager execution remains blocked unless a separate shim plan
  explicitly defines property area/socket behavior.
