# NATIVE_INIT V2686 — ACDB core-topology replay live result

Date: 2026-06-18

## Scope

Ran one rollbackable native live replay using the V2684 core-derived ACDB manifest
through the V2639 SET-cal replay handoff. The unit stayed inside the audio
measurement/replay envelope: boot-only flash to the V2334 audio node image,
route apply, exact manifest SET sequence, one low-amplitude PCM probe,
reverse deallocate/reset cleanup, and checked rollback to V2321.

## Decision

- decision: `v2686-core-topology-setcal-succeeded-pcm-open-enomem`
- previous runner decision: `v2639-acdb-setcal-replay-live-blocked`
- blocker type: `SpeakerPilotBlocked`
- blocker: PCM open failed for `/dev/snd/pcmC0D0p` with `Cannot allocate memory`
- rollback: `v2321-usb-clean-identity-rodata` restored and verified
- post-rollback health: `version=0.9.285`, `selftest fail=0`

## ACDB Replay Result

- manifest source: `workspace/private/builds/audio/v2684-acdb-core-topology-replay-deploy-plan/deploy-plan.json`
- replay order: `39, 10, 14, 24, 13, 9, 11, 12, 15, 23, 16, 21`
- final SET index: `11`
- generated topology payloads:
  - cal_type `10`: ADM topology `0x10004000`
  - cal_type `14`: ASM topology `0x10005000`
- retained exact payloads: cal_types `39, 24, 11, 15, 16`
- SET completion marker: `A90_SETCAL_REPLAY_ALL_SET_OK pid=862 final_index=11`
- cleanup marker: `A90_ACDB_SETCAL_REPLAY_DONE rc=0`
- observed dealloc indices: `0, 1, 2, 3, 6, 8, 10`
- route apply: all mixer route apply steps returned success
- route reset: all reset steps returned success; reset verification had no mismatches

## PCM Probe Result

The bounded PCM probe did not reach playback. It failed while opening the PCM
node, before any useful speaker output validation:

```text
A90_PCM_PROBE_START version=V2386 card=0 device=0 channels=2 rate=48000 bits=16 data_bytes=192000 period_size=1024 period_count=4
A90_PCM_PROBE_PCM_OPEN_ERROR card=0 device=0 pcm_error="cannot open device 0 for card 0: Cannot allocate memory"
pcm_hw_open: cannot open device '/dev/snd/pcmC0D0p'
ERR exit=20
```

Kernel evidence captured before route reset shows the failure is no longer an
ACDB SET delivery failure. The DSP rejected the custom topology during PCM open:

```text
q6asm_callback: cmd = 0x10dbe returned error = 0x2
send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]
msm_pcm_open: Could not allocate memory
msm-pcm-dsp soc:qcom,msm-pcm: ASoC: can't open platform soc:qcom,msm-pcm: -12
SM8150 Media1: ASoC: failed to start FE -12
```

Additional post-failure logging also showed AFE excursion logging timeout on
port `0x4000`, but that appeared after the PCM open failure path:

```text
afe_apr_send_pkt: request timedout
afe_get_sp_rx_tmax_xmax_logging_data: get param port 0x4000 param id[0x102bc]failed -110
afe_get_sp_xt_logging_data Excursion logging fail
```

## Interpretation

V2686 proves the V2684/V2685 path is operational through the native SET replay
layer: the helper accepted all manifest entries, completed the final SET, and
cleanly deallocated all payload-backed calibration blocks. The remaining blocker
has shifted to the DSP/PCM-open side of the speaker path. The strongest current
signal is `send_asm_custom_topology: ADSP_EBADPARAM`, meaning the generated or
selected ASM/ADM topology payload is still not accepted by the ADSP for this
route/app-type combination.

This is progress relative to earlier ACDB runs: the failure is now past manifest
acceptance and SET delivery. The next unit should be host/source-first and should
not repeat blind SET replay. It should classify why the ADSP rejects the custom
topology at PCM open: topology IDs `0x10004000`/`0x10005000`, q6asm opcode
`0x10dbe`, route app-type, payload geometry, or missing companion calibration.

## Rollback And Health

- rollback image: `boot_linux_v2321_usb_clean_identity_rodata.img`
- rollback SHA-256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- rollback flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- rollback flash result: success
- rollback version check: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- rollback selftest: `pass=11 warn=1 fail=0`
- current live recheck after report: bridge up, `status` OK, `selftest verbose` fail=0

## Validation

- Live command: `native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live --v2636-manifest ... --manifest-path ... --write-report`
- Private run directory: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-160730`
- Private live manifest: `workspace/private/builds/audio/v2686-acdb-core-topology-live-replay/live-manifest.json`
- Current post-rollback check: `a90ctl.py version`, `a90ctl.py status`, `a90ctl.py selftest verbose`
- Commit-time check: `git diff --check`
