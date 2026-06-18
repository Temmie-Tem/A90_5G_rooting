# NATIVE_INIT V2723 — V2722 ACDB replay frontier analysis

Date: 2026-06-18

## Scope

Host-only analysis of the V2722 corrected ACDB SET replay result. This
unit does not run device actions, flash, calibration ioctls, or playback.
It consumes only metadata/dmesg from the private V2722 run and existing
private manifests.

## Decision

- decision: `v2723-old-asm-cleared-new-afe-q6asm-frontier`
- ok: `True`
- source_v2722_run: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-212439`
- V2722 rollback_selftest_fail0: `True`
- SET replay final marker reached: `True`
- old stale ASM custom-topology markers cleared: `True`
- new AFE/q6asm/ADM frontier markers present: `True`
- stale cal_type 10/14/24 in V2721 manifest: `[]`

## Order Audit

- V2721 full replay order: `[39, 20, 20, 13, 9, 11, 12, 15, 23, 16, 21]`
- V2721 per-device order: `[13, 9, 11, 12, 15, 23, 16, 21]`
- V2632 event order from private `setcal_capture` rows: `[13, 9, 11, 12, 15, 23, 16, 21]`
- current GOAL text order claim: `[13, 9, 11, 12, 15, 16, 21, 23]`
- V2721 per-device order matches V2632 events: `True`
- GOAL text order conflicts with V2632 events: `True`

Interpretation: V2721/V2722 followed the on-disk V2632/V2633/V2634 captured
order (`13,9,11,12,15,23,16,21`). The current GOAL prose also contains a
newer order claim (`13,9,11,12,15,16,21,23`) that conflicts with those
artifacts. Do not silently rerun either order as a guess; if the operator
intends the newer order, make a separate host-only reordered manifest first.

## Dmesg Marker Classification

### Old stale path

- send_asm_custom_topology: `False`
- asm_add_custom_topology_cmd: `False`
- subsystem_custom_topology_ebadparam: `False`

### New frontier

- afe_port_start_0x4000: `True`
- afe_cal_ebadparam: `True`
- q6asm_eneedmore: `True`
- q6asm_send_cal_failed: `True`
- adm_open_0x10004000: `True`
- adm_efailed: `True`
- prepare_minus_22: `True`

## Conclusion

V2722 is a useful positive discriminator: removing cal_type 10/14/24
cleared the old per-subsystem ASM custom-topology failure. The remaining
failure is now the stock prepare path: AFE port `0x4000` calibration returns
`ADSP_EBADPARAM`, q6asm reports `ADSP_ENEEDMORE`, and ADM open for topology
`0x10004000` returns `ADSP_EFAILED`.

The next useful unit is not another same-manifest replay and not a return to
cal_type 10/14/24. It should add host-only/live-safe logging around the SET
helper so the next run records each `AUDIO_SET_CALIBRATION` return/errno and
captures dmesg immediately after SET replay but before PCM prepare. That will
separate a kernel SET acceptance problem from a DSP-time payload/ordering
problem.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2722_frontier_v2723.py tests/test_analyze_audio_acdb_v2722_frontier_v2723.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_v2722_frontier_v2723 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2722_frontier_v2723.py --write-report`
- `git diff --check`
