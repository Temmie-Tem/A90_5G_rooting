# V2413 — AUD-5C msm_audio_cal live open-only preflight

Scope: exact-gated live AUD-5C execution after V2411/V2412. This unit reused the V2334 ADSP + `/dev/snd` materialization window, inventoried `/proc/misc`, materialized a runtime `/dev/msm_audio_cal` node from the dynamic misc minor, performed one open/close-only probe, removed the node it created, and rolled back to V2321.

No calibration ioctl, ACDB payload, mixer route write, PCM write/playback, Android handoff, or Magisk action was executed.

## Code changes

- Added live runner:

```text
workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py
```

- Added focused host-only tests:

```text
tests/test_native_audio_msm_audio_cal_preflight_live_handoff_v2413.py
```

- Corrected the V2412 dry-run shell path from `/bin/sh` to `/bin/busybox sh`. The first V2413 live attempt proved why this matters: V2334 native does not provide `/bin/sh`, so the initial inventory command failed with `execve(/bin/sh): No such file or directory`. Rollback to V2321 still completed with `selftest fail=0`; the fixed runner then completed the live unit.

## Live gate

The runner used the carried-forward exact phrase:

```text
AUD-5C-msm-audio-cal-preflight go: one-shot /dev/msm_audio_cal existence/open-only inventory on V2334, no AUDIO_SET ioctls, no ACDB payload, no playback, rollback to V2321
```

## Successful live result

Private evidence:

```text
workspace/private/runs/audio/v2413-msm-audio-cal-preflight-20260615-090434/result.json
```

Summary:

```json
{
  "decision": "v2413-msm-audio-cal-preflight-live-pass-before-rollback",
  "rolled_back": true,
  "rollback_version_ok": true,
  "rollback_selftest_fail0": true,
  "adsp_boot_once": "accepted-protocol-ok",
  "dev_snd_count": 61,
  "dev_snd_pcm_like": 59,
  "msm_audio_cal_minor": "54",
  "msm_audio_cal_opened": true,
  "msm_audio_cal_opened_mode": "O_RDONLY",
  "created_runtime_node_removed": true
}
```

Observed sequence:

1. Resident V2321 verified via checked helper and `selftest fail=0`.
2. V2334 flashed via `native_init_flash.py`; candidate `0.9.292` selftest passed.
3. ADSP boot-one-shot accepted with protocol OK.
4. Sound card materialized; `/dev/snd` reported 61 nodes, including control and PCM nodes.
5. `/proc/misc` exposed `msm_audio_cal` with minor `54`.
6. `/dev/msm_audio_cal` was missing before materialization.
7. Runner created `crw------- root root 10,54 /dev/msm_audio_cal` in runtime `/dev` only.
8. One O_RDONLY open/close-only probe succeeded.
9. The runner removed the node it created and verified it was absent afterward.
10. V2321 rollback completed through the checked helper; final rollback selftest was `fail=0`.

## Interpretation

N2 `/dev/msm_audio_cal` reachability is now proven under native init after ADSP + `/dev/snd` materialization:

- The kernel misc device is registered (`/proc/misc` minor `54`).
- The native runtime can create the matching `/dev/msm_audio_cal` node.
- A read-only open succeeds without issuing calibration ioctls.
- The node can be removed cleanly when created by the runner.

This does **not** prove any ACDB payload replay path yet. V2411 remains the boundary: real calibration ioctls `200`–`205` can dispatch registered callbacks and mutate calibration state, so N3 must not be attempted until the exact Android-good ioctl/payload bytes are pinned and a separate bounded design exists.

## Magisk-module direction

V2413 did not use Magisk. The current strategy remains:

- Native runtime path should not depend on Magisk modules.
- The successful V2407 M0 transient Magisk-root capture already provided the App Type / ACDB log edge needed for N1.
- Future Magisk use is measurement-only: M0 transient helper first, M1 temporary boot module only if a future Android-good capture misses early `/dev/msm_audio_cal` ioctl payloads that are required to design N3.

This matches the earlier Wi-Fi-style pattern: use Android/Magisk to observe vendor behavior, then port only bounded, source-reviewed facts into native init.

## Validation

Host/static validation:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py \
  workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py \
  tests/test_native_audio_msm_audio_cal_preflight_gate_v2412.py \
  tests/test_native_audio_msm_audio_cal_preflight_live_handoff_v2413.py
python3 -m unittest discover -s tests -p 'test_native_audio_msm_audio_cal_preflight_gate_v2412.py'
python3 -m unittest discover -s tests -p 'test_native_audio_msm_audio_cal_preflight_live_handoff_v2413.py'
python3 workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py --dry-run
```

Live validation:

```text
python3 workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py --run-live --approval '<exact phrase>'
```

Result: pass before rollback; rollback V2321 `selftest fail=0`.

## Next frontier

AUD-5C/N2 is closed as reachable/openable. The next meaningful host-only unit is N3 design: derive a safe ACDB payload replay boundary from Android-good evidence and source, including exact ioctl numbers, payload provenance, reset/abort behavior, and whether another Android/Magisk measurement is needed to capture payload bytes. Do not send any calibration ioctl from native init until that design is complete and reviewed.
