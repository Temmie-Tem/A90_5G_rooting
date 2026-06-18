# NATIVE_INIT V2731 — global App Type Config replay live discriminator

Date: 2026-06-18

## Scope

One self-authorized recoverable-envelope live run of the corrected ACDB SET
replay with the V2730 global `App Type Config` gate enabled. The run used the
existing V2639 checked handoff: flash V2334 audio candidate, boot ADSP,
materialize `/dev/snd`, stage the corrected replay manifest, write mixer gates,
run the exact SET replay, attempt one bounded low-amplitude PCM probe, reset the
route, cleanup runtime artifacts, and rollback to V2321.

No forbidden partitions were touched. The ACDB SET replay used the existing
captured SET bytes and bounded cleanup path. No smart-amp gain/boost change was
added.

## Result

- decision: `v2639-acdb-setcal-replay-live-blocked`
- effective run id: `V2731` using the V2639 live runner with V2730 additions
- out_dir: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-221908`
- global_app_type_config_rc: `0`
- replay_start_ok: `True`
- playback_ok: `False`
- rollback: `rolled_back=True`, `rollback_version_ok=True`, `rollback_selftest_fail0=True`
- current post-run device: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`, `selftest fail=0`

## Key Evidence

The new global mixer write executed successfully:

```text
cmdv1x ... tinymix -D 0 "App Type Config" 1 69941 48000 16
[exit 0]
```

The focused post-failure dmesg still shows the same app-type lookup miss and
bit-width zero:

```text
q6asm_callback: cmd = 0x10da1 returned error = 0x12
q6asm_set_pp_params: DSP returned error[ADSP_ENEEDMORE]
q6asm_send_cal: audio audstrm cal send failed
msm_pcm_routing_get_app_type_idx: App type not available, fallback to default
adm_open:port 0x4000 path:1 rate:48000 mode:1 perf_mode:0,topo_id 0x10004000
adm_open:bit_width:0 app_type:0x11135 acdb_id:15
adm_open: DSP returned error[ADSP_EFAILED]
```

The focused pre-PCM dmesg captured only the ADSP power/clock ready line and no
q6core/topology-registration lines:

```text
subsys-pil-tz 17300000.qcom,lpass: adsp: Power/Clock ready interrupt received
```

## Interpretation

V2731 falsifies the simple hypothesis that writing `App Type Config` as
`1 69941 48000 16` is sufficient to populate the kernel `app_type_cfg[]` table.
The write returns success, but `msm_pcm_routing_get_app_type_idx()` still cannot
find app type `0x11135`, and `adm_open` still consumes `bit_width:0`.

This leaves three concrete possibilities for the next unit:

1. the `App Type Config` put layout is not `[num, app_type, sample_rate, bit_width]`
   on this Samsung/QC build;
2. the control requires a different unit or field order, for example the
   Android/HAL-visible bit-width value `2` rather than raw `16`;
3. the write path accepted the userspace command but did not update the runtime
   table used by this PCM path because another route/usecase/session field is
   required.

The corrected ACDB SET replay itself still reaches the SET-complete marker, and
the q6core focused capture remains useful: there are no observable q6core
registration lines in the pre-PCM focus window. Do not repeat V2731 unchanged.
The next useful unit is host-side RE / source-search of the exact
`msm_routing_put_app_type_cfg_control` parser and/or Android log evidence for
`set_app_type_cfg` field ordering, then one bounded live discriminator with the
corrected tuple.

## Private Evidence

- result: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-221908/result.json`
- global write: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-221908/44_v2730-global-app-type-config.txt`
- post-set focus dmesg: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-221908/61_dmesg-focus-after-setcal-replay-before-pcm.txt`
- post-failure focus dmesg: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-221908/64_dmesg-focus-after-setcal-playback-failure-before-reset.txt`

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py tests/test_native_audio_acdb_setcal_replay_live_handoff_v2639.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_setcal_replay_live_handoff_v2639 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --write-report --report docs/reports/NATIVE_INIT_V2730_AUDIO_ACDB_GLOBAL_APP_TYPE_CONFIG_REPLAY_SUPPORT_2026-06-18.md --manifest-path workspace/private/builds/audio/v2730-global-app-type-config-replay-support/manifest.json`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live --manifest-path workspace/private/builds/audio/v2731-global-app-type-config-replay-live/manifest.json --report docs/reports/NATIVE_INIT_V2731_AUDIO_ACDB_GLOBAL_APP_TYPE_CONFIG_REPLAY_LIVE_2026-06-18.md --write-report`
- post-run `a90ctl version`: V2321
- post-run `a90ctl selftest verbose`: `fail=0`
- `git diff --check`
