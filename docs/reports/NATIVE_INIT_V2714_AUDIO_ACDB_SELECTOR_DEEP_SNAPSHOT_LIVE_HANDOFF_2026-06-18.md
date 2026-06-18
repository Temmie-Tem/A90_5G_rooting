# NATIVE_INIT V2714 — ACDB selector deep-snapshot live handoff

Date: 2026-06-18

## Scope

Android own-process ACDB lower custom-topology GET capture using the V2490 checked Android
boot/stage/pull/rollback engine and the V2713 helper/preload artifacts. This is
measurement-only: no native replay, no speaker write, no real kernel SET from the V2713
preinit path, and raw buffers remain under `workspace/private`.

## Result

- decision: `v2714-selector-deep-snapshot-lower-custom-topology-captured-rollback-pass`
- ok: `True`
- rolled_back: `True`
- counts_toward_fails_twice: `False`
- operator_valuable: `True`
- partial_success: `False`
- success: `True`
- out_dir: `workspace/private/runs/audio/v2714-acdb-selector-deep-snapshot-20260618-202450`
- rollback_health: `v2321 version verified; selftest fail=0`
- classification: `v2714-selector-deep-snapshot-lower-custom-topology-captured`
- selector_event_count: `3`
- selector_success_by_cal_type: `{24: True, 10: True, 14: True}`
- snapshot_cal_types: `[10, 14, 24]`
- missing_snapshot_cal_types: `[]`
- lower_stage_count: `21`
- lower_stages: `['entered_common_topology_hook', 'skip_real_common_topology', 'loader_base_resolved', 'patched_initialized_flag', 'patch_initialized_flag_return', 'armed_inside_common_hook', 'create_cal_node_return', 'allocate_cal_block_return', 'v2703_large_get_request', 'v2703_large_get_return', 'create_cal_node_return', 'allocate_cal_block_return', 'v2703_large_get_request', 'v2703_large_get_return', 'create_cal_node_return', 'allocate_cal_block_return', 'v2703_large_get_request', 'v2703_large_get_return', 'lower_hidden_sequence_complete', 'lower_hidden_nodes_return_inside_common_hook', 'exit_after_inhook_lower_hidden_nodes']`
- lower_codes_by_stage: `{'entered_common_topology_hook': [0], 'skip_real_common_topology': [0], 'loader_base_resolved': [0], 'patched_initialized_flag': [0], 'patch_initialized_flag_return': [0], 'armed_inside_common_hook': [0], 'create_cal_node_return': [0, 0, 0], 'allocate_cal_block_return': [0, 0, 0], 'v2703_large_get_request': [0, 0, 0], 'v2703_large_get_return': [0, 0, 0], 'lower_hidden_sequence_complete': [0], 'lower_hidden_nodes_return_inside_common_hook': [0], 'exit_after_inhook_lower_hidden_nodes': [0]}`
- lower_values_by_stage: `{'entered_common_topology_hook': [0], 'skip_real_common_topology': [0], 'loader_base_resolved': [4139151360], 'patched_initialized_flag': [4139252380], 'patch_initialized_flag_return': [0], 'armed_inside_common_hook': [0], 'create_cal_node_return': [4149416976, 4149416992, 4149417008], 'allocate_cal_block_return': [4147692912, 4147692936, 4147692960], 'v2703_large_get_request': [65536, 65536, 65536], 'v2703_large_get_return': [1180, 16076, 2356], 'lower_hidden_sequence_complete': [0], 'lower_hidden_nodes_return_inside_common_hook': [0], 'exit_after_inhook_lower_hidden_nodes': [0]}`
- lower_cal_types_by_stage: `{'entered_common_topology_hook': [0], 'skip_real_common_topology': [0], 'loader_base_resolved': [0], 'patched_initialized_flag': [0], 'patch_initialized_flag_return': [0], 'armed_inside_common_hook': [0], 'create_cal_node_return': [24, 10, 14], 'allocate_cal_block_return': [24, 10, 14], 'v2703_large_get_request': [24, 10, 14], 'v2703_large_get_return': [24, 10, 14], 'lower_hidden_sequence_complete': [0], 'lower_hidden_nodes_return_inside_common_hook': [0], 'exit_after_inhook_lower_hidden_nodes': [0]}`
- acdbtap_row_count: `9`
- target_seen_count: `3`
- target_success_by_cal_type: `{24: True, 10: True, 14: True}`
- captured_cal_types: `[10, 14, 24]`
- missing_cal_types: `[]`
- real_audio_set_pass_through_count: `0`
- selector_events_path: `workspace/private/runs/audio/v2714-acdb-selector-deep-snapshot-20260618-202450/ownget-device-artifacts/acdb-v2713-selector-deep-snapshot-events.jsonl`

## Selector Deep Snapshots

| cal_type | node_word_count | block_word_count | depth_ok | node_words | block_words |
| ---: | ---: | ---: | --- | --- | --- |
| 24 | 16 | 32 | `True` | `['0xf6b76d45', '0x00000000', '0xf738c570', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` | `['0x00001000', '0x00000001', '0xf6c2f000', '0x00000023', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` |
| 10 | 16 | 32 | `True` | `['0xf6b76d45', '0x00000000', '0xf738c588', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` | `['0x00001000', '0x00000001', '0xf6c2e000', '0x00000024', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` |
| 14 | 16 | 32 | `True` | `['0xf6b76d45', '0x00000000', '0xf738c5a0', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` | `['0x00001000', '0x00000001', '0xf6c2d000', '0x00000025', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000']` |

## Target Rows (metadata only)

| cal_type | seq | cmd | ret | out_len | buffer | raw_ok | sha256 |
| ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| 24 | 1 | `0x000130da` | 0 | 1180 | `ind-lower-afe-custom-topology` | `True` | `53307305946f1a39e1d57de10c5bb7d65d120ea8f1c90725d0432b684c8e92c4` |
| 10 | 2 | `0x00011394` | 0 | 16076 | `ind-lower-adm-custom-topology` | `True` | `fef3ed8df47486a54e625d632961f93366807f70413b47e08b35e7d00216ca36` |
| 14 | 3 | `0x00012e01` | 0 | 2356 | `ind-lower-asm-custom-topology` | `True` | `bc03e4be2dc4667ebfaf14b27ecc088f28fb23f784b352c14f0524963f7b7c98` |

Raw buffers are private. Public output reports only command, length, return code, SHA-256,
and selector word metadata. A success classification requires cal_types `10`, `14`, and
`24` to each have a bounded 16/32-word selector snapshot and a ret==0 non-zero indirect
raw buffer with matching length and SHA.

## Artifact Selection

- helper: `workspace/private/builds/audio/v2713-acdb-selector-deep-snapshot-build-only/bin/a90_acdb_selector_deep_snapshot_exec_linked_v2713`
- helper_sha256: `c5dd12cc28e7ab991f4c7a0e3439b848fa540accdda06b2711d9a9f0c6329106`
- preload: `workspace/private/builds/audio/v2713-acdb-selector-deep-snapshot-build-only/bin/liba90_acdb_selector_deep_snapshot_combined_preload_v2713.so`
- preload_sha256: `29549d375094d36eb2f3e661c4834ec45eb4b8f8c1a384a999822bd182446101`

## Contract

- stages the V2713 helper/preload through the V2490 Android-good handoff engine;
- forces `A90_ACDB_FAKE_ALLOCATE=1`; the V2713 preinit path does not call real or fake SET;
- uses the common-topology hook to patch initialized state, arm capture, run lower hidden nodes,
  and issue selector-deep-snapshot GET commands for 24/10/14;
- captures lower ADM/ASM/AFE custom topology indirect outputs through `acdbtap`;
- pulls `/data/local/tmp/a90-acdb-ownget/` privately; and
- keeps native replay blocked until selected raw bytes are recovered and reviewed.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py tests/test_native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_selector_deep_snapshot_live_handoff_v2714 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py --dry-run --write-report`
- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py --run-live --write-report`
- if live run is present, post-live rollback must verify `a90ctl.py version` reports V2321 and
  `a90ctl.py selftest verbose` reports `fail=0`
- `git diff --check`
