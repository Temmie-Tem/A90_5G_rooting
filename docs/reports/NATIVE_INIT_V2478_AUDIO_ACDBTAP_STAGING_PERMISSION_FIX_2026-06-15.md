# NATIVE_INIT_V2478_AUDIO_ACDBTAP_STAGING_PERMISSION_FIX_2026-06-15

## Decision

`v2478-acdbtap-staging-permission-fix`

V2478 fixes the Android-side staging permissions used by the V2476/V2477 ACDB
`acdb_ioctl` interposer live route. No new live capture succeeded in this unit;
this is a targeted host-side fix for the concrete blocker observed during the
first V2477 live attempts.

## Evidence

Two live attempts were made after V2477 was committed:

1. `workspace/private/runs/audio/v2477-acdbtap-live-handoff-20260615-223200/`
   - Result: `failed-before-rollback-rollback-pass`.
   - Cause: operator error / invocation bug. The runner was invoked from native
     init without `--from-native`, so the checked Android flash helper waited for
     recovery ADB and timed out before flashing Android.
   - Recovery: checked V2321 rollback fallback succeeded; final native version
     was `0.9.285 (v2321-usb-clean-identity-rodata)` with `selftest fail=0`.

2. `workspace/private/runs/audio/v2477-acdbtap-live-handoff-20260615-223725/`
   - Result: `failed-before-rollback-rollback-pass`.
   - Android boot: checked Android handoff succeeded, Magisk root was available.
   - Cause: `adb push` to
     `/data/local/tmp/a90-acdbtap-v2476/incoming/libacdbtap.so` failed with
     `Permission denied`.
   - Root cause: the V2476 setup command created the stage root and `incoming/`
     as root-only `0700`; plain `adb push` runs as shell and could not traverse
     or write that path.
   - Recovery: Android cleanup path ran, checked V2321 rollback succeeded, final
     native `selftest fail=0`.

No ACDB tap payload was captured in either attempt, so there is no private raw
payload set to preserve for operator mapping.

## Fix

Updated `native_audio_acdbtap_live_planner_v2476.py` setup permissions:

- stage root: `0755` so shell can traverse to `incoming/`;
- `incoming/`: `0777` so `adb push` can stage `libacdbtap.so`;
- `lib/`: remains root-only `0700`; root `install_libacdbtap` copies from
  `incoming/`, chowns root, and sets final `libacdbtap.so` mode `0644`.

This keeps the final preload library under root-controlled installation while
making only the transient incoming drop directory shell-writable under
`/data/local/tmp`.

## Acceptance clarification

If the next live run reaches ACDB tap capture and classifies as
`captured-acdbtap-full-outbuf-set-no-4916`, it is a **partial success**, not a
dead failure. The per-device AFE / ASM / ADM / VOL payloads are still valuable
operator input. Such a result must be preserved and must not count against the
fails-twice retry budget as a low-information dead run.

A full target capture remains
`captured-acdbtap-full-outbuf-set-with-4916`: complete ordered `out_len>0`
metadata and private raw bytes for every event, including at least one
`out_len==4916` record.

## Validation

Commands planned/run for this fix:

```bash
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 -m py_compile \
    workspace/public/src/scripts/revalidation/native_audio_acdbtap_live_planner_v2476.py \
    workspace/public/src/scripts/revalidation/native_audio_acdbtap_live_handoff_v2477.py \
    tests/test_native_audio_acdbtap_live_planner_v2476.py \
    tests/test_native_audio_acdbtap_live_handoff_v2477.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest \
    tests.test_native_audio_acdbtap_live_planner_v2476 \
    tests.test_native_audio_acdbtap_live_handoff_v2477 -v

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest discover -s tests -v

git diff --check
```

Results:

- focused V2476/V2477 tests: `9` passed;
- full test suite: `1270` passed;
- `git diff --check`: passed.

## Next

Retry the V2477 live capture using `--run-live --from-native`. Expected next
blockers are now preload/linker/SELinux related, not the `adb push` staging
permission issue.
