# NATIVE_INIT_V2523_AUDIO_ACDB_OWNPROCESS_TIMEOUT_SALVAGE_HOST_ONLY_2026-06-16

## Scope

- Unit: V2523 host-only hardening of the V2490 own-process ACDB live runner.
- Trigger: V2522 timed out in `ownget-run-helper`, then cleaned the remote temp directory before log/context/artifact pull.
- Goal: preserve evidence on helper timeout before cleanup and rollback.

## Changes

- Added a helper-timeout salvage path:
  - records a synthetic timeout step for `ownget-run-helper`;
  - runs best-effort logcat/dmesg capture after timeout;
  - runs best-effort collection/readability chmod;
  - pulls `/data/local/tmp/a90-acdb-ownget` before cleanup;
  - parses the pulled artifact set and prefixes the decision with `helper-timeout`.
- Added parser support for context-only evidence:
  - `ownprocess-context-only-no-events`
  - still `operator_valuable=true` because it preserves execution context and logs even without ACDB rows.

## Safety Boundary

- Host-only unit; no device run.
- No HAL injection, Magisk module install, HAL restart, AudioTrack/playback, native speaker write, or `/dev/msm_audio_cal` SET ioctl.
- The next live timeout will still roll back to V2321, but it will no longer discard the most relevant evidence first.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
  - Result: `19` tests passed.
- V2490 dry-run with the V2512 helper:
  - `ok=true`
  - `live_ready=true`
  - command safety `ok=true`

## Next Unit

- V2524 can rerun the hardened V2490 live path.
- If it times out again, acceptance is now a preserved `ownget-device-artifacts/` directory with `ownget-exec-context.txt`, `ownget-run-context.txt`, ACDB logs, and any partial helper outputs.
- Do not increase the timeout until preserved evidence identifies the hang site.

