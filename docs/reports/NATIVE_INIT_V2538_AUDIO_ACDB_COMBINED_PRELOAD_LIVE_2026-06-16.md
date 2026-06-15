# NATIVE_INIT V2538 — ACDB combined preload live attempt

Date: 2026-06-16  
Scope: ACDB own-process measurement path, single combined ARM32 `LD_PRELOAD` exporting both `acdb_ioctl` tap and `ioctl` fake/trace hooks.  
Result: **negative live result, rollback clean**.

## Purpose

V2536/V2537 showed that two separate preloads (`libacdbtap.so` plus `liba90_ioctl_trace_v2531.so`) could leave the own-process helper stuck at `ACDB_CMD_INITIALIZE_V2` with zero `acdbtap` and zero `ioctl_trace` events. V2538 removes Android linker multi-preload behavior from the measurement by building one ARM32 shared object that exports both symbols:

- `acdb_ioctl` from the V2475 tap, for out-buffer capture.
- `ioctl` from the V2531 observer/fake path, with `A90_ACDB_FAKE_ALLOCATE=1` returning success for audio calibration allocate/deallocate/SET attempts.

The unit stays measurement-only: no native speaker write, no committed raw payloads, and no persistent module install.

## Implementation

Public code added/updated:

- `workspace/public/src/scripts/revalidation/build_android_acdb_combined_preload_v2538.py`
- `workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- `tests/test_build_android_acdb_combined_preload_v2538.py`
- `tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`

Private build artifact:

- Path: `workspace/private/builds/audio/v2538-acdb-combined-preload-host-only/bin/liba90_acdb_combined_preload_v2538.so`
- SHA256: `e6e5ba9ff42c0a676c311a44fbfa2690446811382e52c2dbbbb21561915f3b4b`
- File size: `9324` bytes
- Mode: `0600`
- Export check: both `acdb_ioctl` and `ioctl` are exported.

Runner changes:

- `--use-combined-preload` selects only `/data/local/tmp/a90-acdb-ownget/liba90_acdb_combined_preload_v2538.so` for `LD_PRELOAD`.
- When combined preload is enabled, the older separate `acdbtap` and `ioctl_trace` preloads are disabled.
- `--fake-audio-cal-allocate` sets `A90_ACDB_FAKE_ALLOCATE=1` for the combined preload.
- The artifact pull path still preserves the full `/data/local/tmp/a90-acdb-tap/` directory if any `acdb_ioctl` rows are emitted.

## Static validation

Passed before live execution:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_combined_preload_v2538.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py \
  tests/test_build_android_acdb_combined_preload_v2538.py \
  tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_build_android_acdb_combined_preload_v2538 \
  tests.test_build_android_acdbtap_v2475 \
  tests.test_build_android_ioctl_trace_preload_v2531 \
  tests.test_native_audio_acdb_ownprocess_get_live_handoff_v2490
```

Result: `Ran 44 tests ... OK`.

Dry-run checks before live:

- Combined build: `build_ok=true`
- Own-process dry-run: `ok=true`
- `live_ready=true`
- Command safety: `ok=true`
- Preload selection: exactly one combined preload, with separate `acdbtap`/`ioctl_trace` preload paths absent.

## Live execution

Private run directory:

- `workspace/private/runs/audio/v2538-acdb-combined-preload-20260616-065736`

Command shape:

```bash
PYTHONPATH=workspace/public/src/scripts/revalidation \
python3 workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py \
  --run-live \
  --from-native \
  --fake-audio-cal-allocate \
  --use-combined-preload \
  --helper-timeout 60 \
  --adb-command-timeout 90 \
  --adb-pull-timeout 180 \
  --out-dir workspace/private/runs/audio/v2538-acdb-combined-preload-20260616-065736
```

Device-side environment captured by the run:

```text
LD_PRELOAD=/data/local/tmp/a90-acdb-ownget/liba90_acdb_combined_preload_v2538.so
A90_ACDBTAP_DIR=/data/local/tmp/a90-acdb-tap
A90_ACDB_FAKE_ALLOCATE=1
LD_LIBRARY_PATH=/data/local/tmp/a90-acdb-ownget:/vendor/lib:/system/lib:/system_ext/lib:/product/lib
```

The combined preload was staged and pulled back as part of the artifact set. No separate `libacdbtap.so` or `liba90_ioctl_trace_v2531.so` path was used for this run.

## Result

Runner decision:

```text
v2490-helper-timeout-ownprocess-context-only-no-events-before-rollback-rollback-pass
```

Parsed summary:

| Field | Value |
| --- | --- |
| classification | `ownprocess-context-only-no-events` |
| `row_count` | `0` |
| `acdbtap_row_count` | `0` |
| `target_4916_count` | `0` |
| `acdbtap_target_4916_count` | `0` |
| `full_success` | `false` |
| `partial_success` | `false` |
| `operator_valuable` | `true` |
| `counts_toward_fails_twice` | `true` |

Observed loader progress stopped at the same boundary as the previous stacked-preload attempts:

```text
ACDB-LOADER: ACDB -> ACDB_CMD_INITIALIZE_V2
```

There were no `ioctl_trace` events and no `acdbtap` events. Therefore the fake allocate/deallocate path did not fire in this run; no `ret==0` non-zero out-buffer was captured, and no 4916-byte topology payload was captured.

SELinux filtering did not produce a specific causal denial for this measurement path. The collected AVC/dmesg filters contain general Android boot/property denials plus one unrelated audit line, but no `msm_audio_cal` open/ioctl denial and no ACDB-specific preload denial.

## Rollback and health

The runner rolled the device back to V2321. Final manual health check after the runner completed:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

No private raw payload is committed. The run-private artifact set remains under `workspace/private/runs/audio/v2538-acdb-combined-preload-20260616-065736/`.

## Interpretation

V2538 eliminates the two-`LD_PRELOAD` variable and confirms that merely combining the V2475 `acdb_ioctl` tap with the V2531 `ioctl` fake/trace hook does **not** move the own-process helper past `ACDB_CMD_INITIALIZE_V2`. The expected `AUDIO_ALLOCATE_CALIBRATION` fake path did not execute, so this is not evidence that faking allocate is insufficient after being reached; it is evidence that the helper is still blocked before any observable `ioctl` or `acdb_ioctl` wrapper event.

This makes another preload-stacking retry low value. The next meaningful unit should be a new mechanism-level discriminator, for example:

1. Host RE / targeted instrumentation around `ACDB_CMD_INITIALIZE_V2` and the ACPH/DB initialization wait path, or
2. An own-process direct-call path that bypasses the stuck init phase if a safe `is_initialized`/GET gate can be pinned, or
3. A narrowly scoped mmap-handle interposer only if source/RE shows the current block is waiting on a mapped fake allocation handle.

Do not advance to native replay or mark the payload captured from V2538.
