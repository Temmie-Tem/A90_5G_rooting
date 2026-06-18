# NATIVE_INIT V2698 — ACDB route-selector frontier audit

Date: 2026-06-18

## Scope

Host-only audit. This consolidates V2695-V2697 and scans metadata from private stock audio binaries without emitting proprietary bytes. No device action, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor binary commit occurred.

## Result

- decision: `v2698-route-selector-frontier-needs-new-selector-model`
- ok: `True`
- recommended_next: `loader-selector-re-or-new-real-hal-set-capture`
- park_native_replay: `True`
- lib_has_avcs_custom_topo_cmd: `True`

## Closed branch matrix

| branch                          | closed | meaning                                                                        |
| --- | --- | --- |
| lower_ptrtarget_retry           | True   | V2695: same lower pointer-target model produced stale ASM and no ADM SET       |
| db_staging_simple_parse         | True   | V2697: firmware /etc/acdbdata staging has no simple parseable selected records |
| synthetic_core_replay           | True   | V2689: core-derived selected-topology replay failed DSP semantics              |
| set_geometry                    | True   | V2694: host SET geometry is not the blocker                                    |
| cross_process_or_in_hal_capture | True   | operator spec: cross-process dmabuf and in-HAL LD_PRELOAD are closed           |

## Binary metadata scan

### libacdbloader

- path: `workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so`
- exists: `True`
- size: `92500`
- sha256: `25ae25afda6f52fc75d9b72e7f9df22094c7e3b243efb7257654ec9445bcd0a1`

| constant                     | value      | count | first offsets |
| --- | --- | --- | --- |
| selected_adm_0x10004000      | 0x10004000 | 1     | 0x1030        |
| selected_asm_0x10005000      | 0x10005000 | 0     | none          |
| selected_afe_0x1001025d      | 0x1001025d | 0     | none          |
| speaker_app_0x11135          | 0x00011135 | 0     | none          |
| adm_get_cmd_0x11394          | 0x00011394 | 0     | none          |
| asm_get_cmd_0x12e01          | 0x00012e01 | 0     | none          |
| afe_get_cmd_0x130da          | 0x000130da | 0     | none          |
| afe_get_cmd_alt_0x130dc      | 0x000130dc | 0     | none          |
| avcs_custom_topo_cmd_0x13296 | 0x00013296 | 1     | 0x6f48        |

| symbol                                  | value    | size | defined |
| --- | --- | --- | --- |
| acdb_ioctl                              | 00000000 | 0    | False   |
| acdb_loader_store_set_audio_cal         | 0000e2d5 | 360  | True    |
| acdb_loader_set_audio_cal_v2            | 0000e68d | 136  | True    |
| acdb_loader_send_audio_cal_v5           | 00009d31 | 876  | True    |
| acdb_loader_send_common_custom_topology | 00008cf1 | 2620 | True    |
| acdb_loader_adsp_set_audio_cal          | 0000e43d | 592  | True    |

### audio_primary

- path: `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/hw/audio.primary.msmnile.so`
- exists: `True`
- size: `733636`
- sha256: `b4609f8b61b757053a9804fa0c2b2cb0f60e09810271fc38dc7b7959059329eb`

| constant                     | value      | count | first offsets |
| --- | --- | --- | --- |
| selected_adm_0x10004000      | 0x10004000 | 0     | none          |
| selected_asm_0x10005000      | 0x10005000 | 0     | none          |
| selected_afe_0x1001025d      | 0x1001025d | 0     | none          |
| speaker_app_0x11135          | 0x00011135 | 0     | none          |
| adm_get_cmd_0x11394          | 0x00011394 | 0     | none          |
| asm_get_cmd_0x12e01          | 0x00012e01 | 0     | none          |
| afe_get_cmd_0x130da          | 0x000130da | 0     | none          |
| afe_get_cmd_alt_0x130dc      | 0x000130dc | 0     | none          |
| avcs_custom_topo_cmd_0x13296 | 0x00013296 | 0     | none          |

| symbol                          | value    | size | defined |
| --- | --- | --- | --- |
| platform_send_audio_calibration | 0005df34 | 2092 | True    |
| platform_get_audio_cal          | 0006b4dc | 120  | True    |
| platform_send_audio_cal         | 0006b3f8 | 228  | True    |
| platform_store_audio_cal        | 0006b554 | 44   | True    |

## Interpretation

The current evidence does not support another same-route lower GET/pointer-target retry. AFE cal_type `24` is aligned, but exact lower ASM cal_type `14` is stale and exact ADM cal_type `10` is absent. The staged firmware DB does not expose the selected ADM/ASM/AFE records as simple parseable `.acdb` records, and the synthetic core-derived replay path has already failed DSP-side semantics.

The private binary metadata scan reinforces that this is a runtime selector problem, not a plain hardcoded route tuple: `libacdbloader.so` contains the AVCS custom topology command `0x13296`, but the stock loader/HAL metadata does not contain a complete selected route constant set for selected ADM `0x10004000`, selected ASM `0x10005000`, selected AFE `0x1001025d`, and app type `0x11135`. The lone selected-ADM literal in `libacdbloader.so`, by itself, is not enough to define the missing selected cal_type `10`/`14` SET payloads.

Therefore native replay remains parked. The next useful work must either change the own-process selector model through deeper `libacdbloader`/ACDB runtime RE, or invent a new recoverable route-specific Android-good capture that observes the real HAL custom-topology SET path without reopening the closed cross-process dmabuf or in-HAL `LD_PRELOAD` lines.

## Next unit

Design a V2699 loader-selector RE unit around the `acdb_loader_send_common_custom_topology` / custom-topology lower blocks and the HAL `platform_send_audio_calibration` call graph. Acceptance should be a concrete new request model for cal_type `10` and `14`, or a documented close decision if no safe route-specific raw SET capture remains. Do not run another native replay until byte-exact selected cal_type `10` and selected cal_type `14` payloads are recovered.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_route_selector_frontier_v2698.py tests/test_analyze_audio_acdb_route_selector_frontier_v2698.py`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_route_selector_frontier_v2698 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_route_selector_frontier_v2698.py --write-report`
- `git diff --check`
