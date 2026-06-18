# NATIVE_INIT V2729 — vi-feedback ACDB SET capture live handoff

Date: 2026-06-18

## Scope

Android own-process ACDB vi-feedback SET-calibration capture using the V2490
checked Android boot/stage/pull/rollback engine and the V2728 helper/preload
artifacts. Measurement only: the SET ioctl is fake-successed in-process;
there is no native replay and no speaker write.

## Result

- decision: `v2729-setcal-records-no-cal17-rollback-pass`
- ok: `True`
- rolled_back: `True`
- operator_valuable: `True`
- partial_success: `True`
- success: `False`
- out_dir: `workspace/private/runs/audio/v2729-acdb-vi-feedback-setcal-capture-20260618-220651`
- classification: `v2729-setcal-records-no-cal17`
- setcal_record_count: `8`
- cal_types_seen: `[9, 11, 12, 13, 15, 16, 21, 23]`
- target_record_count: `0`
- target_payload_record_count: `0`
- target_dmabuf_dumped_count: `0`
- supplemental_cal_types_seen: `[11]`
- real_audio_set_pass_through_count: `0`
- counts_toward_fails_twice: `False`

## Interpretation

The explicit live approval was sufficient for this bounded unit, and the
approved Android handoff was executed. The run remained inside the measurement
envelope: the V2728 preload fake-successed Android `AUDIO_SET_CALIBRATION`,
no real kernel SET passed through, no native replay ran, and rollback to V2321
passed.

The attempted vi-feedback tuple
`send_audio_cal_v5(102,1,0x11132,8000,0,8000,1)` did not reproduce an Android
HAL `cal_type=17` vi-feedback SET. It emitted eight SET records with
cal_types `[13, 9, 11, 12, 15, 23, 16, 21]`, matching the already-known
speaker-manifest class rather than the target vi-feedback path. The ACDB GET
inputs did carry the intended values (`acdb_id=102`, app type `0x11132`, sample
rate `8000`), so the negative result is not a simple staging failure.

Do not replay this output natively: it lacks the target cal17 record and is not
the missing vi-feedback payload. The run is still operator-valuable negative
evidence and must not count as a fails-twice dead run. The next useful unit is
host-side RE of why the public `send_audio_cal_v5` call normalizes or redirects
to the speaker manifest under own-process context, or a different measurement
point that observes the HAL route context that selects `cal_type=17`.

## Ordered SET Records (metadata only)

| seq | cal_type | data_size | cal_size | mem_handle | arg_sha256 | dmabuf_status | dmabuf_sha256 |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 13 | 40 | 0 | -1 | `df29760a9f24808c2737ef55441a8b124e50fd9a37f3a8a31368575030234d08` | `header-only` | `0000000000000000000000000000000000000000000000000000000000000000` |
| 2 | 9 | 52 | 0 | -1 | `28277c8268c45e2bcbf569dcfd444fc73b4339ce49e05c4d9132d05ea768a812` | `header-only` | `0000000000000000000000000000000000000000000000000000000000000000` |
| 3 | 11 | 48 | 20 | 15 | `595943b37e691137ccfd67548f78cdcaf1e5f4a557bfee04c964e38f73553b23` | `dumped` | `0ad850cc6b82063d0f39a61cd3a308d8a3edddc4b01cd791f98afe05ae11de41` |
| 4 | 12 | 48 | 0 | 17 | `b0b18ecea78f62d4a5642b06b72421dfef8323b0498034afc60c5acd99979704` | `header-only` | `0000000000000000000000000000000000000000000000000000000000000000` |
| 5 | 15 | 36 | 20 | 20 | `bf1f74229499ad08abcd3cd740a645f4c5a6197f6141fb53fa273545ebb8828c` | `dumped` | `0ad850cc6b82063d0f39a61cd3a308d8a3edddc4b01cd791f98afe05ae11de41` |
| 6 | 23 | 48 | 0 | -1 | `1fe8b222033d9281c5bf8703cd119470a33f22821cf75e4e27138aff65c862e1` | `header-only` | `0000000000000000000000000000000000000000000000000000000000000000` |
| 7 | 16 | 44 | 792 | 21 | `1bdfb70bdb4c5a43124f015b5246e5a860e406b1e84e7ba20ac0e3bdb5de857c` | `dumped` | `88877cbb25b7a78b0c2725a9510aacf500b983ad05976fd8fd3d89c89a99c417` |
| 8 | 21 | 80 | 36 | -1 | `ac97288abe06baae56e361d3cda20303902ef65fb13226de83319f7cee13688a` | `no-mem-handle` | `0000000000000000000000000000000000000000000000000000000000000000` |

## Artifact Selection

- helper: `workspace/private/builds/audio/v2728-acdb-vi-feedback-setcal-capture-build-only/bin/a90_acdb_vi_feedback_setcal_capture_exec_linked_v2728`
- helper_sha256: `89c32a607f931c7f019aed77b517ecc5c2c6344c88eab468cd171d3f42dfc911`
- preload: `workspace/private/builds/audio/v2728-acdb-vi-feedback-setcal-capture-build-only/bin/liba90_acdb_vi_feedback_setcal_capture_combined_preload_v2728.so`
- preload_sha256: `1212a2886d4eaaf37a4f9b0152dfab465a247550a5e7f257e751d5ad4edc9735`

## Contract

- stages the V2728 helper/preload through the V2490 Android-good handoff engine;
- forces `A90_ACDB_FAKE_ALLOCATE=1`; real Android kernel SET pass-through is a boundary violation;
- calls `send_audio_cal_v5(102,1,0x11132,8000,0,8000,1)` once;
- pulls `setcal-events.jsonl`, `ioctl-trace-events.jsonl`, helper events, and private raw `setcal-*` files;
- classifies success only after a captured `cal_type=17` vi-feedback SET record.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729.py tests/test_native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729 -v`
- dry-run/live command as recorded by the V2490 engine
- `git diff --check`
