# NATIVE_INIT V2725 — corrected ACDB replay deploy plan with ioctl-result helper

Date: 2026-06-18

## Scope

Host-only deploy-plan refresh for the corrected ACDB SET replay path. This keeps the
V2721 corrected replay set, but replaces the helper artifact with the V2724 private
helper that emits uniform per-ioctl result markers and pairs with the V2639 pre-PCM
dmesg capture. No device action, flash, calibration ioctl, or playback occurred.

## Decision

- decision: `v2725-corrected-core39-ioctl-result-deploy-plan-ready`
- ok: `True`
- safe_to_run_native_replay: `True`
- replay_blockers: `[]`
- private_manifest: `workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json`
- remote_dir: `/cache/a90-acdb-setcal-replay-v2725`
- helper_sha256: `aa9160278a344b706ef644fb1b27b5af39e58553697bbfc4a39f2635282c7751`
- expected_helper_sha256: `aa9160278a344b706ef644fb1b27b5af39e58553697bbfc4a39f2635282c7751`
- declared_replay_entries: `11`
- helper_entry_count_fits: `True`
- replay_order: `[39, 20, 20, 13, 9, 11, 12, 15, 23, 16, 21]`
- expected_replay_order: `[39, 20, 20, 13, 9, 11, 12, 15, 23, 16, 21]`
- stale_cal_types_present: `[]`
- no_basic_payload_argv: `True`

## Replay Entries

| seq | cal_type | role | kind | payload | ok |
| ---: | ---: | --- | --- | --- | --- |
| 0 | 39 | `CORE_CUSTOM_TOPOLOGIES_BYTE_EXACT_SET` | `exact-set` | `True` | `True` |
| 1 | 20 | `AFE_FB_SPKR_PROT_HEADER_REAL_HAL_1` | `exact-set` | `False` | `True` |
| 2 | 20 | `AFE_FB_SPKR_PROT_HEADER_REAL_HAL_2` | `exact-set` | `False` | `True` |
| 3 | 13 | `APP_META_HEADER` | `exact-set` | `False` | `True` |
| 4 | 9 | `AFE_TOPOLOGY_HEADER` | `exact-set` | `False` | `True` |
| 5 | 11 | `AUDPROC_COMMON_PAYLOAD` | `exact-set` | `True` | `True` |
| 6 | 12 | `VOL_HEADER_NO_PAYLOAD` | `exact-set` | `False` | `True` |
| 7 | 15 | `ASM_STREAM_PAYLOAD` | `exact-set` | `True` | `True` |
| 8 | 23 | `AFE_TOPOLOGY_ID_HEADER` | `exact-set` | `False` | `True` |
| 9 | 16 | `AFE_COMMON_PAYLOAD` | `exact-set` | `True` | `True` |
| 10 | 21 | `SPEAKER_VI_HEADER` | `exact-set` | `False` | `True` |

## Interpretation

- The deploy set remains the corrected V2721/V2722 set: cal39 + cal20 +
  per-device records, with no stale 10/14/24 and no legacy `--basic-payload`.
- The helper artifact is the V2724 private build, so the next live run can
  classify every calibration ioctl by `A90_ACDB_SETCAL_IOCTL_RESULT`.
- The paired V2639 runner now captures `post_set_dmesg` before PCM prepare, so
  future live evidence can separate SET ioctl acceptance from DSP prepare failure.

## Validation

- Re-read `GOAL.md`, `AGENTS.md`, `CLAUDE.md`, and the ACDB operator spec.
- Generated private V2725 deploy manifest with V2724 helper SHA validation.
- Verified corrected replay order and stale cal_type exclusion through focused tests.
- `py_compile`, focused unittest, dry-run/write-report, and `git diff --check` passed.
