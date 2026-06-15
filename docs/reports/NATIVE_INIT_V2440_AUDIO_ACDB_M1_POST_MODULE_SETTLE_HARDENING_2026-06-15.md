# NATIVE_INIT_V2440_AUDIO_ACDB_M1_POST_MODULE_SETTLE_HARDENING_2026-06-15

## Summary

V2440 is a host-only hardening unit for the V2439 wall. V2439 proved that the
V2438 staging-transfer fix works live, but stopped before capture because the
post-module-reboot Magisk root check hit a transient:

```text
adb: no devices/emulators found
```

V2440 adds a new runner that keeps the V2438 staging/install path unchanged and
changes only the post-module-reboot settle behavior. After the planned Android
reboot for Magisk `service.sh` activation, the runner now performs:

1. initial `adb wait-for-device`;
2. boot-complete recheck;
3. bounded ADB re-acquire + `su -c id` root-check retry loop;
4. metadata records for each failed root-check attempt;
5. progress only after a root-check stdout contains `uid=0`.

No live device action was run in V2440.

## Touched Public Artifacts

- `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_magisk_module_retry_live_handoff_v2440.py`
- `tests/test_native_audio_acdb_m1_magisk_module_retry_live_handoff_v2440.py`

## Runner Changes

The V2440 runner adds:

- `RUN_ID=V2440`
- build tag `v2440-audio-acdb-m1-magisk-module-retry`
- `DEFAULT_POST_MODULE_ROOT_RETRY_ATTEMPTS=8`
- `DEFAULT_POST_MODULE_ROOT_RETRY_SLEEP_SEC=3.0`
- dry-run metadata under `android_post_module_reboot_settle`
- `run_post_module_reboot_settle()`

The retry helper records each attempt as normal step metadata:

- `android-post-module-reboot-settle-0-wait-for-device`
- `android-post-module-reboot-settle-1-boot-complete`
- `android-post-module-reboot-root-wait-<n>`
- `android-post-module-reboot-root-check-<n>`

Each root-check step gets:

- `root_ready=true|false`
- `settle_decision=post-module-root-ready|post-module-root-not-ready`

The helper raises only after all configured attempts fail to produce `uid=0`.

## Preserved Boundaries

V2440 intentionally does not change:

- V2438 shell-owned incoming directory transfer;
- V2438 exact SHA-256 validation;
- final module install path;
- module payload/helper;
- stimulus APK;
- observer strategy;
- cleanup;
- V2321 rollback;
- native audio boundaries.

It still does not run or add:

- native speaker/mixer/PCM writes;
- native `/dev/msm_audio_cal` ioctl;
- native ACDB replay;
- `magisk --install-module`;
- `post-fs-data.sh`;
- Wi-Fi actions, DHCP, routes, or ping.

## Dry-Run Evidence

Materialized dry-run summary:

```json
{
  "command_safety_ok": true,
  "decision": "v2440-acdb-m1-magisk-module-retry-live-dry-run",
  "future_live_blockers": [],
  "future_live_ready": true,
  "ok": true,
  "retry_classification": "bounded adb reacquire plus Magisk-root retry after module activation reboot",
  "root_retry_attempts": 8,
  "root_retry_sleep_sec": 3.0,
  "run_id": "V2440"
}
```

## Validation

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_acdb_m1_magisk_module_retry_live_handoff_v2440.py \
  tests/test_native_audio_acdb_m1_magisk_module_retry_live_handoff_v2440.py

PYTHONPATH=tests python3 -m unittest \
  tests/test_native_audio_acdb_m1_magisk_module_retry_live_handoff_v2440.py -v

PYTHONPATH=tests python3 -m unittest discover -s tests

git diff --check
```

Focused tests: `7` passed. Full discovery: `1198` tests passed.

The focused tests prove:

- wrong live approval exits before device action;
- dry-run emits V2440 metadata;
- V2438 incoming transfer and SHA validation remain present;
- pushes still target `/incoming/`, not `module-stage`;
- post-module-reboot settle dry-run exposes bounded retry metadata;
- mocked retry flow tolerates one transient root-check failure and proceeds only
  after a later `uid=0` result.

## Next Unit

V2441 should be the exact-gated live rerun with the V2440 runner. It should keep
the same M1 measurement boundary:

- Android-good measurement only;
- temporary Magisk `service.sh` module only;
- no native speaker/mixer/PCM writes;
- no native `/dev/msm_audio_cal` ioctl;
- no native ACDB replay;
- exact cleanup before checked rollback to V2321.

If V2441 captures payload events, the next unit should be host-only payload
analysis. If it activates the module and captures zero events, classify the
Android-good measurement wall before changing hook strategy.
