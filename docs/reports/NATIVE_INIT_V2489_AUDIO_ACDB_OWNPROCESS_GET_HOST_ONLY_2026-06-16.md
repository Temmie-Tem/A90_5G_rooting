# NATIVE_INIT V2489 — ACDB own-process pure-read GET helper, host-only

## Scope

V2489 implements the newly unblocked own-process ACDB capture path from the
operator spec update.  This is **host-only**: no Android boot, no Magisk capsule,
no HAL restart, no playback, and no native calibration ioctl execution.

The goal is to prepare a bounded ARM32 helper that can run in a future Android
measurement window and directly query ACDB read commands without entering the
native `/dev/msm_audio_cal` SET path.

## Inputs verified

- Operator spec: `docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md`
- Helper source: `workspace/public/src/android/acdb_payload_capture/a90_acdb_ownprocess_get_v2489.c`
- Builder: `workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py`
- Tests: `tests/test_build_android_acdb_ownprocess_get_v2489.py`
- Private vendor dump:
  - `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/libacdbloader.so`
  - `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/libaudcal.so`

Private symbol checks passed:

| Library | Required fact | Result |
| --- | --- | --- |
| `libacdbloader.so` | exports `acdb_loader_init_v3` | present |
| `libacdbloader.so` | exports `acdb_loader_init_v4` | present |
| `libacdbloader.so` | imports `acdb_ioctl` | present |
| `libaudcal.so` | exports `acdb_ioctl` | present |

## Helper design

The helper is a freestanding 32-bit ARM PIE with a custom `_start`.  It uses
`dlopen()` / `dlsym()` at runtime rather than linking directly to proprietary
vendor libraries:

1. `dlopen("libaudcal.so", RTLD_NOW | RTLD_GLOBAL)`
2. `dlopen("libacdbloader.so", RTLD_NOW | RTLD_GLOBAL)`
3. `dlsym(..., "acdb_loader_init_v3")`
4. `dlsym(..., "acdb_ioctl")`
5. `acdb_loader_init_v3("/vendor/etc/acdbdata", "/data/local/tmp/a90-acdb-ownget/delta", 0)`
6. bounded pure-read `acdb_ioctl` matrix:
   - commands: `0x11394`, `0x12e01`, `0x130da`, `0x130dc`
   - `in_len`: `0`, `4`, `8`, `16`, `32`
   - `out_len`: `4`, `4916`
   - maximum calls: `40`

The helper writes ordered JSONL metadata and raw out-buffer files under
`/data/local/tmp/a90-acdb-ownget/`.  Raw files are future-live private artifacts
only and must never be committed.

## Safety boundary

V2489 deliberately excludes every known unsafe/native-calibration path:

- no `/dev/msm_audio_cal` open;
- no `0xc00461cb` command;
- no `AUDIO_SET_CALIBRATION` / allocation / deallocation ioctl path;
- no `acdb_loader_send_common_custom_topology`, because that wrapper proceeds to
  the SET path after the GET;
- no `tinymix`, `tinyplay`, AudioTrack, speaker write, HAL restart, or Magisk
  staging in this unit.

The future live run remains a separate V-iteration.  This unit only proves that
the helper can be built and that the public source encodes the intended
pure-read command boundary.

## Build result

Private artifact:

```text
workspace/private/builds/audio/v2489-acdb-ownprocess-get-host-only/bin/a90_acdb_ownprocess_get_v2489
```

Metadata:

| Field | Value |
| --- | --- |
| Type | `ELF 32-bit LSB shared object, ARM, dynamically linked` |
| Interpreter | `/system/bin/linker` |
| Runtime dependency | `libdl.so` |
| Undefined runtime symbols | `dlopen`, `dlsym` |
| Size | `7064` bytes |
| SHA-256 | `800933fa47b117e67036dc355fa1b87be4f1dc5ddb612e8126ab1face59333b4` |

The `libdl.so` dependency is produced with a private build-time stub only; the
future Android execution uses the device's real `libdl.so`.

## Validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_build_android_acdb_ownprocess_get_v2489 -v

python3 workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py --build
```

Results:

- `py_compile`: pass
- focused unittest: `5` tests pass
- private ARM32 PIE build: pass
- source boundary scan: required markers present, prohibited markers absent
- `git diff --check`: run after final patch set

## Notes for next unit

Next live unit should not reuse the failed V2488 HAL-wrapper route as the first
choice.  The lower-risk next step is a bounded Android handoff that stages this
helper plus a run-local output directory, sets a controlled library search path
if needed, runs the helper once, pulls the complete ordered output set privately,
cleans up, and rolls back to V2321 with `selftest fail=0`.

The live unit must preserve the existing ACDB tap acceptance policy:
`captured-acdbtap-full-outbuf-set-no-4916` is operator-valuable partial success
and does not count as a fails-twice dead run.
