# Native Init V427 Query Improvement Report

Date: 2026-05-20

## Scope

V427 adds a host-only planner for the next native service-query improvement.
It interprets V425/V426 evidence using AOSP `lshal` semantics and prevents a
false conclusion that V425 target rows alone prove live hwservice registration.

No ADB command, device mutation, daemon start, Wi-Fi enable, scan/connect/link-up,
credential, DHCP, or routing action was executed.

## Implementation

```text
scripts/revalidation/wifi_v427_query_improvement_planner.py
```

The planner:

- discovers the latest V426 manifest by default;
- follows the V426 input chain back to V425 and V423 command evidence;
- inspects each Samsung `ISehWifi/default` target line;
- detects `cannot be fetched from service manager (null)` warnings;
- emits ranked V428 query-improvement options;
- writes private 0700/0600 evidence through `EvidenceStore`.

## Source Interpretation

AOSP `lshal` source shows that binderized service listing and VINTF declaration
listing are separate concepts:

- binderized service fetch uses `hwservicemanager` `list()` and then `get()`;
- a null `get()` result emits `cannot be fetched from service manager (null)`;
- manifest entries are emitted separately as `DECLARED`;
- `-V` exposes VINTF flags and `-S` exposes explicit service status;
- `--types` can request `binderized`, `vintf`, or both.

Reference: `https://android.googlesource.com/platform/frameworks/native/+/013be5f/cmds/lshal/ListCommand.cpp`

## Validation

Static checks:

```text
python3 -m py_compile scripts/revalidation/wifi_v427_query_improvement_planner.py
git diff --check
```

Plan evidence:

```text
tmp/wifi/v427-query-improvement-plan-20260520-140121/
decision: v427-query-improvement-planner-plan-ready
pass: True
device_commands_executed: False
device_mutations: False
wifi_bringup_executed: False
```

Run evidence:

```text
tmp/wifi/v427-query-improvement-run-statusfix-20260520-140148/
decision: v427-explicit-status-query-needed
pass: True
reason: target rows are present but all have get-null warnings; explicit lshal service-status/VINTF split is the next minimal read-only improvement
device_commands_executed: False
device_mutations: False
wifi_bringup_executed: False
```

Current native state was also checked:

```text
A90 Linux init 0.9.61 (v319)
cmdv1 version: rc=0 status=ok
```

## Target Status

```text
vendor.samsung.hardware.wifi@2.0::ISehWifi/default: line=yes get-null=yes explicit-status=- interpretation=declared-or-listed-but-get-null
vendor.samsung.hardware.wifi@2.1::ISehWifi/default: line=yes get-null=yes explicit-status=- interpretation=declared-or-listed-but-get-null
vendor.samsung.hardware.wifi@2.2::ISehWifi/default: line=yes get-null=yes explicit-status=- interpretation=declared-or-listed-but-get-null
```

## V428 Options

Ranked options emitted by V427:

1. `v428-explicit-lshal-status-columns` — recommended.
   - Native composite query with explicit `-V -S` columns.
   - Same bounded service-manager + Wi-Fi HAL start-only cleanup model.
   - No scan/connect/link-up.
2. `v428-vintf-only-control` — recommended control.
   - Native VINTF-only lshal proof to separate declaration surface from
     binderized registration.
   - Read-only command only.
3. `android-managed-runtime-pivot` — deferred.
   - If explicit status still shows declared/get-null, Android framework control
     path is likely more realistic than native service-manager recreation.

## Interpretation

V427 refines the V425/V426 conclusion: Android boot-complete target rows exist,
but current evidence does not yet prove the targets are alive registered
hwservices.  The next safe step is to add explicit `lshal -S/-V` status evidence
on both native and Android paths before deciding whether to continue native
private-runtime reconstruction or pivot to Android-managed runtime control.
