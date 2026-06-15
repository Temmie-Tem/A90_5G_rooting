# NATIVE_INIT_V2456_AUDIO_ACDB_M1_LIVE_PREFLIGHT_READY_2026-06-15

## Summary

V2456 performed a no-flash/no-playback preflight for the next exact-gated AUD-5L
ACDB M1 hybrid late-observer rerun after the V2455 post-module settle hardening.
The live path is ready, but was not executed because this iteration did not carry
the exact AUD-5L approval phrase as a fresh operator gate.

## Preconditions Checked

- Current resident native image verified through the checked flash helper:
  - `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
  - `native_init_flash.py --verify-only --from-native` passed.
- Serial bridge status:
  - bridge process/listener present on `127.0.0.1:54321`
  - selected serial device resolves to the A90 native ACM node.
- Native health:
  - `version` passed.
  - `status` passed.
  - `selftest verbose` passed with `fail=0`.
- Rollback inputs:
  - V2321 rollback image SHA256 matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
  - V2237 fallback image SHA256 matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
  - V48 fallback image exists at `workspace/private/inputs/boot_images/boot_linux_v48.img`.

## Dry-Run Result

Materialized V2451/V2455 dry-run for the future V2456 live rerun:

- `ok=true`
- `future_live_ready=true`
- `future_live_blockers=[]`
- `command_safety_ok=true`
- `stage_wait_count=10`
- `boot_complete_soft_gate=true`
- `root_check_hard_gate=true`
- Android boot candidate:
  - `workspace/private/backups/baseline_a_20260423_030309/boot.img`
  - SHA256 `c15ce425abb8da41f0b1696d19d05a625fd7cec949b4ae50651a5f1e7293057b`
- Private module/helper artifacts were generated under `workspace/private/` only and are not committed.

## Gate Status

The exact live approval phrase remains required before any Android handoff/flash/playback:

```text
AUD-5L-acdb-m1-hybrid-late-observer go: rollbackable Android AudioTrack speaker msm_audio_cal diagnostic ioctl capture with temporary Magisk service module plus host-coordinated late observer, helper-completion wait, no native calibration ioctl, no native speaker write, rollback to V2321
```

Without that exact phrase in the current live unit, V2456 stops at preflight. This is not a failure and not ACDB evidence.

## Magisk Position

No change: Magisk is only the Wi-Fi-style Android-good measurement capsule for observing the stock Android ACDB/App Type path. It is not a native-init runtime dependency.

## Next

Run the exact-gated AUD-5L live rerun when the operator provides the phrase above. Expected discriminator:

- post-module ADB reacquires,
- post-module boot-complete is recorded as soft telemetry,
- Magisk `uid=0` root becomes ready,
- late observer starts immediately before bounded Android `AudioTrack` playback,
- private artifacts classify whether `/dev/msm_audio_cal` payload entries were captured.
