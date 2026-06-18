# NATIVE_INIT V2702 — libaudcal topology-data handler RE

Date: 2026-06-18

## Scope

Host-only `libaudcal.so` topology-data handler reverse engineering. This unit reads a private vendor library and stores only public-safe metadata: command IDs, handler symbols, table IDs, branch targets, and control-flow interpretation. No device action, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor byte commit occurred.

## Result

- decision: `v2702-libaudcal-ret-minus-12-is-buffer-too-small`
- ok: `True`
- all_lookup_calls_resolve_acdbdata_ioctl: `True`
- all_copy_calls_resolve_memcpy: `True`
- all_handlers_have_buffer_size_gate: `True`
- table_ids_match_expected: `True`
- cal10_ret_minus_12_reclassified: `True`
- recommended_next: `v2703-ownprocess-large-buffer-topology-get-plan`
- native_replay_remains_parked: `True`

## Handler internals

| cal_type | role              | cmd     | handler                                    | table id | lookup                                | copy                                  | size gate                                                                          | V2700 state                    |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10       | ADM_CUST_TOPOLOGY | 0x11394 | AcdbCmdGetAudioCOPPTopologyData@0x00017050 | 0x12e47  | 0x00017098->acdbdata_ioctl@0x00026300 | 0x000170e6->__aeabi_memcpy@0x00026310 | word0_len=0x000170c0, required=0x000170c2, ret-12=0x000170d6, word1_dst=0x000170e4 | ret=-12 absent-ret-minus-12    |
| 14       | ASM_CUST_TOPOLOGY | 0x12e01 | AcdbCmdGetAudioPOPPTopologyData@0x000171a4 | 0x12e48  | 0x000171ec->acdbdata_ioctl@0x00026300 | 0x00017240->__aeabi_memcpy@0x00026310 | word0_len=0x0001721a, required=0x0001721c, ret-12=0x00017230, word1_dst=0x0001723e | ret=0 stale-selected-absent    |
| 24       | AFE_CUST_TOPOLOGY | 0x130da | AcdbCmdGetAfeTopologyData@0x00017734       | 0x130de  | 0x0001777c->acdbdata_ioctl@0x00026300 | 0x000177ca->__aeabi_memcpy@0x00026310 | word0_len=0x000177a4, required=0x000177a6, ret-12=0x000177ba, word1_dst=0x000177c8 | ret=0 aligned-selected-present |

## Interpretation

The three topology-data handlers share the same internal pattern: build a 12-byte ACDB table query on the stack, call `acdbdata_ioctl(3, query, 12, NULL, 0)`, then copy the returned table bytes only if the caller-provided destination size is large enough.

The important correction is cal_type `10` / command `0x11394`. In `AcdbCmdGetAudioCOPPTopologyData`, the `-12` return is the insufficient-destination-buffer branch (`mvn r0, #11`) reached after the handler loads request `word0` as the supplied destination length, loads the returned required size from the ACDB table query, and compares them. V2700 supplied `word0=0x1000`; therefore the previous `absent-ret-minus-12` label is too strong. The evidence now points to `buffer too small` rather than selected ADM topology absence.

The `ret=0` paths for cal_type `14` and `24` mean their returned required sizes fit the supplied buffer in that run. That does not prove the ASM selected topology was correct; V2700 still observed stale/non-selected data for cal_type `14`. It does mean the next capture unit should fix output-buffer geometry before treating `-12` or stale success as database absence.

## Next unit

V2703 should update the own-process ACDB topology GET path to use a size-first or larger indirect output buffer for `0x11394` and re-check `0x12e01` with the same geometry. Acceptance should require `ret==0`, a non-zero output buffer, and private-only raw bytes/SHA for selected cal_type `10` and `14`. Native replay remains parked until byte-exact selected topology SET/GET payloads are recovered.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_libaudcal_topology_data_handlers_v2702.py tests/test_analyze_audio_libaudcal_topology_data_handlers_v2702.py`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_libaudcal_topology_data_handlers_v2702 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_libaudcal_topology_data_handlers_v2702.py --write-report --json`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover -s tests -v`
- `git diff --check`
