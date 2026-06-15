# NATIVE_INIT V2490 — ACDB own-process GET live attempt, libaudcal dlopen block

## Scope

V2490 is the first live attempt on the new own-process ACDB capture path.  It
explicitly pivots away from the V2477–V2488 in-HAL LD_PRELOAD/module/wrapper-exec
line per the operator nudge.

The runner boots stock Android through the checked helper, stages only the V2489
ARM32 own-process helper under `/data/local/tmp/a90-acdb-ownget`, runs it once in
`su` domain, pulls private artifacts, cleans up, and rolls back to V2321.

No Magisk module, HAL restart, AudioTrack playback, native speaker write, or
native `/dev/msm_audio_cal` calibration ioctl was used.

## Pre-run state

Before V2490, the device was already back on V2321 native init despite the stale
operator note that it might still be in Android:

```text
A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
selftest: pass=11 warn=1 fail=0
```

Rollback images were present, including the V2321 rollback target with SHA-256
`ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.

## Implementation

New public files:

- `workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- `tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`

The runner reuses the checked Android handoff/rollback helpers and V2396's
post-handoff settle retry path.  That gives the requested slow-first-boot
hardening without iterating the in-HAL wrapper-exec mechanism.

Dry-run status before live:

| Field | Result |
| --- | --- |
| `live_ready` | `true` |
| command safety | pass |
| Android boot candidate | pass |
| V2321 rollback image | pass |
| V2489 helper artifact | pass, SHA `800933fa47b117e67036dc355fa1b87be4f1dc5ddb612e8126ab1face59333b4` |

## Live run

Private run directory:

```text
workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-012233
```

Outcome:

```text
v2490-ownprocess-error-dlopen-libaudcal-before-rollback-rollback-pass
```

The original live `result.json` initially reported `ownprocess-no-events` because
`adb pull` produced a flat directory while the parser expected a nested
`a90-acdb-ownget/` directory.  The parser is fixed in the committed runner and
re-analysis of the private artifacts gives the correct classification:

```json
{
  "classification": "ownprocess-error-dlopen-libaudcal",
  "row_count": 0,
  "error_count": 1,
  "target_4916_count": 0,
  "raw_file_count": 0,
  "operator_valuable": true,
  "counts_toward_fails_twice": true
}
```

Private event evidence:

```json
{"event":"error","stage":"dlopen-libaudcal","code":-1,"pid":3568,"tid":3568}
```

This confirms the expected remaining risk from the operator nudge: standalone
execution from `/data/local/tmp` in shell/su domain can fail to load `/vendor/lib`
ACDB dependencies because of Android/VNDK linker namespace constraints.  The
helper did not reach `acdb_loader_init_v3` or any `acdb_ioctl` GET call.

## Rollback / health

Rollback to V2321 completed through the checked helper:

```text
rollback-v2321 rc=0
```

Post-rollback selftest:

```text
selftest: pass=11 warn=1 fail=0
```

The recoverable envelope held.  No persistent Android module remained because
V2490 did not install one.

## Validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest \
  tests.test_build_android_acdb_ownprocess_get_v2489 \
  tests.test_native_audio_acdb_ownprocess_get_live_handoff_v2490 -v

python3 workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py --dry-run

git diff --check
```

Focused tests: `13` tests pass after the parser fix.

## Next unit

Do **not** return to in-HAL injection.  The next meaningful unit is V2491:
classify and fix own-process vendor-library loadability.

Recommended V2491 host-first work:

1. add `dlerror()` capture to the V2489 helper so future live runs report the
   exact linker namespace error string;
2. stage a bounded loadability probe matrix, still pure-read and no ACDB ioctl:
   - run from `/data/local/tmp` with `LD_LIBRARY_PATH=/vendor/lib`;
   - if needed, stage a Magisk/systemless vendor-path wrapper or linker-namespace
     compatible launch path, without HAL injection and without playback;
3. only after `dlopen-libaudcal` and `dlopen-libacdbloader` pass, rerun the GET
   matrix.

The partial-success policy remains unchanged: an ordered out-buffer set with no
4916-byte record is preserved as operator-valuable partial evidence and does not
count as a dead ACDB tap run.
