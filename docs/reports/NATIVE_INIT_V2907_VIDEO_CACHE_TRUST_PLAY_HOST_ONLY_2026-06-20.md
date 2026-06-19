# NATIVE_INIT_V2907_VIDEO_CACHE_TRUST_PLAY_HOST_ONLY_2026-06-20

## Summary

V2907 adds an explicit fast playback path for the SD-card video cache:

- `video cache verify SHA256` remains the full-content integrity gate.
- `video cache play SHA256 --trust-cache ...` skips the full stream SHA-256 re-read and starts the existing stream player immediately after cheap manifest/stat checks.
- Default `video cache play SHA256 ...` is unchanged in safety posture: it still performs full SHA-256 verification before playback.

This is host-only preparation for A/V sync testing. The previous V2906 live run proved the existing 2.1 GiB cached Bad-Apple-scale stream can play 6501 page-flip frames from SD with `dropped=0`, but full SHA verification immediately before playback costs roughly the same order as the bounded audio test window. A pre-verified trusted cache mode is needed so the next live A/V-sync unit can verify once, start audio, and then enter video presentation without re-hashing the whole stream.

## Scope

Touched public paths:

- `workspace/public/src/native-init/v319/30_status_hud.inc.c`
- `workspace/public/src/native-init/v319/60_shell_basic_commands.inc.c`
- `workspace/public/src/native-init/v319/80_shell_dispatch.inc.c`
- `tests/test_native_video_cache_command_v2904.py`

No private payloads, boot images, raw logs, or generated binaries are committed.

## Behavior

### Default path

`video cache play SHA256 ...` still:

1. Loads the content-addressed manifest from `/mnt/sdext/a90/runtime/video/cache/sha256-<sha>/manifest.json`.
2. Prints cache status.
3. Requires the stream file to exist and match the manifest-derived expected byte size.
4. Computes the full stream SHA-256 via `video_cache_verify_hash()`.
5. Emits `video.cache.play.trust_cache=0`.
6. Reuses `video_stream_play()`.

### Trusted path

`video cache play SHA256 --trust-cache ...` now:

1. Loads the same content-addressed manifest.
2. Prints cache status.
3. Requires the stream file to exist and match the manifest-derived expected byte size.
4. Skips the full stream SHA-256 re-read.
5. Emits explicit markers:
   - `video.cache.play.trust_cache=1`
   - `video.cache.verify.actual_sha256=trust-cache-not-checked`
   - `video.cache.verify.sha256_checked=0`
   - `video.cache.verify.sha256_match=0`
6. Reuses `video_stream_play()`.

The trusted path is intentionally not silent. Logs make it clear that integrity was not rechecked during this invocation.

## Guardrails

`--trust-cache` is not accepted as an implicit shortcut:

- It must be passed explicitly to `play`.
- Duplicate `--trust-cache` is rejected as usage error.
- It does not bypass manifest SHA equality.
- It does not bypass stream existence or exact-size checks.
- It does not change the underlying stream player, page-flip code, or audio-sync status-path allowlist.

## Validation

Completed host validation:

- `python3 -m py_compile tests/test_native_video_cache_command_v2904.py` — PASS.
- `python3 -m unittest tests.test_native_video_cache_command_v2904` — PASS (`7` tests).
- AArch64 static compile of `workspace/public/src/native-init/init_v725_fasttransport.c` with the touched include graph — PASS.
  - Output checked with `file`: `ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped`.
  - Existing `a90_usb_gadget.c` truncation warnings appeared; they are unrelated to this video-cache change.
- `git diff --check` — PASS.

Device validation is intentionally deferred to the next build/live unit. The next live target should be a cache A/V-sync slice:

1. `video cache verify <known V2900 cache SHA>`.
2. Start bounded internal-speaker audio.
3. `video cache play <same SHA> --trust-cache --frames 300 --present pageflip --sync-audio-status /cache/a90-audio-play/status.txt`.
4. Require audio-sync markers and accounted video frames, then rollback to `v2321`.
