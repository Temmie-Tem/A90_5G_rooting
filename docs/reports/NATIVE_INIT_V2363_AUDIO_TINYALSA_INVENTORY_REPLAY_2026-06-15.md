# NATIVE_INIT V2363 — AUD-3C tinyalsa inventory replay

Date: 2026-06-15

## Scope

- Unit: operator-requested AUD-3C replay of the V2359 read-only tinyalsa inventory path.
- Approval phrase used: `AUD-3C-tinyalsa-inventory go: read-only tinyalsa mixer/PCM inventory on materialized V2334, no mixer set, no tinyplay/playback, rollback to V2321`.
- Candidate image: V2334 `0.9.292` (`v2334-audio-snd-nodes-preflight`), SHA256 `53b1130cd912ca4019a3d76835eb721804bae0460b920eb7fdfad5509a2dfcac`.
- Rollback target: V2321 `0.9.285` (`v2321-usb-clean-identity-rodata`), SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Raw private run evidence: `workspace/private/runs/audio/v2349-tinyalsa-inventory-20260615-022634/`.

## Result

Decision: `v2363-tinyalsa-inventory-replay-pass-frontier-unchanged`.

The V2359 AUD-3C result reproduced cleanly: V2334 booted, ADSP boot and `/dev/snd`
materialization completed, the pinned tinyalsa read-only tools ran successfully over `tcpctl`,
and the device rolled back to V2321 with `selftest fail=0`.

This replay does not move the audio frontier. The next substantive speaker-route step remains
the V2362 Android route-delta helper gap: add a checked Android-target flash/handoff path before
any Android framework playback capture.

## Evidence

- Preflight resident health:
  - V2321 `version: 0.9.285 build=v2321-usb-clean-identity-rodata`
  - `selftest verbose`: `fail=0`
- Candidate V2334 boot:
  - flash helper verified V2334 `0.9.292`
  - candidate post-inventory `selftest verbose`: `fail=0`
- `/dev/snd` materialization:
  - before materialization: `audio.dev_snd.count=0 control_like=0 pcm_like=0`
  - after materialization: `audio.dev_snd.count=61 control_like=1 pcm_like=59`
- Tinyalsa tools:
  - `tinymix` staged to `/cache/bin/tinymix`
  - `tinypcminfo` staged to `/cache/bin/tinypcminfo`
  - transfer path selected `tcpctl` after host NCM repair

## Read-only inventory commands

| Command | Result | Transport | Evidence |
| --- | --- | --- | --- |
| `/cache/bin/tinymix -D 0` | `rc=0` | `tcpctl` | card `sm8150-tavil-snd-card`, `3628` controls |
| `/cache/bin/tinymix -D 0 --all-values` | `rc=0` | `tcpctl` | full mixer value snapshot captured privately |
| `/cache/bin/tinypcminfo -D 0 -d 0` | `rc=0` | `tcpctl` | card 0/device 0 PCM out/in caps returned |

`tinypcminfo -D 0 -d 0` again reported:

- formats: `S16_LE`, `S24_LE`, `S32_LE`, `S24_3LE`
- rate range: `8000Hz` to `384000Hz`
- channel range: `1` to `16`
- sample bits: `16` to `32`
- playback period size: `2` to `61440`, period count `2` to `8`
- capture period size: `5` to `61440`, period count `2` to `8`

## Safety outcome

- No `tinyplay` command executed.
- No mixer set/write command executed.
- No PCM playback/write command executed.
- No audio HAL path executed.
- No `adsprpc` path executed.
- Rollback to V2321 completed.
- Final V2321 health check:
  - `version: 0.9.285 build=v2321-usb-clean-identity-rodata`
  - `selftest verbose`: `fail=0`

## Interpretation

AUD-3C is reproducible. The evidence remains limited to read-only ALSA control/PCM
introspection after ADSP and `/dev/snd` materialization. It does not prove any safe speaker
route, and it does not justify native `tinymix set`, PCM playback, or `tinyplay`.

The V2362 conclusion still stands: learn the actual speaker route from Android's vendor HAL path
before attempting native speaker writes.

## Validation

- `native_audio_tinyalsa_inventory_live_handoff_v2349.py --dry-run`
- exact-gated live run with rollback to V2321
- final `a90ctl.py version`
- final `a90ctl.py selftest verbose`
- `git diff --check`
