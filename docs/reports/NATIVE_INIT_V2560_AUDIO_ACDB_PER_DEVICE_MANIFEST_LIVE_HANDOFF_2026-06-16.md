# NATIVE_INIT V2560 — ACDB per-device manifest live handoff

Date: 2026-06-16

## Decision

`v2560-init-common-topology-recaptured-before-per-device-rollback-pass`

The V2560 Android handoff completed and rolled back safely to V2321, but it did **not** capture per-device AFE/ASM/ADM/AUDPROC/VOL calibration payloads.  The first generated V2560 wrapper result over-classified the run because it counted a 16-byte ACDB init record as a per-device record.  The corrected classifier requires a helper-side `send_audio_cal_v5` stage marker and excludes known init/topology commands.

## Scope

- Android own-process ACDB capture handoff using the V2490 checked Android boot/stage/pull/rollback engine.
- V2559 helper/preload artifacts were staged privately.
- `A90_ACDB_FAKE_ALLOCATE=1` remained enabled; real `AUDIO_SET_CALIBRATION` pass-through stayed at zero.
- Raw ACDB buffers remain private under the run directory and are not committed.

## Result

| Field | Value |
| --- | --- |
| Run dir | `workspace/private/runs/audio/v2560-acdb-per-device-manifest-20260616-103940` |
| Corrected decision | `v2560-init-common-topology-recaptured-before-per-device-rollback-pass` |
| Corrected ok | `False` |
| Rollback | `pass` |
| Final health | V2321 `0.9.285`, manual `selftest fail=0` |
| Real `AUDIO_SET_CALIBRATION` pass-through | `0` |

## Corrected Capture Summary

| Metric | Value |
| --- | --- |
| `send_audio_cal_v5_reached` | `False` |
| `topology_success_count` | `1` |
| `per_device_success_count` | `0` |
| `successful_nonzero_count` | `5` |
| `size_query_count` | `3` |
| `fake_audio_set_count` | `1` |
| `fake_audio_set_cal_types_observed` | `[39]` |

The captured successful non-zero rows are still the known init/topology set:

| Seq | Cmd | Out len | SHA-256 |
| --- | --- | --- | --- |
| `0x00000000` | `0x000131de` | `16` | `25513169f466cb63e98fe30731e7c577f76cb6b58283d4041b1c650d0bf0915c` |
| `0x00000001` | `0x00013262` | `4` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` |
| `0x00000002` | `0x00013297` | `4` | `57e0c8cd1fbd539454489e739d06a59027fab0432f6f7187b7a39bb76ffc2bae` |
| `0x00000003` | `0x00013296` | `4916` | `7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89` |
| `0x00000003` | `0x00013296` | `4` | `57e0c8cd1fbd539454489e739d06a59027fab0432f6f7187b7a39bb76ffc2bae` |

## Interpretation

`acdb_loader_init_v3` itself reaches the common-topology path and still segfaults before returning to the helper.  Therefore the V2559 helper never writes the `before_send_audio_cal_v5` marker and never reaches the intended `acdb_loader_send_audio_cal_v5(...)` call.

This means V2559's "skip common topology after init" design is insufficient: the crash happens inside init, before the helper has a chance to skip anything.  The 4916-byte topology payload remains valid and pinned, but per-device payload capture is still blocked.

## Corrective Change Made

The V2560 classifier now requires both:

1. a helper-stage marker proving `send_audio_cal_v5` was reached; and
2. a non-zero `ret==0` ACDB out-buffer with `out_len` not in `{4, 4916}` and not from the known init/topology command set.

A private sidecar records the corrected result:

- `workspace/private/runs/audio/v2560-acdb-per-device-manifest-20260616-103940/v2560-corrected-analysis.json`

## Next Unit

Per-device capture must move earlier or bypass the init common-topology tail.  The next host-only design should avoid relying on `acdb_loader_init_v3` returning before `send_audio_cal_v5`, for example by interposing or short-circuiting the init-time common-topology call itself, or by directly calling the per-device ACDB GET commands once their command IDs and input structs are pinned.

Native full-calibration replay remains blocked until per-device payloads are captured with command/order, lengths, SHA-256, memory-handle policy, cleanup, and rollback behavior.

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_per_device_manifest_live_handoff_v2560.py
PYTHONPATH=tests python3 -m unittest tests.test_native_audio_acdb_per_device_manifest_live_handoff_v2560 -v
python3 workspace/public/src/scripts/revalidation/native_audio_acdb_per_device_manifest_live_handoff_v2560.py --build-v2559-artifacts
python3 workspace/public/src/scripts/revalidation/native_audio_acdb_per_device_manifest_live_handoff_v2560.py --run-live --write-report --build-v2559-artifacts --helper-timeout 120
python3 workspace/public/src/scripts/revalidation/a90ctl.py version
python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose
```

Result: focused tests passed; dry-run was live-ready; live handoff rolled back to V2321; final manual `selftest verbose` reported `fail=0`.
