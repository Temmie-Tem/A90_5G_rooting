# v219 Native Android-Env Shim Plan

## Summary

v219 adds a manifest-only native Android-env shim planner for future CNSS
experiments. It does not execute daemons or mutate device state.

Result: PASS.

Final decision: `shim-plan-partial`.

Reason: bounded shim areas are mapped, but recovery/property/QMI blockers
remain.

## Changes

- Added `scripts/revalidation/wifi_android_env_shim_plan.py`.
- Added v219 plan:
  `docs/plans/NATIVE_INIT_V219_NATIVE_ANDROID_ENV_SHIM_PLAN_2026-05-13.md`.

## Scope

The planner consumes v216/v217/v218 manifests and writes:

- `tmp/wifi/v219-native-android-env-shim/manifest.json`
- `tmp/wifi/v219-native-android-env-shim/shim-matrix.json`
- `tmp/wifi/v219-native-android-env-shim/summary.md`

## Static Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_android_env_shim_plan.py
```

Result: PASS.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_android_env_shim_plan
wifi_android_env_shim_plan.validate_no_active_commands()
print('v219 command guard PASS')
PY
```

Result:

```text
v219 command guard PASS
```

## Planner Run

Command:

```bash
python3 scripts/revalidation/wifi_android_env_shim_plan.py \
  --v216-manifest tmp/wifi/v216-service-replay-model/manifest.json \
  --v217-native-manifest tmp/wifi/v217-icnss-debug-recovery-inventory-native/manifest.json \
  --v218-manifest tmp/wifi/v218-cnss-daemon-dryrun/manifest.json \
  --v218-native-manifest tmp/wifi/v218-cnss-daemon-dryrun-native/manifest.json \
  --out-dir tmp/wifi/v219-native-android-env-shim
```

Result:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v219-native-android-env-shim decision=shim-plan-partial reason=bounded shim areas are mapped, but recovery/property/QMI blockers remain
```

## Shim Matrix Summary

```text
available=3
shim-required=5
host-evidence-required=1
blocked=4
out-of-scope=1
```

Available:

- temporary read-only vendor visibility
- `init.svc` service state model as evidence
- ACM/NCM rescue control validation

Shim required:

- `/system/vendor -> /vendor` path compatibility
- bounded `NET_ADMIN` handling for `cnss-daemon`
- Android group mapping
- private daemon stdout/stderr evidence
- before/after health bundle

Blocked or out of scope:

- real Android property service recreation
- QMI/PDR/SSR writes
- ICNSS recovery without reboot
- Wi-Fi credentials and `/data/misc/wifi`
- binder/hwbinder service publication

## Guardrails

- No daemon execution.
- No Android property mutation.
- No `ctl.start` or `class_start`.
- No binder/hwbinder service publication.
- No writable vendor/system/data mount.
- No ICNSS `bind`/`unbind`/`driver_override`.
- No rfkill write, link-up, scan, or connect.
- No credential collection from `/data/misc/wifi`.

## Hashes

```text
c6a856af865b15e74d23cb4b3fa2745e2d0449a685227c8022a1614d84c8d161  scripts/revalidation/wifi_android_env_shim_plan.py
dc4e46246dce230cdac7772a86f12198e77a1232a96ec764d71950a7c1db34fd  docs/plans/NATIVE_INIT_V219_NATIVE_ANDROID_ENV_SHIM_PLAN_2026-05-13.md
a1aa110304dd277c8e2a9189a0fc84009f9a3f8c50d57cfc5d7322211c442f3f  tmp/wifi/v219-native-android-env-shim/manifest.json
07ad51853c70ea079451ee5cc39c5452adb08c2e712b66e8f9762ea067c3f9a7  tmp/wifi/v219-native-android-env-shim/shim-matrix.json
dd17bf33f683f7ae3499578bd4626be0cf17ea073f436120624f9be96e55ce68  tmp/wifi/v219-native-android-env-shim/summary.md
```

## Decision

v219 is enough for v220 gate work. It does not approve daemon execution. The
shim scope is bounded, but active service experiments remain blocked by
property/QMI/recovery constraints and missing host ELF/library evidence.

## Next

Plan v220 as Wi-Fi bring-up preflight gate v2. It should consume v216-v219
evidence and continue to return `no-go` unless lifecycle, recovery, shim,
security, and evidence prerequisites are all explicitly satisfied.
