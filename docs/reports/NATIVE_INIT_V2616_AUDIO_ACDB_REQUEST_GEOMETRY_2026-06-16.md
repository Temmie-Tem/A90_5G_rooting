# NATIVE_INIT V2616 — ACDB request geometry

Date: 2026-06-16

## Scope

Host-only analysis of the V2614 private `acdbtap` run. This decodes metadata-sized
input/output words from ACDB GET calls so the next capture/replay design can use exact
request geometry. It does not touch the device, issue calibration `SET`, copy raw payload
bytes into public files, or mark native replay ready.

## Decision

- decision: `v2616-request-geometry-pinned`
- ok: `True`
- source_run: `workspace/private/runs/audio/v2614-acdb-meta-list-indirect-layout-live-20260616-192454`
- source_decision: `v2490-acdbtap-full-outbuf-set-no-4916-before-helper-exit-before-rollback-rollback-pass`
- native_replay_ready: `False`
- native_replay_blocked_reason: `operator Gate-2 mapping plus missing VOL/Afe topology decision are unresolved`

## Ordered ACDB GET Geometry

| seq | cmd | role | ret | input words | output word0 | candidate cal_type | note |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| `0x00000001` | `0x0001122e` | metadata | `0` | `0x00011135` | `0x10005000` |  | send_audio_cal_v5 first app metadata |
| `0x00000002` | `0x0001122d` | metadata | `0` | `0x0000000f, 0x00011135` | `0x10004000` |  | device/app metadata |
| `0x00000003` | `0x00013267` | size-query | `0` | `0x0000000f, 0x0000bb80, 0x00011135` | `0x000046a4` | 11 | AUDPROC instance common size |
| `0x00000004` | `0x00013265` | indirect-data | `0` | `0x0000000f, 0x0000bb80, 0x00011135, 0x000046a4, 0xf0eb3000` | `0x000046a4` | 11 | AUDPROC instance common data |
| `0x00000005` | `0x0001326d` | size-query | `-19` | `0x0000000f, 0x00011135, 0x00000000` | `0x00000000` | 12 | AUDPROC gain-dependent step size |
| `0x00000006` | `0x0001326e` | indirect-data | `-19` | `0x0000000f, 0x00011135, 0x00000000, 0x00001000, 0xf12d3000` | `0x00000000` | 12 | AUDPROC gain-dependent step data |
| `0x00000007` | `0x00013268` | size-query | `0` | `0x00011135` | `0x0000001c` | 15 | AUDPROC stream size |
| `0x00000008` | `0x00013269` | indirect-data | `0` | `0x00011135, 0x00001000, 0xf0f4e000` | `0x0000001c` | 15 | AUDPROC stream data |
| `0x00000009` | `0x000130d8` | metadata | `0` | `0x0000000f` | `0x1001025d` |  | AFE metadata |
| `0x0000000a` | `0x00013271` | size-query | `0` | `0x0000000f, 0x0000bb80` | `0x00000618` | 16 | AFE instance common size |
| `0x0000000b` | `0x0001326f` | indirect-data | `0` | `0x0000000f, 0x0000bb80, 0x00001000, 0xf0f4d000` | `0x00000618` | 16 | AFE instance common data |
| `0x0000000c` | `0x00012eeb` | metadata | `0` | `0x0000000f, 0x00000001, 0x000000cc, 0xffc1a3c4` | `0x0000001c` |  | tail metadata row |

## Pinned Request Fields

- `0x0001122e` send_audio_cal_v5 first app metadata: app_id=0x00011135
- `0x0001122d` device/app metadata: acdb_id=0x0000000f, app_id=0x00011135
- `0x00013267` AUDPROC instance common size: acdb_id=0x0000000f, sample_rate=0x0000bb80, app_id=0x00011135
- `0x00013265` AUDPROC instance common data: acdb_id=0x0000000f, sample_rate=0x0000bb80, app_id=0x00011135, capacity=0x000046a4, out_ptr=0xf0eb3000
- `0x0001326d` AUDPROC gain-dependent step size: acdb_id=0x0000000f, app_id=0x00011135, gain_step=0x00000000
- `0x0001326e` AUDPROC gain-dependent step data: acdb_id=0x0000000f, app_id=0x00011135, gain_step=0x00000000, capacity=0x00001000, out_ptr=0xf12d3000
- `0x00013268` AUDPROC stream size: app_id=0x00011135
- `0x00013269` AUDPROC stream data: app_id=0x00011135, capacity=0x00001000, out_ptr=0xf0f4e000
- `0x000130d8` AFE metadata: acdb_id=0x0000000f
- `0x00013271` AFE instance common size: acdb_id=0x0000000f, sample_rate=0x0000bb80
- `0x0001326f` AFE instance common data: acdb_id=0x0000000f, sample_rate=0x0000bb80, capacity=0x00001000, out_ptr=0xf0f4d000
- `0x00012eeb` tail metadata row: acdb_id=0x0000000f, path=0x00000001, word2=0x000000cc, word3=0xffc1a3c4

## Capture Interpretation

- AUDPROC common (`0x13265`) captured a valid non-zero indirect payload for candidate cal_type 11.
- AUDPROC stream (`0x13269`) captured a valid non-zero indirect payload for candidate stream/ASM cal.
- AFE common (`0x1326f`) captured a valid non-zero indirect payload for candidate cal_type 16.
- VOL/gain (`0x1326d`/`0x1326e`) returned `-19` for `acdb_id=15`, `app_id=0x11135`, `gain_step=0`; no VOL payload exists in V2614.
- `0x130d8` returned AFE metadata `0x1001025d`; its relation to the V2393 cal_type 8/9 topology errors remains an operator Gate-2 question.

## Checks

- `source_run_ok`: `True`
- `rolled_back`: `True`
- `complete_expected_order`: `True`
- `audproc_common_payload_captured`: `True`
- `audproc_stream_payload_captured`: `True`
- `afe_common_payload_captured`: `True`
- `vol_size_ret_minus_19`: `True`
- `vol_data_ret_minus_19`: `True`

## Next Boundary

- next_recommended_unit: V2617 host-only design/build for a bounded lower-getter or send_v5 matrix focused on VOL cal_type 12 and AFE cal_type 8/9 coverage; do not run native SET replay yet
- Native replay remains blocked. This report supplies request geometry and operator questions only.

## Operator Questions

- Is VOL cal_type 12 mandatory when 0x1326d/0x1326e return -19 for speaker app_type 0x11135 gain_step 0?
- Does the captured topology plus AFE common table cover the V2393 cal_type 8/9 topology-id errors, or is a separate table required?
- Can the V2614 command order be mapped directly to the V2461/V2462 SET sequence before constructing a live replay manifest?

## Validation Commands

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_request_geometry_v2616.py tests/test_analyze_audio_acdb_request_geometry_v2616.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_request_geometry_v2616 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_request_geometry_v2616.py --write-report`
- `git diff --check`
