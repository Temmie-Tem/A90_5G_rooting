# Native Init V427 Query Improvement Plan

Date: 2026-05-20

## Scope

V427 is a host-only planning step after V426.  It consumes the V425/V426
boot-complete Android evidence and decides the smallest safe improvement to the
native service-query path before any Wi-Fi bring-up.

V427 does not execute ADB, mutate the device, start daemons, enable Wi-Fi,
scan/connect/link-up, touch credentials, run DHCP, or change routing.

## Background

V425/V426 showed all three Samsung `ISehWifi/default` target rows in Android
boot-complete `lshal` output, but each target also had:

```text
cannot be fetched from service manager (null)
```

AOSP `lshal` source is important for interpreting this:

- `fetchBinderized()` lists services from `hwservicemanager`, then calls `get()`
  for each fqinstance; if `get()` returns null, `lshal` emits the warning above.
- `fetchManifestHals()` separately emits VINTF manifest rows with service status
  `DECLARED`.
- `-V` prints VINTF origin flags (`DM`, `DC`, `FM`, `FC`).
- `-S` prints explicit service status (`alive`, `registered;dead`, `declared`,
  `N/A`).
- `--types` can split `binderized` and `vintf` sections.

Reference: `https://android.googlesource.com/platform/frameworks/native/+/013be5f/cmds/lshal/ListCommand.cpp`

## Implementation

```text
scripts/revalidation/wifi_v427_query_improvement_planner.py
```

Modes:

```text
plan: identify latest V426 evidence and record a no-device-command plan
run: classify target rows and produce V428 query-improvement options
```

## Expected Decision

Current expected result:

```text
v427-explicit-status-query-needed
```

This means target rows are present, but current evidence does not prove live
registration because all target rows have get-null warnings and the existing
columns do not include explicit `-S` service status.

## Recommended Next Step

V428 should be an explicit status-column probe, still bounded and not Wi-Fi
bring-up:

1. Native control: `/system/bin/lshal list --types=vintf --neat -V -S -i`
   inside the private namespace, no HAL start required.
2. Native composite query: `/system/bin/lshal list --types=binderized,vintf --neat -V -S -i -p -e -c`
   under the existing bounded service-manager + Wi-Fi HAL start-only composite
   path.
3. Optional Android mirror: boot-complete Android read-only capture using the
   same explicit columns for comparison.

If explicit `-S` still shows declared/get-null rather than alive registration,
then the project should pivot toward Android-managed runtime control instead of
trying to recreate the full Android framework/supplicant/service-manager state
inside native init.
