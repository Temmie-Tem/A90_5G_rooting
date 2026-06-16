# NATIVE_INIT V2594 — ACDB send_audio_cal_v5 pre-GET geometry RE

Date: 2026-06-16

## Scope

Host-only RE after V2593. No Android handoff, native replay `SET`, speaker write,
ACDB command execution, or raw payload publication was performed. Proprietary disassembly
and JSON scratch stay private under `workspace/private/runs/audio/v2594-send-audio-cal-preget-recon`.

## Decision

- decision: `v2594-send-audio-cal-v5-first-dispatch-geometry-pinned`
- ok: `True`
- V2593 closed corrected stack-arg order as insufficient: `send_audio_cal_v5` still timed out before any real armed `acdb_ioctl` row.
- This unit pins the first dispatcher row geometry so the next unit can bypass the hanging local setup path with a pure-read metadata probe.

## Pre-first-dispatch Calls

Imported calls before the first `acdb_ioctl` dispatcher row:
- `0x9d50` -> `pthread_mutex_lock` via PLT `0x15a00`
- `0x9d5e` -> `pthread_mutex_unlock` via PLT `0x15a10`
- `0x9da2` -> `__android_log_print` via PLT `0x15a40`
- `0x9e3c` -> `__android_log_print` via PLT `0x15a40`
- `0x9e70` -> `__android_log_print` via PLT `0x15a40`

Local/internal calls before the first dispatcher row:
- `0x9df8` -> `0xfd44` (`acdb_loader_get_mod_loading_meta_info+0x293`, contains=False)
- `0x9e18` -> `0xfbbc` (`acdb_loader_get_mod_loading_meta_info+0x10b`, contains=False)

The first dispatcher call itself is the `acdb_ioctl` PLT call at `0x9e86`. V2593 saw zero real
armed rows, so the live stall is before or at the local setup that precedes this call, not in later
AFE/AUDPROC/VOL handlers.

## Direct Metadata GET Geometry

- command: `0x1122e`
- call site: `0x9e86`
- `in_len`: `4`
- `out_len`: `4`
- first input word: `0x11135`
- input source: r8 = send_audio_cal_v5 arg3 app_id; stored to [sp,#80] at 0x9e42
- proposed pure-read probe: `acdb_ioctl(0x1122e, &app_id, 4, &out_word, 4)` after ACDB init and before any `send_audio_cal_v5` call.
- boundary: no `AUDIO_SET_CALIBRATION`, no native replay SET, no speaker write.

## Interpretation

The corrected `send_audio_cal_v5(15, 1, 0x11135, 48000, 0, 48000, 1)` call still depends on local
state/list setup before it can issue its first ACDB dispatcher row. The direct `0x1122e` metadata
query is safer and higher-signal than another argument variant because it exercises the first pinned
pure-read row without entering the hanging local setup path or the later SET path.

## Next Unit

Build V2595 as a host-only source/build unit for a post-init direct `0x1122e` metadata probe:

1. reuse the own-process Android-good helper and fake-allocate preload;
2. initialize ACDB normally and keep the zero-buffer discriminator;
3. call only `acdb_ioctl(0x1122e, &app_id, 4, &out_word, 4)` with `app_id=0x11135`;
4. record `{ret,out_word,sha/all-zero}` privately/metadata-only;
5. do not issue `send_audio_cal_v5` or any `/dev/msm_audio_cal` SET in that unit.

If V2595 returns valid metadata, use that value to derive the subsequent per-device pure-read request
structs. If it fails, fall back to an armed import-call tracer around `send_audio_cal_v5` to identify
which internal pre-`0x1122e` helper stalls.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_send_audio_cal_preget_recon_v2594.py tests/test_native_audio_acdb_send_audio_cal_preget_recon_v2594.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_send_audio_cal_preget_recon_v2594`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_send_audio_cal_preget_recon_v2594.py --write-report`
- `git diff --check`
