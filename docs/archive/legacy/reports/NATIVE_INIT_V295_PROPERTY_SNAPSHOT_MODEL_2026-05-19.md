# Native Init v295 Read-Only Property Snapshot Model

- date: `2026-05-19`
- scope: read-only Android property snapshot model
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V295_PROPERTY_SNAPSHOT_MODEL_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_property_snapshot_model.py`
- evidence:
  - plan mode: `tmp/wifi/v295-property-snapshot-plan/`
  - live mode: `tmp/wifi/v295-property-snapshot-live-20260519-142740/`

## Result

- decision: `property-snapshot-model-ready`
- pass: `True`
- reason: static property and context inputs were parsed successfully.

## Validation

Static validation passed:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_property_snapshot_model.py \
  scripts/revalidation/wifi_property_runtime_feasibility.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Plan mode passed:

```bash
python3 scripts/revalidation/wifi_property_snapshot_model.py \
  --out-dir tmp/wifi/v295-property-snapshot-plan \
  plan
```

Live read-only mode passed:

```bash
python3 scripts/revalidation/wifi_property_snapshot_model.py \
  --out-dir tmp/wifi/v295-property-snapshot-live-20260519-142740 \
  run
```

## Snapshot

| Item | Value |
| --- | --- |
| property files parsed | `3` |
| property count | `248` |
| property context files parsed | `2` |
| property context line count | `1264` |
| Wi-Fi related property count | `7` |
| required baseline keys present | `1/4` |

Required baseline sample:

- `ro.build.version.sdk=31`
- `ro.hardware` absent
- `ro.product.name` absent
- `ro.vendor.build.version.sdk` absent

Wi-Fi related sample:

- `persist.data.df.iwlan_mux=9`
- `ro.setupwizard.wifi_on_exit=false`
- `ro.telephony.iwlan_operation_mode=legacy`
- `ro.wifi.channels=`
- `sys.qca1530=detect`

## Interpretation

The native environment can build a useful static property snapshot from mounted
Android files. This is enough to design a read-only lookup model, but it is not
a live Android property runtime:

- no `/dev/socket/property_service`;
- no `/dev/__properties__`;
- only `1/4` selected baseline runtime keys were present in static files.

Therefore service-manager execution remains blocked until a property shim or
captured Android-runtime property set is designed.

## Guardrails Kept

- no property service creation
- no `/dev/socket` or `/dev/__properties__` writes
- no property value mutation
- no service-manager execution
- no Binder ioctl or Binder devnode creation
- no Wi-Fi daemon execution
- no QMI/QRTR packet
- no Wi-Fi scan/connect/link-up/credential/DHCP/routing
- no Android partition write

## Next

- v296 should design a property shim strategy.
- The likely safe path is still model-only:
  - define which properties a service-manager dry-run would require;
  - compare static snapshot versus Android-boot captured properties;
  - avoid creating `/dev/__properties__` or a property socket until explicitly
    planned.
