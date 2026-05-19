# v311 Plan: Property Context Mapping Proof

- date: `2026-05-19`
- scope: host-only `property_contexts` mapping proof for selected seed keys
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v310 proved the serializer/parser mechanics with a synthetic context. v311 maps
the selected Android-backed property seed keys through captured Android
`property_contexts` and regenerates a context-aware `property_info` binary.

This is still host-only. It does not install generated files on the device.

## Inputs

- `tmp/wifi/v301-property-shim-seed-android/seed.json`
- `tmp/wifi/v295-property-snapshot-live-20260519-142740/manifest.json`
- `tmp/wifi/v310-property-serializer-proof/manifest.json`

## Key Checks

1. Captured `property_contexts` evidence is present.
2. v310 serializer proof is present.
3. Every selected seed key maps to a context/type.
4. Generated context-aware `property_info` parses back to the same context/type
   for each selected key.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_property_context_mapping_proof.py
python3 scripts/revalidation/wifi_property_context_mapping_proof.py \
  --out-dir tmp/wifi/v311-property-context-mapping-proof \
  run
git diff --check
```

Expected result:

```text
property-context-mapping-ready
```

## Acceptance

- Host-only execution only.
- No device command and no ADB command.
- No runtime install of generated files.
- Mapping result identifies exact source context line for each selected key.
- Next step is a private runtime layout package dry-run, not live install.

