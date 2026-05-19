# v307 Plan: Property Shim Design Model

- date: `2026-05-19`
- scope: host-only property shim design model from Android-backed seed
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v307 consumes the Android-backed v301 property seed and produces a design matrix
for future property shim work. It does not create `/dev/__properties__`, does
not create `/dev/socket/property_service`, and does not execute service-manager,
HAL, CNSS, or Wi-Fi daemons.

The result should answer which shim path is safest to prototype next and which
proofs are still missing.

## Background

AOSP property access is not a simple environment variable lookup. Bionic exposes
`sys/system_properties.h` APIs, property data is backed by a property area under
`/dev/__properties__`, and writes go through property service sockets. Android
also treats cross-partition properties as API-governed sysprops on modern
versions.

References:

- AOSP sysprop API overview: <https://source.android.com/docs/core/architecture/configuration/sysprops-apis>
- AOSP property service source: <https://android.googlesource.com/platform/system/core.git/+/master/init/property_service.cpp>
- Bionic system property API header: <https://android.googlesource.com/platform/bionic/+/master/libc/include/sys/system_properties.h>

## Candidate Designs

1. `analysis-only-seed`
   - use captured property values only for host-side decisions;
   - zero runtime risk;
   - insufficient if a bionic daemon actively calls `property_get`.
2. `private-readonly-property-area`
   - create a private, non-global property area only inside a controlled helper
     namespace;
   - no global `/dev/__properties__` mutation;
   - requires proof that the property area format and property info files match
     this Android build.
3. `ld-preload-property-get-shim`
   - intercept selected property APIs for one process;
   - avoids property area creation;
   - high linker/ABI risk and only valid if the target binary accepts preload in
     the private Android namespace.
4. `minimal-property-service-socket`
   - emulate read/write property service socket behavior;
   - highest scope and security risk;
   - not selected for early Wi-Fi work.

## Key Changes

- Add `scripts/revalidation/wifi_property_shim_design.py`.
- Inputs:
  - `tmp/wifi/v301-property-shim-seed-android/seed.json`
  - optional v297/v298/v306 manifests for evidence context
- Output:
  - design matrix;
  - selected next prototype;
  - blocked actions;
  - proof checklist for the selected design.

## Decision Policy

- If the Android-backed seed is missing or blocked, decision is
  `property-shim-design-waiting-for-seed`.
- If seed is ready, decision is `property-shim-design-model-ready`.
- Preferred next prototype is `private-readonly-property-area`, but only as a
  separate future plan. v307 does not implement it.
- `minimal-property-service-socket` is explicitly deferred.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_property_shim_design.py
python3 scripts/revalidation/wifi_property_shim_design.py \
  --out-dir tmp/wifi/v307-property-shim-design \
  run
git diff --check
```

Expected with v301 Android-backed seed: `property-shim-design-model-ready`.

## Acceptance

- v307 is host-only and does not touch the device.
- The selected next step is clearly separated from implementation.
- The model records all blocked actions, especially global property runtime
  creation and Wi-Fi daemon execution.
- The next prototype plan can be derived from explicit proof requirements.
