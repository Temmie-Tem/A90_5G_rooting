# NATIVE_INIT_V2448_AUDIO_ACDB_M1_CAPTURE_METHOD_DIAGNOSIS_2026-06-15

## Summary

V2448 is host-only analysis of the V2447 M1 temporary Magisk module run. It rechecks the
V2423 threadset ptrace helper source and the private V2447 artifacts to classify why
V2447 reached Android playback and attached the logcat-proven audio HAL worker but still
reported `0` `/dev/msm_audio_cal` ioctl entries.

Conclusion: do **not** rerun M1 unchanged. The V2447 result is not a clean negative. The
module delivery worked, and worker TID `12004` was attached, but artifact collection pulled
the helper JSONL files before the relevant helpers had completed, and the helper records
only fd-matched ioctl entries. It does not record enough nonmatching syscall telemetry to
distinguish:

- no syscall stops,
- syscall stops but no `ioctl`,
- `ioctl` on a different fd/path,
- fd resolution miss,
- syscall entry/exit parity issue,
- or a real absence of `/dev/msm_audio_cal` ioctls.

The next unit should be a host-only diagnostic-helper/runner fix: add timestamps and
nonmatching syscall/ioctl counters, and make the runner wait for helper completion before
classifying zero payloads.

## Source Findings

Relevant helper:

```text
workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_threadset_v2423.c
```

Confirmed source behavior:

- The helper attaches all existing TIDs with `PTRACE_ATTACH`.
- It enables `PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACECLONE`.
- It resumes with `PTRACE_SYSCALL`.
- It reads arm64 syscall registers via `PTRACE_GETREGSET` / `NT_PRSTATUS`.
- It filters for `__NR_ioctl`.
- It then filters ioctl fd targets by resolving `/proc/<fd_pid>/fd/<fd>` and requiring the
  substring `/dev/msm_audio_cal`.
- It writes JSONL only for matching `ioctl_entry` / `ioctl_exit`.

Diagnostic gap:

```text
handle_syscall_stop()
  if entering:
    syscall_nr = regs.regs[8]
    if syscall_nr == __NR_ioctl:
      if fd_matches_device(... "/dev/msm_audio_cal" ...):
        write ioctl_entry
  else if pending.active:
    write ioctl_exit
```

The helper does **not** currently write public-safe counters for:

- total syscall stops,
- total syscall entries,
- total `ioctl` entries before fd filtering,
- fd-resolution failures,
- unmatched ioctl fd targets,
- first-N unmatched ioctl request numbers and fd targets,
- per-tracee entry/exit parity state,
- event timestamps.

Therefore a zero-entry JSONL is ambiguous.

## V2447 Artifact Findings

Private run:

```text
workspace/private/runs/audio/v2447-acdb-m1-magisk-module-retry-20260615-151404/
```

Public-safe summary:

```json
{
  "classification": "threadset-attached-no-msm-audio-cal-ioctl",
  "helper_starts": 10,
  "tracee_adds": 138,
  "clone_events": 90,
  "ioctl_entries": 0,
  "ioctl_exits": 0
}
```

The relevant audio HAL worker was followed:

```json
{"event":"tracee-add","tid":12004}
{"event":"clone","tid":9023,"child_tid":12004}
{"event":"clone-child-resumed","tid":12004}
```

Logcat simultaneously shows that worker performing the speaker path:

```text
audio_hw_primary: start_output_stream ... usecase(0: deep-buffer-playback) devices(0x2)
audio_hw_primary: select_devices ... to (2: speaker, acdb 15)
audio_hw_utils: send_app_type_cfg_for_device PLAYBACK app_type 69941, acdb_dev_id 15
ACDB-LOADER: ACDB -> send_audio_cal, acdb_id = 15, path = 0, app id = 0x11135
ACDB-LOADER: AUDIO_SET_AUDPROC_CAL cal_type[11] acdb_id[15] app_type[69941]
```

But the p8795 helper file is incomplete at collection time. Its tail ends immediately after
the worker is resumed:

```json
{"event":"tracee-add","tid":12004}
{"event":"clone","tid":9023,"child_tid":12004}
{"event":"clone-child-resumed","tid":12004}
```

There is no terminal `stop` event for p8795 or p8796 in the pulled artifacts:

```text
msm-audio-cal-threadset-p8795.jsonl: stop event absent
msm-audio-cal-threadset-p8796.jsonl: stop event absent
```

That means V2447 pulled active helper files before the relevant helpers completed. Earlier
helpers that finished do have terminal records such as:

```json
{"event":"stop","captured_entries":0,"tracees":20,"timed_out":true}
```

The M1 service confirms why this can happen:

```text
A90_M1_SERVICE_BEGIN duration=180 max_bytes=512 process_poll_sec=0.2
A90_M1_HELPER_START tgid=8795 remaining=49 helper_duration=49 mode=threadset-clone-following
A90_M1_HELPER_START tgid=8796 remaining=49 helper_duration=49 mode=threadset-clone-following
```

The V2446 runner only waits:

```python
wait_sec = max(capture_observe_sec, duration_ms / 1000.0 + post_delay_sec + 1.0)
```

with default `capture_observe_sec=6.0`. That is sufficient for playback/logcat, but not
sufficient to guarantee helper completion when the M1 service still has about `49s` left for
the newly discovered audio HAL/audioserver pids.

## Interpretation

V2447 closes these hypotheses:

- M1 temporary module cannot run: false.
- Android post-module wait budget is too short: fixed by V2446/V2447.
- The ACDB edge is absent: false; logcat shows it.
- The audio HAL worker TID is completely missed: false; TID `12004` was followed.

V2447 does not close these hypotheses:

- The helper is receiving syscall stops at all after TID `12004` resumes.
- The helper is seeing `ioctl` but missing the `/dev/msm_audio_cal` fd target.
- The helper is seeing `ioctl` on a path alias or short-lived fd not visible through the
  current `/proc/<tgid>/fd/<fd>` lookup.
- The helper's initial entry/exit parity is wrong for pre-existing attached threads.
- The payload edge occurs after the artifact pull.

The highest-confidence immediate blocker is observability quality, not Android/Magisk
delivery.

## Magisk Module Direction

Keep the user's Wi-Fi-style Magisk-module pattern, but use it precisely:

- Keep M1 as a temporary Android-good measurement capsule.
- Use `service.sh` for early placement and helper packaging.
- Keep exact cleanup and rollback.
- Keep raw payloads private.
- Do not treat Magisk as a native-init runtime dependency.

For the next run, the module should host a better observer rather than the same observer.
Reworking install/wait/cleanup again is low value unless the new observer changes require it.

## Next Unit

V2449 should be host-only implementation of a diagnostic M1 capture revision.

Required changes:

1. Add timestamps to every service/helper event:
   - service wall time,
   - helper monotonic milliseconds,
   - JSONL event timestamp.
2. Add public-safe counters:
   - `syscall_stop_count`,
   - `syscall_entry_count`,
   - `ioctl_any_entry_count`,
   - `ioctl_fd_match_count`,
   - `ioctl_fd_miss_count`,
   - `fd_readlink_error_count`.
3. Add bounded first-N unmatched ioctl samples without raw payload:
   - TID,
   - fd,
   - request number,
   - fd target or readlink error.
4. Preserve raw payload capture only for matched `/dev/msm_audio_cal` ioctls and keep it
   private.
5. Change result classification:
   - if relevant p8795/p8796 JSONL lacks `stop`, classify `partial-helper-still-running`,
     not `threadset-attached-no-msm-audio-cal-ioctl`.
6. Make the runner wait for helper completion or explicitly poll for terminal `stop` markers
   before collection. A bounded longer wait is acceptable because this is Android-good
   measurement, not native runtime.

Future live criteria:

- Do not run M1 unchanged.
- Do not attempt native ACDB replay.
- Only after the diagnostic observer proves matched ioctl payloads, or proves a different
  lower-level path, should the native side be redesigned.

