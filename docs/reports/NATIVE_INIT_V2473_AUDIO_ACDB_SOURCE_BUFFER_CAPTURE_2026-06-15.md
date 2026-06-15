# NATIVE_INIT V2473 — Audio ACDB Source-Buffer Capture

Date: 2026-06-15
Scope: host-only implementation and validation

## Decision

`v2473-audio-acdb-source-buffer-capture-host-only-pass`

V2473 adds a lower-risk Android-good source-buffer capture path before attempting more invasive owner-context instrumentation. The Android-side ACDB observer can now capture candidate ACDB bytes from regular-file source reads and source mmaps into private artifacts while public summaries expose only metadata and SHA-256.

## Context

Previous dmabuf-focused attempts localized the remaining ACDB payload gap:

- V2466 observed the custom topology SET_CAL edge but could not reopen the process-local dmabuf fd.
- V2468 observed matching `mmap2(len=4916)` records, but owner-VA reads failed with `EIO`.
- V2471 showed early `/proc/<tgid>/fd/<mem_handle>` duplication still fails with `ENXIO`.
- V2472 removed AArch64 anonymous mmap fd noise.

The next bounded direction is to see whether the stock audio process reads the custom topology bytes from ACDB source files before passing them through dmabuf-backed calibration buffers.

## Implementation

Changed source:

- `workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_diag_v2449.c`
- `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_planner_v2449.py`
- `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_live_handoff_v2450.py`
- `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py`

Added observer support:

- Detects AArch64 `read`/`pread64` and AArch32 compat `read`/`pread64`.
- Filters source fds to likely ACDB/audconf sources:
  - `/vendor/etc/acdbdata`
  - `/vendor/etc/audconf`
  - `/acdbdata/`
  - `.acdb`
- Explicitly excludes library paths such as `/vendor/lib/` and `/system/lib/` to avoid treating loader shared objects as ACDB data sources.
- Captures read buffers after successful syscall exit with `read_remote()`.
- Captures successful regular-file source mmaps by reopening `/proc/<fd_pid>/fd/<fd>` and `pread()`ing from the mapped file offset.
- Writes private `sourcebuf*.bin` artifacts under the existing private capture directory.
- Emits `source_buffer_capture` JSONL events with status values including `ok-source-read` and `ok-source-mmap`.
- Adds stop counters `source_buffer_capture_count` and `source_buffer_error_count`.

Updated host summaries:

- Source-buffer files are summarized by relative file path, size, and SHA-256 only.
- Raw source-buffer bytes are not embedded in public summaries.
- Late-observer classification can now return `late-msm-audio-cal-source-buffer-candidate-captured`.
- Generic observer classification can now return `msm-audio-cal-source-buffer-candidate-captured`.

## Boundaries

Still not done in V2473:

- No live Android handoff was run.
- No native calibration ioctl was issued.
- No native replay was attempted.
- No owner-context or in-process instrumentation was added.
- No raw ACDB source-buffer bytes are committed.

## Validation

Commands run:

```sh
aarch64-linux-gnu-gcc -O2 -static -s -Wall -Wextra \
  -o /tmp/a90_v2473_test \
  workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_diag_v2449.c
file /tmp/a90_v2473_test

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest \
  tests.test_native_audio_acdb_m1_diag_observer_planner_v2449 \
  tests.test_native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451

PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_planner_v2449.py \
  --dry-run --materialize-module-template --module-out-dir <tmpdir>
```

Observed validation:

- AArch64 static helper build passed; `file` reports a stripped static ARM aarch64 executable.
- Focused unittest result: `Ran 19 tests ... OK`.
- Materialized dry-run metadata:
  - `future_live_ready=true`
  - `command_safety_ok=true`
  - `contains_source_buffer_capture=true`
  - `contains_acdb_source_target_filter=true`
  - `adds_acdb_source_buffer_capture=true`

## Next

Run a fresh bounded Android-good AUD-5L-style live rerun with the V2473 helper. Success criterion for the next unit is not speaker playback; it is whether private `sourcebuf*.bin` candidates appear and whether their size/hash/timing can be correlated to the known custom-topology edge (`cal_type=39`, `cal_size=4916`). Native calibration ioctls remain blocked until payload bytes/order/hash/lifetime/cleanup policy are pinned.
