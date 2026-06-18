# NATIVE_INIT V2687 — ACDB topology rejection classifier

Date: 2026-06-18

## Scope

Host-only analysis after V2686. No device action, flash, `/dev/msm_audio_cal` ioctl, mixer write, or PCM probe occurred. Private candidate bytes, if generated, stay under `workspace/private/` and are not committed.

## Result

- decision: `v2687-v2686-topology-rejection-classified`
- source root: `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/techpack/audio`
- manifest: `workspace/private/builds/audio/v2684-acdb-core-topology-replay-deploy-plan/deploy-plan.json`
- module definitions found in stock audio source: `111`
- next action: `generate-defined-only-asm-candidate-before-another-live-replay`

## V2686 failure classifier

| marker | present |
| --- | --- |
| `asm_add_topologies_ebadparam` | `True` |
| `q6asm_opcode_10dbe_error_2` | `True` |
| `pcm_open_enomem` | `True` |
| `afe_excursion_timeout` | `True` |
| `adm_topology_error` | `False` |

Relevant kernel lines:

```text
[  221.773327] I[1:      swapper/1:    0] q6asm_callback: cmd = 0x10dbe returned error = 0x2
[  221.773357] [2:a90_pcm_write_p:  864] send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]
[  221.774076] [2:a90_pcm_write_p:  864] msm_pcm_open: Could not allocate memory
[  221.774091] [2:a90_pcm_write_p:  864] msm-pcm-dsp soc:qcom,msm-pcm: ASoC: can't open platform soc:qcom,msm-pcm: -12
[  221.774105] [2:a90_pcm_write_p:  864]  SM8150 Media1: ASoC: failed to start FE -12
[  223.840115] [2:a90_pcm_write_p:  864] afe_get_sp_rx_tmax_xmax_logging_data: get param port 0x4000 param id[0x102bc]failed -110
[  223.840127] [2:a90_pcm_write_p:  864] afe_get_sp_xt_logging_data Excursion logging fail
```

## Replay payload module classification

| cal_type | role | topologies | undefined modules | Samsung adaptation modules | sha256 |
| --- | --- | --- | --- | --- | --- |
| 10 | `ADM_CUSTOM_TOPOLOGY_FROM_CORE_SELECTED_0x10004000` | 0x10004000 | `0x0001031f`, `0x00010943` | `0x10001f01` | `4fbf08cad1e937fa20c15268e6af2e2e459f872a5daeb53f3dbe9590d3eb9f35` |
| 14 | `ASM_CUSTOM_TOPOLOGY_FROM_CORE_SELECTED_0x10005000` | 0x10005000 | `0x10001f10`, `0x10001f30` | `0x10001f20`, `0x10001fa0`, `0x10001fb0`, `0x10001fc0`, `0x10001fd0`, `0x10001fe0`, `0x10001ff0` | `984b31dd690f51e10697e4356830bbc3bf9a5db944470d1d62accc190d196487` |
| 24 | `AFE_CUSTOM_TOPOLOGY_PAYLOAD` | 0x1001025c, 0x1001025e, 0x1001025d | none | none | `53307305946f1a39e1d57de10c5bb7d65d120ea8f1c90725d0432b684c8e92c4` |

### cal_type 14 selected topology detail

- topology `0x10005000` module_count=`11`
  - modules: `0x00010912`/0x00010000 (AUDPROC_MODULE_ID_MFC; qcom-defined), `0x10001f30`/0x00010000 (unknown; undefined-in-source), `0x00010bfe`/0x00010000 (ASM_MODULE_ID_VOL_CTRL; qcom-defined), `0x10001fb0`/0x00010000 (MODULE_ID_PP_SA_VSP; samsung-adaptation), `0x10001ff0`/0x00010000 (MODULE_ID_PP_SA_MSP; samsung-adaptation), `0x10001fd0`/0x00010000 (MODULE_ID_PP_DOLBY_DAP; samsung-adaptation), `0x10001fa0`/0x00010000 (MODULE_ID_PP_SA; samsung-adaptation), `0x10001fe0`/0x00010000 (MODULE_ID_PP_LRSM; samsung-adaptation), `0x10001fc0`/0x00010000 (MODULE_ID_PP_ADAPTATION_SOUND; samsung-adaptation), `0x10001f20`/0x00010000 (MODULE_ID_PP_SA_UPSCALER_COLOR; samsung-adaptation), `0x10001f10`/0x00010000 (unknown; undefined-in-source)

## Private sanitized candidates

| cal_type | topology | removed | kept | bytes | sha256 | private path |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 0x10004000 | 2 | 4 | 396 | `f8e81e666ee39945a1b4b29f46b1d79f013ad3f944ea7cb19851d2528bf9ab5b` | `workspace/private/builds/audio/v2687-acdb-topology-rejection-candidates/cal10-topology-0x10004000-defined-modules-only.bin` |
| 14 | 0x10005000 | 2 | 9 | 396 | `c02c2226a07d8204bde278c141c1be10b63bd1f33307c443401f287132e788c4` | `workspace/private/builds/audio/v2687-acdb-topology-rejection-candidates/cal14-topology-0x10005000-defined-modules-only.bin` |

## Interpretation

V2686 falsifies SET delivery as the active blocker: every replay entry reached the final SET marker and cleanup completed, but the PCM open path failed when `ASM_CMD_ADD_TOPOLOGIES` returned `ADSP_EBADPARAM`.

The V2684 cal_type `14` payload is mechanically well-formed, but it was forged by moving the selected ASM topology record from the CORE graph into the fixed ASM custom-topology grammar. That live candidate is now falsified: the ADSP rejected it. The important new detail is that the selected `0x10005000` record contains module IDs not defined anywhere in the available stock audio source, notably `0x10001f30` and `0x10001f10`, mixed with Samsung adaptation modules from `sec_adaptation.h`.

The old `cal14-current-unique-plus-0x10005000` branch is dominated: it contains the same selected record that V2686 already caused the ADSP to reject (`True`). Running that branch next would not test a new root cause.

The next bounded unit should therefore avoid another blind V2684-style replay. A safer next host-first branch is to build a new deploy manifest around the private `defined-modules-only` cal_type `14` candidate generated here, or to recover the exact selected ASM custom topology from ACDB with a different request tuple. If the defined-only candidate is used live, keep all V2639 invariants: one-shot, low-amplitude PCM probe, reverse deallocate, dmesg capture, route reset, and rollback to V2321.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2686_topology_rejection_v2687.py tests/test_analyze_audio_acdb_v2686_topology_rejection_v2687.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_v2686_topology_rejection_v2687 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2686_topology_rejection_v2687.py --write-candidates --write-report`
- `git diff --check`
