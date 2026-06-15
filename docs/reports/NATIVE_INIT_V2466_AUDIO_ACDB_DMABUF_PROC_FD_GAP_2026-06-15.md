# NATIVE_INIT_V2466_AUDIO_ACDB_DMABUF_PROC_FD_GAP_2026-06-15

## Scope

Fresh bounded Android-good ACDB dmabuf capture rerun using the V2465-hardened
stage ADB retry wrapper.

The run stayed inside the GOAL.md recoverable envelope:

- Android boot image was flashed only through the checked helper path;
- temporary Magisk measurement capsule state was staged and cleaned up;
- Android `AudioTrack` speaker playback was used only as the known-good
  measurement stimulus;
- no native `/dev/msm_audio_cal` calibration ioctl was issued;
- checked rollback to V2321 completed.

Private raw artifacts remain under:

`workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/`

## Decision

`v2466-android-good-setcal-reached-dmabuf-proc-fd-open-failed-rollback-pass`

V2466 closed the V2464 transport/staging gap, but did not capture the required
4916-byte custom-topology dmabuf payload.

The previous V2464 `stage-2` ADB closure did not recur. All ten staged
commands completed on attempt 1 with the V2465 naming/evidence model:

- `stage-0-attempt-1` through `stage-9-attempt-1` all returned `rc=0`;
- every stage command also had a preceding `adb wait-for-device` step;
- no semantic residue/hash/install failure marker was observed.

The run reached the intended Android-good measurement window and collected
`/dev/msm_audio_cal` ioctl metadata. However, every custom-topology dmabuf
capture attempt failed while opening the target process fd through
`/proc/<tgid>/fd/<mem_handle>`.

## Live evidence

Top-level runner result:

```json
{
  "decision": "v2451-acdb-m1-hybrid-late-observer-payload-captured-before-rollback-rollback-pass",
  "ok": true,
  "rolled_back": true
}
```

Payload summary:

```json
{
  "classification": "msm-audio-cal-payload-captured",
  "ioctl_entries": 116,
  "ioctl_fd_match_count": 116,
  "dmabuf_payload_count": 0,
  "dmabuf_payload_hashes": []
}
```

The summary classification is true only for public ioctl header capture. It is
not a dmabuf topology-payload success.

Four custom-topology `AUDIO_SET_CALIBRATION` events were recognized:

| Source process | seq | cal_type | cal_size | mem_handle | status | open_errno |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| p4381 | 28 | 39 | 4916 | 37 | `open-proc-fd-failed` | 6 |
| p7248 | 28 | 39 | 4916 | 35 | `open-proc-fd-failed` | 6 |
| p802 | 28 | 39 | 4916 | 37 | `open-proc-fd-failed` | 6 |
| p8763 | 28 | 39 | 4916 | 37 | `open-proc-fd-failed` | 6 |

No `dmabuf-seq*.bin` file was produced, and therefore no private dmabuf SHA-256
hash exists for native replay design.

Late observer status:

```json
{
  "classification": "late-partial-helper-still-running",
  "ioctl_entries": 0,
  "dmabuf_capture_events": [],
  "wait_done_markers": [
    "A90_M1_LATE_DIAG_HELPER_WAIT_DONE tgid=8763 helper_pid=11812 rc=3 mode=late-diagnostic",
    "A90_M1_LATE_DIAG_HELPER_WAIT_DONE tgid=8765 helper_pid=11850 rc=3 mode=late-diagnostic"
  ]
}
```

The useful capture came from the thread-set observer artifacts, not from the
late observer window.

## Source-backed interpretation

Kernel source confirms the native replay boundary remains the same:

- `audio_cal_shared_ioctl()` copies only the ioctl argument buffer from
  userspace and dispatches `AUDIO_SET_CALIBRATION` through registered
  calibration callbacks.
- `cal_utils_set_cal()` reads `audio_cal_type_basic.cal_data.mem_handle`, looks
  up an existing allocation when `mem_handle > 0`, and then maps the referenced
  calibration block before sending it to the DSP.
- `create_cal_block()` stores `basic_cal->cal_data.mem_handle` as
  `cal_block->map_data.ion_map_handle` and calls the ION import path when it is
  positive.
- The stock dmabuf file object is backed by `dma_buf_fops`, supports `mmap`, and
  is normally a userspace file descriptor, but the V2463 `/proc/<tgid>/fd/<fd>`
  duplication strategy failed live with errno `6`.

Therefore V2466 proves one concrete negative fact: **the current
`/proc/<tgid>/fd/<mem_handle>` duplication path is not a sufficient dmabuf
payload capture method for this Android-good audio service path.**

It does not prove that the payload is absent, that `mem_handle` is invalid to the
kernel, or that native ACDB replay is viable. It only says the implemented
observer could not open that fd path at the moment it saw the SET_CALIBRATION
header.

## Rollback / health

Rollback sequence:

- Android ADB was available before rollback.
- `adb reboot recovery` returned `rc=0`.
- Checked V2321 flash through `native_init_flash.py` returned `rc=0`.

Independent post-run native health check on resident V2321:

```text
A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
selftest: pass=11 warn=1 fail=0
```

## Next safe unit

Do not rerun the unchanged V2463/V2465 dmabuf capture path. It already reached
the measurement edge and failed at the same per-fd duplication point four times
inside one successful Android-good run.

Next meaningful unit is host-only V2467 fallback design/implementation for the
dmabuf payload capture, grounded in source and V2466 evidence. Candidate
directions:

1. capture the ION/dmabuf allocation and `mmap` lifecycle in the 32-bit audio
   process instead of duplicating `/proc/<tgid>/fd/<mem_handle>` only at
   `AUDIO_SET_CALIBRATION`;
2. snapshot `/proc/<tgid>/fd`, `/proc/<tgid>/fdinfo`, and relevant mappings near
   the SET_CALIBRATION event rather than only at helper start;
3. if the userspace mapping address is recoverable from the live `mmap` return,
   copy the declared 4916 bytes from the traced process memory with the same
   private-artifact/no-raw-commit discipline.

Native `/dev/msm_audio_cal` calibration ioctls remain blocked until the
Android-good dmabuf payload bytes, length, hash, mem-handle lifetime, and
cleanup policy are pinned.
