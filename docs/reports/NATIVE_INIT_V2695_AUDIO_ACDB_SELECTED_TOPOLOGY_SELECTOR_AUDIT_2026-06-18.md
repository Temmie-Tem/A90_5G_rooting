# NATIVE_INIT V2695 — ACDB selected-topology selector audit

Date: 2026-06-18

## Scope

Host-only audit after V2693/V2694. This reads existing private V2693 lower pointer-target artifacts and parsed topology payload metadata only. No device action, flash, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, or raw ACDB payload commit occurred.

## Result

- decision: `v2695-selector-audit-pivots-away-from-lower-ptrtarget`
- ok: `True`
- v2693_run: `workspace/private/runs/audio/v2693-acdb-lower-ptrtarget-capture-20260618-171518`
- all_word1_unmapped: `True`
- all_word1_page_aligned: `True`
- afe_selected_topology_present_in_cal24: `True`
- asm_selected_topology_present_in_cal14: `False`
- adm_set_captured: `False`
- lower_ptrtarget_retries_low_value: `True`

## Selector table

| cal_type | role | GET cmd | request words | ptrtarget | ret | SET captured | payload topologies | selected topology | selected present | verdict |
| ---: | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 24 | `AFE_CUST_TOPOLOGY` | `0x000130da` | `0x00001000`, `0xf14f6000` | `ptrtarget_unmapped` | `0` | `True` | `0x1001025c`, `0x1001025e`, `0x1001025d` | `0x1001025d` | `True` | AFE path aligned; selected topology is present |
| 10 | `ADM_CUST_TOPOLOGY` | `0x00011394` | `0x00001000`, `0xf14f5000` | `ptrtarget_unmapped` | `-12` | `False` | none | `0x10004000` | `False` | ADM exact SET still absent; lower GET returns failure |
| 14 | `ASM_CUST_TOPOLOGY` | `0x00012e01` | `0x00001000`, `0xf14bb000` | `ptrtarget_unmapped` | `0` | `True` | `0x1000ffff`, `0x10000018`, `0x10000018`, `0x10000019`, `0x1000001a`, `0x1000001b` | `0x10005000` | `False` | ASM exact SET is stale/misaligned; selected topology absent |

## Legacy real-HAL trace scan

- dirs_seen: `['workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190515', 'workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530', 'workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643']`
- files_scanned: `258`
- setcal_literal_matches: `0`
- cal10_structured_matches: `0`
- cal14_structured_matches: `0`
- cal24_structured_matches: `0`
- cal39_structured_matches: `4`

This structured legacy scan is intentionally limited evidence: it counts explicit result.json `cal_type` fields and ACDB-LOADER `cal_type[...]` log lines only. It shows the archived V2461/V2466 artifacts expose cal39 but no obvious cal10/cal14/cal24 custom-topology SET record; it does not replace byte-exact route-specific SET capture.

## Interpretation

V2693 did not recover a new selector buffer. The second GET word for cal_types 24/10/14 is page-aligned but maps-unreadable in the helper process, and all three pointer-target probes returned `ptrtarget_unmapped`. That makes another same-route maps-based pointer-target retry low-value unless the argument model changes.

The subsystem alignment is now split cleanly:

- AFE is aligned: cal_type 24 contains the selected `0x1001025d` topology and produced a real SET payload.
- ASM is not aligned: cal_type 14 produced a structurally valid 2356-byte payload, but it contains only `0x1000ffff` and `0x10000018..1b`, not selected `0x10005000`. V2694 already showed host SET geometry is not the blocker, and V2689 falsified synthetic selected-topology replacements.
- ADM remains absent: cal_type 10 create/allocate succeeded, but the lower GET returned `-12`, produced an all-zero size output, and no SET payload exists for selected `0x10004000`.

Therefore the current lower own-process route is no longer producing the byte-exact selected ADM/ASM custom topology records needed by the DSP. Native replay should remain parked: replaying existing cal14, defined-only cal14, or another lower-ptrtarget retry would repeat already-refuted evidence.

## Next unit

Do not rerun V2693 or any existing cal14/defined-only replay. The next useful branch is either a route-specific Android-good capture that observes the real HAL custom-topology SET path for selected ADM `0x10004000` and ASM `0x10005000`, or a deeper libacdbloader/ACDB DB selector RE unit that changes the request model rather than dumping the same unmapped `get_arg1` word again. If neither path can recover byte-exact selected cal10/cal14 payloads, close native speaker playback as blocked on DSP topology semantics, not on `/dev/msm_audio_cal` SET delivery.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_selected_topology_selector_v2695.py tests/test_analyze_audio_acdb_selected_topology_selector_v2695.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_selected_topology_selector_v2695 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_selected_topology_selector_v2695.py --write-report`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover -s tests -v`
- `git diff --check`
