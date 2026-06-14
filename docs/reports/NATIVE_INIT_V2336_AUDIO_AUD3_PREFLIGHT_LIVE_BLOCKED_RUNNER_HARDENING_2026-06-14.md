# Native Init V2336 Audio AUD-3 Preflight Live Blocked + Runner Hardening

## Summary

- Cycle: `V2336`
- Track: audio AUD-3 preflight live attempt + runner hardening.
- Decision: `aud3-preflight-blocked-before-audio-actions-control-channel-desync`
- Result: BLOCKED before ADSP/audio commands.
- Operator gate: exact AUD-3-preflight approval phrase received.
- Candidate flashed: `A90 Linux init 0.9.292 (v2334-audio-snd-nodes-preflight)`.
- Candidate SHA256: `53b1130cd912ca4019a3d76835eb721804bae0460b920eb7fdfad5509a2dfcac`.
- Rollback target: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence directory: `workspace/private/runs/audio/v2335-snd-nodes-preflight-20260614-223301`.

## Live Result

The approved live run did not reach the AUD-3-preflight audio window.

Completed safely:

1. Verified resident V2321 through `native_init_flash.py --verify-only` and `selftest fail=0`.
2. Flashed V2334 through the checked `native_init_flash.py` path with pinned SHA256.
3. V2334 booted and passed the flash helper's post-boot `selftest` verification.
4. `candidate-version` returned `0.9.292 (v2334-audio-snd-nodes-preflight)`.
5. `candidate-status` returned successfully.

Blocked point:

- `candidate-selftest` failed at the host protocol layer after 120 seconds.
- `a90ctl.py` raised `A90P1 END marker not found`.
- The captured tail showed serial-contention/desynchronization text ending with `a90:/# lfteATATATATAT`.
- No `audio adsp-status`, `audio snd-status`, `audio adsp-boot-once`, or `audio snd-materialize-once` command ran.

Rollback:

- Automatic rollback to V2321 ran through `native_init_flash.py` with pinned SHA256.
- Rollback version check returned `0.9.285 (v2321-usb-clean-identity-rodata)`.
- Rollback `selftest verbose` returned `fail=0`.
- A follow-up manual bridge check with slow input also confirmed V2321 `version`, `status`, and `selftest fail=0`.

## Classification

`control-channel-desync-before-materialization`

This is not a `/dev/snd` result and not an ADSP/audio regression. The run stopped before all audio commands because the runner treated a single protocol parse failure in a read-only health command as fatal. The device recovered through the expected rollback path.

## Hardening Applied

Updated `workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py` to reduce this specific failure mode before the next gated live attempt:

- Adds `--input-mode slow` to every `a90ctl.py` command constructed by the runner.
- Adds `run_a90ctl_observation()` for read-only observation commands.
- Observation commands now use `--hide-on-busy` plus bounded retry.
- The helper is intentionally **not** used for token-gated mutation commands.
- `audio adsp-boot-once AUD2_ONE_SHOT_ADSP_BOOT` and `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY` remain one-shot live actions; marker loss after a token command is not retried.
- Dry-run output now reflects slow input and hide-on-busy for observation commands.

## Safety Boundary Preserved

- No ALSA node open/ioctl.
- No mixer, tinyalsa, PCM, HAL, or playback.
- No `adsprpc` invoke/ioctl.
- No `/dev/subsys_adsp` open.
- No `/dev/snd` materialization was attempted in this live run.
- Boot partition only was flashed.
- Rollback to V2321 completed and final selftest remained `fail=0`.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py`: PASS.
- `python3 workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py --dry-run`: PASS after hardening.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: PASS (`996` tests).
- `git diff --check`: PASS.

## Next Step

Do not count this as an AUD-3 materialization result. The next live attempt can reuse the same exact AUD-3-preflight approval boundary, but it should run the hardened runner. Because the token-gated audio actions were never reached, this was not a repeated audio-subgoal failure.
