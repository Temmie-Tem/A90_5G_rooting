# NATIVE_INIT V2734 — atomic App Type Config replay live pass

Date: 2026-06-18

## Scope

One self-authorized recoverable-envelope live run of the corrected V2725 ACDB
SET replay, with the V2733 atomic ALSA writer for the global `App Type Config`
control.  The run used the existing V2639 live handoff: flash V2334 audio
candidate, boot ADSP, materialize `/dev/snd`, stage the corrected SET replay,
write the global app-type table, apply the observed speaker route, run one
bounded low-amplitude PCM probe, reset route state, cleanup runtime artifacts,
and rollback to V2321.

No forbidden partitions were touched.  The only persistent device write was the
checked boot-partition flash/rollback.  The audio probe used the existing
1-second, 48 kHz, 16-bit stereo, low-amplitude PCM buffer; there was no smart-amp
gain/boost experimentation beyond the previously observed route controls.

## Result

- decision: `v2734-atomic-app-type-config-pcm-write-pass-rollback-pass`
- runner_decision: `v2639-acdb-setcal-replay-live-pass-before-rollback`
- private_run_dir: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705`
- source_manifest: `workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json`
- global_app_type_writer: `atomic-alsa-elem-write`
- global_app_type_rc: `0`
- replay_start_ok: `True`
- playback_ok: `True`
- rollback: `rolled_back=True`, `rollback_version_ok=True`, `rollback_selftest_fail0=True`
- post_run_device: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`, `selftest fail=0`

## Key Evidence

The V2733 writer resolved the real write-only multi-value control by name and
submitted one full ALSA elem write:

```text
A90_APP_TYPE_CFG_CONTROL numid=3123 count=128 name="App Type Config"
A90_APP_TYPE_CFG_PAYLOAD num_entries=1 entry0=69941:48000:16
A90_APP_TYPE_CFG_WRITE_OK num_entries=1
```

The corrected ACDB replay reached the final SET marker and deallocation cleanup
succeeded.  The bounded PCM probe no longer failed at `pcm_prepare`; it opened
card0/device0, wrote every chunk, and drained:

```text
A90_PCM_PROBE_PCM_OPEN_OK buffer_frames=4096 buffer_bytes=16384
A90_PCM_PROBE_WRITE_OK chunk=0 bytes=16384
...
A90_PCM_PROBE_WRITE_OK chunk=11 bytes=11776
A90_PCM_PROBE_DONE chunks=12 bytes=192000 drain_us=85333
[exit 0]
```

The focused dmesg capture before the PCM probe no longer contains the previous
`msm_pcm_routing_get_app_type_idx: App type not available` / `adm_open:bit_width:0`
failure signature in the captured window; the only focused line is the ADSP
power/clock-ready interrupt.  Because playback succeeded, the runner did not
collect a post-failure dmesg block.

## Interpretation

V2734 confirms the V2732/V2733 hypothesis: V2731 failed because `tinymix` wrote
the write-only `App Type Config` integer control as multiple per-index writes,
not because the tuple `69941:48000:16` was wrong.  Replacing that with one
atomic `SNDRV_CTL_IOCTL_ELEM_WRITE` populated the global `app_type_cfg[]` path
well enough for the native ACDB replay and speaker route to pass PCM prepare,
write all samples, and drain.

This is a functional native-init audio-path pass at the kernel/ALSA/ADSP level.
A human audible confirmation was not independently captured by the runner, so do
not overstate this as a listener-verified sound-quality result.  The old
`pcm_prepare` frontier is closed.

## Private Evidence

- result: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/result.json`
- atomic writer step: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/48_v2733-atomic-app-type-config.txt`
- replay start: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/63_acdb-setcal-replay-start-wait-all-set.txt`
- pre-PCM focused dmesg: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/65_dmesg-focus-after-setcal-replay-before-pcm.txt`
- PCM probe: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/66_tinyplay-low-amplitude-speaker-pilot.txt`
- cleanup: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/67_acdb-setcal-helper-deallocate-check.txt`
- rollback log: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-224705/83_rollback-v2321.txt`

## Validation

- Re-read `GOAL.md`, `AGENTS.md`, `CLAUDE.md`, and the ACDB operator spec before running.
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --v2636-manifest workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json --manifest-path workspace/private/builds/audio/v2734-atomic-appcfg-corrected-core39-live/preflight.json --report docs/reports/NATIVE_INIT_V2734_AUDIO_ATOMIC_APP_TYPE_CONFIG_REPLAY_LIVE_2026-06-18.md --write-report`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live --v2636-manifest workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json --manifest-path workspace/private/builds/audio/v2734-atomic-appcfg-corrected-core39-live/live-manifest.json --report docs/reports/NATIVE_INIT_V2734_AUDIO_ATOMIC_APP_TYPE_CONFIG_REPLAY_LIVE_2026-06-18.md --write-report`
- post-run `python3 workspace/public/src/scripts/revalidation/a90ctl.py --retry-unsafe version`: V2321 / `0.9.285`
- post-run `python3 workspace/public/src/scripts/revalidation/a90ctl.py --retry-unsafe selftest verbose`: `fail=0`
