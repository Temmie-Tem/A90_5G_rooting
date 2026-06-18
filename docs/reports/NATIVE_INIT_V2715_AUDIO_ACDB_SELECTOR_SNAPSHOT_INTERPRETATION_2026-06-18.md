# NATIVE_INIT V2715 — ACDB selector snapshot interpretation

Date: 2026-06-18

## Scope

Host-only interpretation of V2714 selector deep-snapshot metadata. This unit reads
metadata JSON/report text only: no raw ACDB payload bytes, device action, audio ioctl,
mixer write, PCM probe, or speaker playback occurred.

## Result

- decision: `v2715-selector-snapshot-confirms-lower-hidden-stale-path-no-replay`
- v2714_capture_success: `True`
- v2711_setarg_geometry_closed: `True`
- v2712_existing_payloads_exhausted: `True`
- v2708_replayed_same_payload_family_and_failed: `True`
- selector_block_shape_is_lower_hidden_family: `True`
- contiguous_mem_handles_35_36_37: `True`
- all_payloads_match_replayed_family: `True`
- any_selector_word_contains_selected_topology: `False`
- native_replay_should_remain_parked: `True`
- recommended_next: `route-specific-real-hal-custom-topology-set-capture-or-loader-selector-re`

## Selector Snapshot Rows

| cal_type | role | selected topology | node_word0 | node_block_ptr | block_arg0 | block_arg1 | block_ptr | mem_handle | selected_in_words | payload_len | payload_sha_match |
| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| 24 | `AFE_CUST_TOPOLOGY` | `0x1001025d` | `0xf6b76d45` | `0xf738c570` | `0x00001000` | `0x00000001` | `0xf6c2f000` | 35 | `False` | 1180 | `True` |
| 10 | `ADM_CUST_TOPOLOGY` | `0x10004000` | `0xf6b76d45` | `0xf738c588` | `0x00001000` | `0x00000001` | `0xf6c2e000` | 36 | `False` | 16076 | `True` |
| 14 | `ASM_CUST_TOPOLOGY` | `0x10005000` | `0xf6b76d45` | `0xf738c5a0` | `0x00001000` | `0x00000001` | `0xf6c2d000` | 37 | `False` | 2356 | `True` |

## Interpretation

V2714 captured the missing deep selector state, but it did not create a new replay contract.
The selector blocks for cal_types 24/10/14 are the same lower-hidden family: `arg0=0x1000`,
`arg1=1`, adjacent payload pointers, and contiguous mem_handles 35/36/37. None of the
selector words contains the selected ADM/ASM topology IDs. The payload lengths and SHA-256
values are exactly the family already replayed in V2708, which reached the DSP and failed at
`send_asm_custom_topology` with `ADSP_EBADPARAM`.

Therefore a new native replay using V2714 bytes unchanged is low-value and should remain parked.
The next useful frontier is route-specific Android-good custom-topology SET capture or loader
selector RE that changes the cal10/cal14 selected-payload contract.

## Next Requirements

- Do not run another V2639 replay using V2707/V2714 lower-hidden payloads unchanged.
- Treat V2714 as evidence that the lower hidden path still selects the same stale payload family for cal10/cal14.
- Recover the route-specific Android-good custom-topology SET path for selected ADM/ASM, or RE the selector inputs that should produce selected topology IDs 0x10004000 and 0x10005000.
- If a new replay is built, it must change the cal10/cal14 payload/selector contract, not only restage the same SHA values.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_snapshot_v2715.py tests/test_analyze_audio_acdb_selector_snapshot_v2715.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_selector_snapshot_v2715 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_snapshot_v2715.py --write-report --json`
- `git diff --check`
