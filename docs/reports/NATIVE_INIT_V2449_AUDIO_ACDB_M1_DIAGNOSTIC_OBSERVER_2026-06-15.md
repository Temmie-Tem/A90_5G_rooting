# NATIVE_INIT_V2449_AUDIO_ACDB_M1_DIAGNOSTIC_OBSERVER_2026-06-15

## Summary

V2449 is a host-only implementation unit after V2448 diagnosed the V2447 M1
capture gap.  It does not boot Android, install a module, run playback, touch the
device, or issue any native audio/calibration ioctl.

The result is a source-controlled diagnostic M1 observer and planner for the next
Android-good ACDB payload measurement:

- new helper source:
  `workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_diag_v2449.c`
- new host-only planner:
  `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_planner_v2449.py`
- new focused tests:
  `tests/test_native_audio_acdb_m1_diag_observer_planner_v2449.py`

The Magisk-module direction remains the same as the earlier Wi-Fi-style handoff
pattern: use a temporary Android-side measurement capsule for boot-time helper
packaging and vendor-path observation, then clean it up and roll back.  It is not
a native-init runtime dependency.

## Why This Unit Exists

V2447 reached the right Android-good window:

- temporary Magisk service module activated;
- Android playback and cleanup completed;
- checked rollback returned to V2321 with `selftest fail=0`;
- the audio HAL worker TID that logged the speaker ACDB edge was attached.

But V2448 showed that the resulting `0` `/dev/msm_audio_cal` ioctl count was not
a clean negative:

- the previous helper recorded only fd-matched `/dev/msm_audio_cal` ioctls;
- it did not record total syscall stops, total ioctl attempts, fd miss/readlink
  errors, unmatched fd targets, or timestamps;
- the relevant p8795/p8796 JSONL files lacked terminal `stop` records and were
  pulled while helpers were still running.

Repeating V2447 unchanged would only reproduce the same ambiguous zero.

## What Changed

### Diagnostic helper

`a90_acdb_ioctl_capture_diag_v2449.c` keeps the V2423/V2447 core model:

- attach all existing TIDs in the target process;
- enable `PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACECLONE`;
- resume with `PTRACE_SYSCALL`;
- follow clone-created worker threads;
- copy raw request bytes only for fd-matched `/dev/msm_audio_cal` ioctls.

It adds public-safe diagnostic telemetry:

| Field / event | Purpose |
| --- | --- |
| `ts_ms` | monotonic timestamp for event ordering |
| `wall_ms` | wall timestamp for correlation with Android logs |
| `syscall_stop_count` | proves whether ptrace syscall stops occurred |
| `syscall_entry_count` | separates syscall entry from exit accounting |
| `ioctl_any_entry_count` | proves whether any ioctl entries occurred before fd filtering |
| `ioctl_fd_match_count` | fd-matched `/dev/msm_audio_cal` ioctl count |
| `ioctl_fd_miss_count` | ioctl count rejected by fd/path filter |
| `fd_readlink_error_count` | `/proc/<fd_pid>/fd/<fd>` resolution failures |
| `ioctl_unmatched` | bounded first-N metadata-only unmatched ioctl samples |

Unmatched samples include only metadata such as TID, fd, request number,
readlink result, and fd target.  They do not copy raw request buffers.

### Diagnostic M1 service module plan

`native_audio_acdb_m1_diag_observer_planner_v2449.py` materializes a private
temporary Magisk service module under:

```text
workspace/private/builds/audio/v2449-acdb-m1-diag-observer/
```

Default private artifacts generated during validation:

```text
helper = workspace/private/builds/audio/v2449-acdb-m1-diag-observer/bin/a90_acdb_ioctl_capture_diag_v2449
helper_sha256 = 9520e9f297ba4cb52ce2730d8166876409162a70f64998b7c2ac16ca21f165f8

module_zip = workspace/private/builds/audio/v2449-acdb-m1-diag-observer/a90_audio_acdb_m1_diag_v2449.zip
module_zip_sha256 = ef98419a2a63f610115238eebf934391e8d1799a3c3b9329d9426c4618428bd0
```

Those generated binaries/zips are private and not committed.

The service script adds:

- `A90_M1_DIAG_SERVICE_BEGIN` / `A90_M1_DIAG_SERVICE_END` wall markers;
- `A90_M1_DIAG_HELPER_START` for each target process;
- `--max-unmatched-samples` passed to the helper;
- `A90_M1_DIAG_HELPER_WAIT_BEGIN`;
- `A90_M1_DIAG_HELPER_WAIT_DONE` for each helper pid.

The future live collection contract explicitly requires:

- wait for service helper completion before artifact pull;
- poll JSONL files for terminal `stop` records before classifying zero payloads;
- classify any missing terminal `stop` as `partial-helper-still-running`;
- do not repeat the V2447 early-pull failure.

## Dry-Run Result

Materialized dry-run:

```json
{
  "decision": "v2449-acdb-m1-diagnostic-observer-dry-run",
  "ok": true,
  "source_ok": true,
  "command_safety_ok": true,
  "module_ok": true,
  "future_live_ready": true
}
```

Future exact gate:

```text
AUD-5K-acdb-m1-diagnostic-observer go: rollbackable Android AudioTrack speaker msm_audio_cal diagnostic ioctl capture with temporary Magisk service module, helper-completion wait, no native calibration ioctl, no native speaker write, rollback to V2321
```

## Safety Boundary

V2449 itself is host-only.

The helper and planner preserve the ACDB safety boundary:

- no helper open of `/dev/msm_audio_cal`;
- no native calibration ioctl;
- no native ACDB replay;
- no native speaker write;
- no mixer writes;
- no `tinyplay`;
- no persistent Magisk install;
- no `post-fs-data` early hook;
- no boot/partition/device action in this V-iteration.

## Validation

Commands run:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_planner_v2449.py \
  tests/test_native_audio_acdb_m1_diag_observer_planner_v2449.py

aarch64-linux-gnu-gcc -O2 -static -s -Wall -Wextra \
  -o workspace/private/builds/audio/v2449-diag-helper-test/a90_acdb_ioctl_capture_diag_v2449 \
  workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_diag_v2449.c

file workspace/private/builds/audio/v2449-diag-helper-test/a90_acdb_ioctl_capture_diag_v2449

python3 -m unittest discover -s tests \
  -p 'test_native_audio_acdb_m1_diag_observer_planner_v2449.py'

python3 workspace/public/src/scripts/revalidation/native_audio_acdb_m1_diag_observer_planner_v2449.py \
  --dry-run --materialize-module-template

python3 -m unittest discover -s tests
```

Observed validation:

- Python compile: pass.
- AArch64 helper compile: pass.
- `file`: `ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped`.
- Focused unittest: `6` tests pass.
- Materialized dry-run: `future_live_ready=true`.
- Full unittest discovery: `1228` tests pass.

## Next

Next meaningful unit is a live V2450/AUD-5K rerun using the V2449 diagnostic
observer.  It should use the exact gate above, keep the V2321 rollback envelope,
and report one of:

- `msm-audio-cal-payload-captured`;
- `ioctl-any-but-fd-miss`;
- `fd-readlink-miss`;
- `syscall-stops-no-ioctl`;
- `no-syscall-stops`;
- `partial-helper-still-running`;
- or another explicitly evidenced diagnostic classification.

Do not attempt native ACDB replay until command order, decoded headers, private
payload hashes, mem-handle policy, and cleanup/rollback behavior are pinned.
