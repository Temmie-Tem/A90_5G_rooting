# NATIVE_INIT V2614 — ACDB meta-list indirect-layout live capture

Date: 2026-06-16

## Scope

Rollbackable Android-good own-process ACDB measurement run using the V2613 helper/preload.
Raw ACDB bytes were pulled only under `workspace/private/`; this report records metadata only.
No native replay, real audio calibration `SET`, speaker write, mixer/PCM playback, or partition
write outside the checked Android-handoff/V2321 rollback path was performed.

## Decision

- decision: `v2614-perdevice-indirect-payloads-captured-no-4916-rollback-pass`
- runner_decision: `v2490-acdbtap-full-outbuf-set-no-4916-before-helper-exit-before-rollback-rollback-pass`
- ok: `True`
- partial_success: `True`
- counts_toward_fails_twice: `False`
- target_4916_success: `False`
- rolled_back: `True`
- rollback_target: `v2321-usb-clean-identity-rodata`
- final_selftest: `fail=0`
- private_run_dir: `workspace/private/runs/audio/v2614-acdb-meta-list-indirect-layout-live-20260616-192454`

## Artifact Inputs

- helper: `workspace/private/builds/audio/v2613-acdb-meta-list-indirect-layout-capture-build-only/bin/a90_acdb_meta_list_indirect_layout_capture_exec_linked_v2613`
- helper_sha256: `e9c06a6b8228cbfd3aea833ba390b3d1731f2f9c5eea360b19454dc110ecf6f5`
- combined_preload: `workspace/private/builds/audio/v2613-acdb-meta-list-indirect-layout-capture-build-only/bin/liba90_acdb_meta_list_indirect_layout_capture_combined_preload_v2613.so`
- combined_preload_sha256: `cba96cb0e9f5ca292ecdf6e39239df8e915680e2688b5f2a56aa284125f7f8db`
- fake_audio_cal_allocate: `A90_ACDB_FAKE_ALLOCATE=1`

## Helper Path Evidence

The helper reached the intended post-init path without crash or timeout:

- `meta_list_head_ready`: `0`
- `before_init_v3`: `0`
- `init_v3_return`: `0`
- `before_arm_capture`: `0`
- `arm_capture_return`: `0`
- `before_send_audio_cal_v5`: `0`
- `send_audio_cal_v5_return`: `0`

The V2608 preinit hook also stayed in the safe no-send mode:

- `entered_common_topology_hook`
- `skip_real_common_topology`
- `patched_initialized_flag_addr`
- `patch_initialized_flag_return`
- `return_to_init_v3_no_arm_no_send`

## Captured ACDB Records

The V2613 direct out-buffer classifier still found no valid `4916` topology payload in this run.
That is a partial success, not a failure, because the requested per-device indirect buffers were
captured and preserved privately.

| command | buffer | bytes | ret | all_zero | sha256 |
| --- | --- | ---: | --- | --- | --- |
| `0x00013265` | `ind-ap-common` | 18084 | `0x00000000` | `False` | `00c2399f9b763cf12d8b41d973be78776bc5de2fdf386e778d85e11860f3be0d` |
| `0x00013269` | `ind-ap-stream` | 28 | `0x00000000` | `False` | `713205fee55c5504a97496b2395ef4f30dac69d785582ed6a520da9ce4349d71` |
| `0x0001326f` | `ind-afe-common` | 1560 | `0x00000000` | `False` | `b76ceb8320f1028f1d8738438112e17b8d00a8658fb16195d721c7909e7faf72` |

Additional context:

- `acdbtap_row_count`: `27`
- `acdbtap_raw_file_count`: `27`
- `acdbtap_call_row_count`: `24`
- gain/VOL commands `0x1326d` and `0x1326e` returned `0xffffffed` with zero direct size, so no valid `ind-ap-gain` payload was dumped for this tuple.
- direct `out_buf` records remained four-byte size/status words; the useful bytes were in command-specific indirect input pointers.

## Interpretation

V2614 confirms the V2613 hypothesis: for the successful per-device GET commands, `acdb_ioctl`
returns only a four-byte direct output word while the real calibration payload is written into
an indirect buffer described by the input request struct. The captured non-zero payloads cover:

- AUDPROC common table, matching the `AUDIO_SET_AUDPROC_CAL` / cal_type `11` path.
- AUDPROC stream table, matching the stream cal payload path.
- AFE common table, matching the `AUDIO_SET_AFE_CAL` / cal_type `16` path.

This does not yet produce the 4916-byte topology payload, and it does not by itself replay
calibration into native init. It does provide the first valid non-zero own-process per-device
payload set needed for the operator replay-manifest assembly step.

## Rollback / Cleanup

- Android-good handoff used the checked helper path.
- `/data/local/tmp/a90-acdb-ownget` and `/data/local/tmp/a90-acdb-tap` cleanup commands returned OK.
- Android rebooted to recovery and V2321 was flashed through `native_init_flash.py`.
- Final native health check reported `selftest: pass=11 warn=1 fail=0` and version `0.9.285`.

## Validation

- V2613 private helper/preload SHA-256 verification in runner plan.
- Live artifact pull from `/data/local/tmp/a90-acdb-ownget` succeeded.
- Private raw files hashed and classified as `ret==0`, non-all-zero indirect payloads.
- Checked rollback to V2321 completed with final `selftest fail=0`.
- `git diff --check` before commit.

## Next Unit

Hand the ordered metadata plus private raw files to the replay-manifest assembly step. The next
safe host-only unit is to generate a private manifest candidate from the V2614 indirect payload
set without issuing native calibration `SET`. Any native replay remains blocked until the manifest
pins command ordering, cal_type mapping, mem_handle policy, and cleanup semantics.
