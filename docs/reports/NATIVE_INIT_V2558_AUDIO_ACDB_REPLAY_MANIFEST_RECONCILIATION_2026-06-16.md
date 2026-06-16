# V2558 — Audio ACDB replay manifest reconciliation

Date: 2026-06-16

## Decision

`v2558-topology-payload-confirmed-full-cal-replay-still-gated`

V2557 independently reconfirmed the 4916-byte `CORE_CUSTOM_TOPOLOGIES` payload and it matches the stable private V2548 payload.  This is enough to keep the topology replay input pinned, but it is not enough to reopen native full-calibration replay: V2552 already proved topology-only replay reaches `AUDIO_SET_CALIBRATION ok` and still fails `pcm_prepare`, and V2557 crashed immediately after common topology before `acdb_loader_send_audio_cal_v5` reached per-device calibration fetches.

## Scope

- Host-only reconciliation; no device action.
- No `/dev/msm_audio_cal` open or calibration ioctl.
- No mixer write, PCM probe, speaker playback, or flash.
- Raw ACDB bytes stay private; this report records only lengths and SHA-256 digests.

## Evidence Inputs

| Input | Path | Result |
| --- | --- | --- |
| V2557 result JSON | `workspace/private/runs/audio/v2555-acdb-full-manifest-20260616-100802/v2555-result.json` | one valid 4916-byte non-zero topology row |
| Stable topology payload | `workspace/private/inputs/audio/acdb_replay/payloads/core_custom_topologies_v2547.bin` | same length and SHA as V2557 |
| V2552 topology replay report | `docs/reports/NATIVE_INIT_V2552_AUDIO_ACDB_TOPOLOGY_REPLAY_ION_LIVE_HANDOFF_2026-06-16.md` | topology SET ok, PCM prepare still fails |
| V2557 report | `docs/reports/NATIVE_INIT_V2557_AUDIO_ACDB_FULL_MANIFEST_POST_INIT_AUTO_ARM_LIVE_2026-06-16.md` | post-init ACDB tap captured topology, no real SET pass-through |
| V2557 logs | private run artifacts | common topology entered/returned, fatal SIGSEGV observed, no `send_audio_cal_v5` marker |
| `libacdbloader.so` metadata | `workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so` | exports and PLT relocation support future interposition design |

## Topology Payload State

- Length: `4916` bytes.
- SHA-256: `7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89`.
- Zero-buffer discriminator: passed; digest is not the SHA-256 of `4916` zero bytes.
- V2557 raw topology row and the stable V2548 private payload match exactly by SHA-256.

## Replay Boundary

Topology-only native replay is closed as insufficient, not worth repeating unchanged.

V2552 already executed the native topology replay path and reached `AUDIO_SET_CALIBRATION ok cal_type=39`, then still failed at `A90_PCM_PROBE_WRITE_ERROR` / `pcm_prepare`.  The missing inputs remain the per-device calibration payloads needed by the ADSP/Q6 path, especially:

| Cal type | Name | Why still required |
| --- | --- | --- |
| `11` | `ADM_AUDPROC_CAL_TYPE` | Android-good AUDPROC edge and ADM prepare dependency |
| `12` | `ADM_AUDVOL_CAL_TYPE` | Android-good volume calibration edge |
| `15` | `ASM_AUDSTRM_CAL_TYPE` | V2393 showed `q6asm_send_cal` cal block missing |
| `16` | `AFE_COMMON_RX_CAL_TYPE` | V2393 showed RX AFE cal block missing |

V2557 did not pin those payloads.  Its helper reached common topology and then crashed before helper-side `acdb_loader_send_audio_cal_v5` capture.  The `per_device_success_count` value in the V2557 summary is therefore not sufficient replay evidence by itself; the ordered event/log boundary is decisive.

## Host Analysis Artifact

A new host-only analyzer records this reconciliation and writes a private manifest:

- Script: `workspace/public/src/scripts/revalidation/analyze_audio_acdb_replay_manifest_v2558.py`
- Test: `tests/test_analyze_audio_acdb_replay_manifest_v2558.py`
- Private manifest: `workspace/private/builds/audio/v2558-audio-acdb-replay-manifest-reconciliation/manifest.json`

The analyzer validates the V2530 zero-buffer rule, checks both split V2557 log files, and marks full calibration replay blocked until per-device payloads are pinned.

## `libacdbloader` Interposition Note

Host `readelf` confirms `libacdbloader.so` exports:

- `acdb_loader_init_v3`
- `acdb_loader_send_common_custom_topology`
- `acdb_loader_send_audio_cal_v5`

It also has an `R_ARM_JUMP_SLOT` relocation for `acdb_loader_send_common_custom_topology`.  This supports a future host-only design/build unit that safely skips or short-circuits common topology after the already-pinned payload, so the helper can reach `acdb_loader_send_audio_cal_v5` and dump the per-device GET records.  That has not been live-tested and must not be treated as proven.

## Next Unit

Design/build only: a per-device ACDB capture path that avoids repeating the crashing common-topology tail and reaches `acdb_loader_send_audio_cal_v5` under the existing fake-allocate/fake-deallocate/fake-set measurement envelope.

Native full-calibration replay remains blocked until the per-device payload manifest is explicit: command/order, lengths, SHA-256, memory-handle policy, cleanup, and rollback behavior.

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_replay_manifest_v2558.py
PYTHONPATH=tests python3 -m unittest tests.test_analyze_audio_acdb_replay_manifest_v2558 -v
python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_replay_manifest_v2558.py > /tmp/v2558-manifest.json
```

Result: 3 unit tests passed; generated manifest reports `ok=True`, `topology_payload_ready=True`, `full_calibration_replay_ready=False`, `fatal_sigsegv_after_topology=True`, and `send_audio_cal_v5_reached=False`.
