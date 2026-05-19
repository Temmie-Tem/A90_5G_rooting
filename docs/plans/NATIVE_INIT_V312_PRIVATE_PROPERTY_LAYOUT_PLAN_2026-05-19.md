# v312 Plan: Private Property Runtime Layout Dry-run

- date: `2026-05-19`
- scope: host-only private `/dev/__properties__` layout dry-run
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v311 proved context-aware mapping for selected Android-backed seed keys. v312
builds the full private property runtime layout locally under `tmp/wifi`,
including:

- `property_info`;
- `properties_serial`;
- one `prop_area` file per required context.

This is still a dry-run. It does not push files, bind mount anything, create
global `/dev/__properties__`, create a property service socket, or start any
daemon.

## Key Changes

- Add `scripts/revalidation/wifi_private_property_layout_dryrun.py`.
- Consume v311 mappings.
- Generate a host-only layout rooted at:

```text
layout/dev/__properties__/
```

- Verify:
  - context filenames are safe single path components;
  - `property_info` maps keys to context/type;
  - each per-context `prop_area` returns the expected values.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_layout_dryrun.py
python3 scripts/revalidation/wifi_private_property_layout_dryrun.py \
  --out-dir tmp/wifi/v312-private-property-runtime-layout \
  run
git diff --check
```

Expected result:

```text
private-property-layout-dryrun-ready
```

## Acceptance

- Host-only execution only.
- No device command and no ADB command.
- Generated files remain local evidence artifacts.
- Next step is an explicit materialization approval packet, not automatic live
  install.

