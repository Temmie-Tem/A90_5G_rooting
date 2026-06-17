# NATIVE_INIT V2628 — ACDB AFE topology Gate-2 mapping

Date: 2026-06-17

## Scope

Host-only mapping of the V2627 AFE-topology capture. This does not run
device code, does not replay ACDB, and does not expose private raw buffers.

## Decision

- decision: `v2628-afe-topology-gate2-reject-replay-payload`
- ok: `True`
- replay_ready: `False`
- native_replay_blocked: `True`
- operator_valuable: `True`
- reason: V2627 captured 0x13262 direct size 4 and indirect word 1 only. That is useful evidence but not a cal_type 8/9 replay payload.
- next_gate: `capture actual AUDIO_SET_AFE_CUSTOM_TOPOLOGY/AFE topology SET payload before native replay`

## Inputs

- source_run: `workspace/private/runs/audio/v2627-acdb-afe-topology-20260616-224848`
- source_result: `workspace/private/runs/audio/v2627-acdb-afe-topology-20260616-224848/v2627-result.json`
- artifact_dir: `workspace/private/runs/audio/v2627-acdb-afe-topology-20260616-224848/ownget-device-artifacts`
- source_decision: `v2627-afe-topology-candidate-captured-rollback-pass`
- source_rolled_back: `True`

## Helper Case Results

| case | cmd | step | ret | out_word |
| --- | --- | ---: | ---: | --- |
| `afe-topology-id` | `0x000130d8` | `0` | `0` | `0x1001025d` |
| `afe-topology-cap4` | `0x00013262` | `4` | `0` | `0x00000004` |
| `afe-topology-cap256` | `0x00013262` | `256` | `0` | `0x00000004` |
| `afe-topology-cap4096` | `0x00013262` | `4096` | `0` | `0x00000004` |

## ACDB Tap Records

| seq | cmd | buffer | ret | raw_len | sha256 | words |
| ---: | --- | --- | ---: | ---: | --- | --- |
| `1` | `0x000130d8` | `in` | `0` | `4` | `972b8373b897c65c4f631c6bdf2443d0d817a88f224b54d8e593fdcf32488d60` | `0x0000000f` |
| `1` | `0x000130d8` | `out` | `0` | `4` | `b47b4e39c00eed03a3456247a9387ae3df5f4b34ad7531b421e9c9c99e4aec7e` | `0x1001025d` |
| `2` | `0x00013262` | `in` | `0` | `8` | `0eca935282c0416ab3dc370f3012b3f6a08e1b24e622aee7a603807bc93ee90a` | `0x00000004, 0xffc7abdc` |
| `2` | `0x00013262` | `ind-afe-topology` | `0` | `4` | `67abdd721024f0ff4e0b3f4c2fc13bc5bad42d0b7851d456d88d203d15aaa450` | `0x00000001` |
| `2` | `0x00013262` | `out` | `0` | `4` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` | `0x00000004` |
| `3` | `0x00013262` | `in` | `0` | `8` | `1e02d7259a5551395fb73b61c78a499a8dc8fd696fea150661afc21201736fb9` | `0x00000100, 0xffc7aadc` |
| `3` | `0x00013262` | `ind-afe-topology` | `0` | `4` | `67abdd721024f0ff4e0b3f4c2fc13bc5bad42d0b7851d456d88d203d15aaa450` | `0x00000001` |
| `3` | `0x00013262` | `out` | `0` | `4` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` | `0x00000004` |
| `4` | `0x00013262` | `in` | `0` | `8` | `5a6f97ef382aa5eba0f3ec4bbf7f24b3c954de6e7fa9a599aa0ce56ac3977983` | `0x00001000, 0xffc79adc` |
| `4` | `0x00013262` | `ind-afe-topology` | `0` | `4` | `67abdd721024f0ff4e0b3f4c2fc13bc5bad42d0b7851d456d88d203d15aaa450` | `0x00000001` |
| `4` | `0x00013262` | `out` | `0` | `4` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` | `0x00000004` |

## Mapping Interpretation

- `0x130d8` returns AFE topology ID `0x1001025d` for the probed speaker ACDB ID.
- `0x13262` returned direct output word `0x00000004` for every capacity sweep.
- `0x13262` also exposed an indirect `ind-afe-topology` word `0x00000001` for every sweep.
- The V2627 four-byte indirect record is therefore treated as a topology count/table scalar, not a native replay cal block.
- V2393/V2552 still require real AFE topology cal_type 8/9 material before native SET replay can be unblocked.

## Historical Cross-Check

| run | seq | out_word | sha256 |
| --- | ---: | --- | --- |
| `workspace/private/runs/audio/v2560-acdb-per-device-manifest-20260616-103940` | `1` | `0x00000004` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` |
| `workspace/private/runs/audio/v2566-acdb-toposkip-export-fixed-20260616-114048` | `1` | `0x00000004` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` |
| `workspace/private/runs/audio/v2570-acdb-preinit-perdevice-capture-20260616-121720` | `1` | `0x00000004` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` |

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_afe_topology_gate2_v2628.py tests/test_analyze_audio_acdb_afe_topology_gate2_v2628.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_afe_topology_gate2_v2628 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_afe_topology_gate2_v2628.py --write-report`
- `git diff --check`
