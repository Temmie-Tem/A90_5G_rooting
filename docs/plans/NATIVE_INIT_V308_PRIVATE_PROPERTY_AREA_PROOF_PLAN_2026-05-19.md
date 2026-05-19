# v308 Plan: Private Property Area Proof Model

- date: `2026-05-19`
- scope: host-only proof model for private read-only Android property area
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v308 consumes the Android-backed v301 property seed and the v297 Android
runtime capture to decide whether the next `private-readonly-property-area`
prototype has enough proof to proceed.

The answer is deliberately fail-closed: v308 validates seed values and safety
scope, but it must not create `/dev/__properties__`, must not create
`/dev/socket/property_service`, and must not run service-manager, HAL, CNSS, or
Wi-Fi daemons.

## Inputs

- `tmp/wifi/v301-property-shim-seed-android/seed.json`
- `tmp/wifi/v297-android-property-capture-android/manifest.json`
- `tmp/wifi/v307-property-shim-design/manifest.json`

## Key Checks

1. Selected seed keys are present, `ready`, non-empty, and conservative
   `PROP_VALUE_MAX` compatible.
2. Selected keys are read-only `ro.*` keys only.
3. v297 Android capture shows the Android property runtime state.
4. v307 selected `private-readonly-property-area` as the next prototype.
5. Property area binary file layout and serialized `property_info`
   compatibility are explicitly marked unproven unless evidence exists.

## Expected Decision

Expected current result:

```text
private-property-area-proof-needs-format-source
```

This means the Android-backed seed is valid, but the repo still lacks an
AOSP-source-backed proof that a private property area and property info files
can satisfy the target bionic property lookup path.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_area_proof.py
python3 scripts/revalidation/wifi_private_property_area_proof.py \
  --out-dir tmp/wifi/v308-private-property-area-proof \
  run
git diff --check
```

## Acceptance

- Host-only execution only.
- No boot image, device command, ADB command, `/dev` node, socket, daemon, or
  Wi-Fi state mutation.
- The report records whether the next step is runtime prototype or source/format
  proof.
- If format proof is missing, the next step remains a non-runtime AOSP format
  extractor/proof model.

## Blocked Actions

- Create global `/dev/__properties__`.
- Create `/dev/socket/property_service`.
- Write `persist.*`, `ctl.*`, or any mutable property.
- Start service-manager, hwservicemanager, Wi-Fi HAL, `wificond`,
  `supplicant`, `hostapd`, CNSS, or diag daemon.
- Wi-Fi scan/connect/link-up/credential/DHCP/routing.

