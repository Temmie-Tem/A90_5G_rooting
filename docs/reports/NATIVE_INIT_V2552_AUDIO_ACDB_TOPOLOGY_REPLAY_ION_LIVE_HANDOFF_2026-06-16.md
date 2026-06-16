# NATIVE_INIT V2552 — ACDB topology replay with ION materialization

Date: 2026-06-16
Run ID: V2552
Build tag: v2552-audio-acdb-topology-replay-ion-live-handoff
Scope: native audio / ACDB replay feasibility

## Purpose

V2551 proved the V2547 topology payload and V2549 replay helper could be staged, but the
native replay helper stopped before `AUDIO_SET_CALIBRATION` because `/dev/ion` was absent in
native init. V2552 adds runtime `/dev/ion` materialization from `/proc/misc` before launching
the topology replay helper, then reruns the bounded topology replay + PCM probe path.

This unit is still bounded and rollbackable:

- boot partition only via the checked flash helper;
- runtime devnodes only (`/dev/msm_audio_cal`, `/dev/ion`);
- pinned V2547 topology payload only;
- one bounded PCM probe;
- checked rollback to V2321.

## Implementation

Changed `native_audio_acdb_topology_replay_live_handoff_v2550.py` so the remote replay script:

1. reads the `msm_audio_cal` misc minor from `/proc/misc` and materializes `/dev/msm_audio_cal`;
2. reads the `ion` misc minor from `/proc/misc` and materializes `/dev/ion`;
3. fails closed with `A90_ACDB_REPLAY_NO_ION_MISC` if `ion` is not registered.

Added `native_audio_acdb_topology_replay_live_handoff_v2552.py` as the exact-gated live runner
for this ION-materialized replay unit.

After the live run, the evidence also exposed a runner cleanup-order bug: the helper cleanup
step removed the runtime directory before route reset, which deleted the staged `tinymix` used
by the reset commands. The V2552 runner was hardened host-side by splitting cleanup into:

- deallocate/stderr capture first, without removing the runtime directory;
- route reset and post-reset snapshot while `tinymix` still exists;
- runtime directory removal only after reset/snapshot.

That ordering fix was not live-rerun in this unit; it is a direct correction from the V2552
run evidence.

## Host validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2550.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2551.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2552.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_native_audio_acdb_topology_replay_live_handoff_v2550 \
  tests.test_native_audio_acdb_topology_replay_live_handoff_v2551 \
  tests.test_native_audio_acdb_topology_replay_live_handoff_v2552
```

Result: pass (`18` focused tests after the V2552 cleanup-order hardening).

Dry-run also returned:

- decision: `v2552-acdb-topology-replay-ion-live-handoff-dry-run`
- `ok=true`
- `run_id=V2552`
- `native_calibration_ioctls_run=false`
- `playback_run=false`
- generated replay script includes `/dev/ion` materialization.

## Pre-live device observation

On the resident V2321 checkpoint, a read-only probe showed both misc devices are registered but
not materialized as devnodes by default:

```text
/proc/misc:
 54 msm_audio_cal
 94 ion
/dev/ion: missing
/dev/msm_audio_cal: missing
```

## Live run

Run directory:

```text
workspace/private/runs/audio/v2552-acdb-topology-replay-ion-20260616-090802
```

Live command used the existing AUD-5N approval phrase and the checked V2334 -> V2321 handoff.

### Good results

The V2552 run crossed the V2551 blocker:

```text
A90_ACDB_REPLAY_SET_OK pid=720
```

The helper stderr confirms all three topology replay ioctls completed:

```text
AUDIO_ALLOCATE_CALIBRATION ok cal_type=39 buffer=0 cal_size=0 mem_handle=4
AUDIO_SET_CALIBRATION ok cal_type=39 buffer=0 cal_size=4916 mem_handle=4
AUDIO_DEALLOCATE_CALIBRATION ok cal_type=39 buffer=0 cal_size=0 mem_handle=4
```

Interpretation:

- `/dev/ion` materialization is sufficient for the replay helper to allocate/import a mem handle;
- the pinned V2547 4916-byte topology payload can be sent through `AUDIO_SET_CALIBRATION`;
- explicit deallocate was observed.

`msync dmabuf: Invalid argument` also appeared before the ioctl success messages. Since
`AUDIO_SET_CALIBRATION` returned success, this is recorded as a helper-side sync warning, not
the blocking failure in this unit.

### Blocking result

The bounded PCM probe still failed at the first write/prepare:

```text
A90_PCM_PROBE_START version=V2386 card=0 device=0 channels=2 rate=48000 bits=16 data_bytes=192000 period_size=1024 period_count=4
A90_PCM_PROBE_PCM_OPEN_OK buffer_frames=4096 buffer_bytes=16384
A90_PCM_PROBE_WRITE_ERROR chunk=0 rc=-1 errno=22 strerror="Invalid argument" pcm_error="cannot prepare channel: Invalid argument" bytes=16384 frames=4096
```

Decision:

```text
v2552-acdb-topology-replay-ion-live-blocked
```

The new audio blocker is no longer `/dev/ion`; it is `pcm_prepare` / first write returning
`EINVAL` even after topology-only calibration is set.

This matches the operator caveat: the 4916-byte `CORE_CUSTOM_TOPOLOGIES` payload is necessary,
but V2393/V2407 indicated the actual prepare failure also depends on per-device AFE / ASM / ADM /
AUDPROC / VOL calibration blocks. V2552 only replays topology cal_type `39`.

### Cleanup and rollback

The helper did deallocate, but the live runner then removed the runtime directory before route
reset. As a result, the reset commands and post-reset `tinymix` snapshot failed with:

```text
run: execve(/cache/a90-runtime/bin/v2550-acdb-topology-replay/tinymix): No such file or directory
[exit 127]
```

This was a runner-ordering bug, not an audio-kernel result. It is fixed host-side in V2552 by
moving runtime directory removal after reset/snapshot.

Rollback succeeded:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

## Conclusion

V2552 is a partial success:

- fixed the concrete `/dev/ion` materialization gap from V2551;
- proved topology-only native ACDB replay reaches `AUDIO_SET_CALIBRATION` and explicit deallocate;
- did not produce a working PCM stream;
- localized the next substantive blocker to missing non-topology calibration or insufficient
  calibration ordering, not to topology payload delivery.

## Next frontier

Do not repeat topology-only replay unchanged. The next meaningful unit should do one of:

1. capture and replay the ordered per-device calibration set in addition to topology
   (AFE/AUDPROC/ASM/ADM/VOL, using private payloads only); or
2. improve live dmesg/log capture around `pcm_prepare` while topology cal is held, so the
   exact q6asm/adm/afe failure point can be correlated with the missing cal class.

The runner cleanup-order hardening should be carried into any future replay live runner before
another device run.
