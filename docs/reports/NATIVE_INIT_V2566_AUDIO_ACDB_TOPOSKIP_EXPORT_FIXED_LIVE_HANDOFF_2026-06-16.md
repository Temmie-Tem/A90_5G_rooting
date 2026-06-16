# NATIVE_INIT V2566 — ACDB topology-skip export-fixed live handoff

Date: 2026-06-16

## Scope

One rollbackable Android own-process ACDB live handoff using the V2565-fixed V2561 preload export.

This is the follow-up to V2564:

- V2564 showed the intended `acdb_loader_send_common_custom_topology()` short-circuit did not run.
- V2565 fixed the preload export to `GLOBAL DEFAULT`.
- V2566 reran the same bounded live path with the rebuilt preload.

No native replay, speaker write, real `AUDIO_SET_CALIBRATION`, or raw ACDB payload commit was performed.

## Result

- decision: `v2564-partial-nonzero-acdbtap-capture-rollback-pass`
- local classification: `v2566-toposkip-marker-present-helper-sigsegv-before-per-device`
- runner ok: `False`
- out_dir: `workspace/private/runs/audio/v2566-acdb-toposkip-export-fixed-20260616-114048`
- topology_skip_marker_count: `1`
- helper exit: `139` / `Segmentation fault`
- send_audio_cal_v5_reached: `False`
- topology_success_count: `0`
- per_device_success_count: `0`
- successful_nonzero_count: `2`
- real_audio_set_pass_through_count: `0`
- counts_toward_fails_twice: `False`
- rollback: V2321 restored, final `selftest fail=0`

## Evidence

The V2565 export fix worked. The live device produced the topology-skip marker:

```json
{"event":"topology_skip","stage":"common_topology_short_circuit","code":0,"payload_len":4916,"payload_sha256":"7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89","pid":3980,"tid":3980}
```

The helper then crashed before reaching the intended per-device `acdb_loader_send_audio_cal_v5()` call:

```text
ownget.rc: 139
ownget.stderr: Segmentation fault
```

Captured ACDB rows before the crash:

| seq | cmd | ret | out_len | all_zero | sha256 |
| --- | --- | --- | --- | --- | --- |
| `0x00000000` | `0x000131de` | `0x00000000` | `0x00000010` | `false` | `25513169f466cb63e98fe30731e7c577f76cb6b58283d4041b1c650d0bf0915c` |
| `0x00000001` | `0x00013262` | `0x00000000` | `0x00000004` | `false` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` |

The ioctl trace showed no real calibration SET pass-through:

| ioctl class | count | intercept |
| --- | ---: | --- |
| `AUDIO_ALLOCATE_CALIBRATION` | `25` | `fake-success` |
| `unknown` | `28` | `pass-through` |

## Artifacts

- helper_sha256: `4256a5a79e8da703a8c4b8ee301c7af0c69ad8ede5b9810ae9ea0591139fd1ae`
- preload_sha256: `7a37cebb38fae83d9cd0882861aacba77dfd490ce28d2cc1254cab75323259ae`
- detailed result: `workspace/private/runs/audio/v2566-acdb-toposkip-export-fixed-20260616-114048/v2564-result.json`
- base handoff result: `workspace/private/runs/audio/v2566-acdb-toposkip-export-fixed-20260616-114048/result.json`

Raw ACDB buffers and vendor libraries remain private under the run directory and are not committed.

## Boundary

- The topology-skip marker confirms the V2565 dynamic export fix is live-effective.
- The run did not reach the per-device calibration fetch path.
- The run did not issue any real `AUDIO_SET_CALIBRATION` pass-through.
- The device was rolled back to V2321 and verified with `selftest fail=0`.

## Decision

`v2566-toposkip-marker-present-helper-sigsegv-before-per-device` is an informative partial success, not a dead retry.

The next unit should not re-run the same path unchanged. The remaining blocker is the post-topology-skip crash before `send_audio_cal_v5`; inspect the call boundary/ABI around `acdb_loader_send_audio_cal_v5(15, 0, 0x11135, 48000, 48000, 0, 1)` and add host-side crash localization before any further live retry.
