# NATIVE_INIT V2647 — ACDB SET-cal replay header mem_handle fix

Date: 2026-06-18

## Scope

Host-only fix for the V2646 live blocker. V2646 proved the V2645
header-only/nonzero-cal-size fix worked, but the replay stopped at cal_type `12`
with:

```text
AUDIO_SET_CALIBRATION failed rc=-1 errno=22 strerror=Invalid argument cal_type=12 buffer=0 cal_size=0 mem_handle=17 arg_len=48
```

No device action, flash, `/dev/msm_audio_cal` ioctl, PCM probe, or raw payload
publication occurred in this unit.

## Captured Arg Header Inspection

The V2636 private deploy manifest and exact arg files were parsed host-side.
Relevant header-only records:

| seq | cal_type | role | len | cal_size | mem_handle | policy |
| ---: | ---: | --- | ---: | ---: | ---: | --- |
| 1 | 13 | `APP_META_HEADER` | 40 | 0 | -1 | preserve |
| 2 | 9 | `AFE_TOPOLOGY_HEADER` | 52 | 0 | -1 | preserve |
| 4 | 12 | `VOL_HEADER_NO_PAYLOAD` | 48 | 0 | 17 | neutralize to -1 |
| 6 | 23 | `AFE_TOPOLOGY_ID_HEADER` | 48 | 0 | -1 | preserve |
| 8 | 21 | `SPEAKER_VI_HEADER` | 72 | 28 | -1 | preserve inline/nonzero exact arg |

Conclusion: cal_type `12` carries a stale positive `mem_handle` even though it has
`cal_size=0` and no external dma-buf payload. In native replay that integer is
not a valid fd in the helper process, and the kernel rejects the SET with
`EINVAL`.

## Change

The V2635 helper now applies a narrow normalization only for header/no-payload
exact SET entries where `cal_size==0` and the captured `mem_handle` is non-negative:

- patch `mem_handle` to `-1` in the transient SET arg copy;
- log `A90_ACDB_SETCAL_HEADER_MEM_HANDLE_NEUTRALIZED` with the original handle;
- preserve the original arg file on disk;
- leave payload-backed entries unchanged;
- leave inline/nonzero header records such as cal_type `21` unchanged.

## Result

- decision: `v2647-header-mem-handle-policy-fixed-host-only`
- helper_source: `workspace/public/src/native-init/helpers/a90_acdb_setcal_replay_scaffold_v2635.c`
- private_helper: `workspace/private/builds/audio/v2635-audio-acdb-setcal-replay-helper-gate/bin/a90_acdb_setcal_replay_execute_v2635`
- private_helper_sha256: `376f93488514467a40b7af4c3842004d553cf73fade90a2aef1aaa8e29e4da05`
- deploy_manifest_refreshed: `workspace/private/builds/audio/v2636-audio-acdb-setcal-replay-deploy-plan/deploy-plan.json`
- V2636 helper entry verifies the same SHA and `all_inputs_ok=True`.

## Safety

This is not a new replay scope. It only prevents a captured stale fd value from
being treated as valid in the helper process for zero-sized header records. It
does not synthesize calibration bytes, add a new ioctl, change route controls,
or touch payload-backed allocation/deallocation semantics.

## Validation

- `python3 -m py_compile` for V2635/V2636/V2638/V2639 scripts and tests.
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_setcal_replay_helper_gate_v2635 tests.test_native_audio_acdb_setcal_replay_deploy_plan_v2636 tests.test_native_audio_acdb_setcal_replay_live_runner_plan_v2638 tests.test_native_audio_acdb_setcal_replay_live_handoff_v2639 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_helper_gate_v2635.py --build-helper --write-report --manifest-path workspace/private/builds/audio/v2635-audio-acdb-setcal-replay-helper-gate/manifest.json`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_deploy_plan_v2636.py --private-manifest workspace/private/builds/audio/v2636-audio-acdb-setcal-replay-deploy-plan/deploy-plan.json --write-report`
- `strings` marker check confirms `A90_ACDB_SETCAL_HEADER_MEM_HANDLE_NEUTRALIZED` exists and the old `exact arg requires payload` blocker is absent.
- `git diff --check`

## Next Unit

A single V2639 live rerun is meaningful. Expected discriminator:

- If cal_type `12` now SETs successfully, watch the next SET boundary and PCM
  prepare dmesg.
- If another header/no-payload record fails with stale-handle semantics, stop and
  fix host-only; do not retry-loop live.
- If all SETs complete, the runner may attempt the bounded low-amplitude PCM
  probe and classify the next kernel-side audio gate.
