# NATIVE_INIT_V2464_AUDIO_ACDB_DMABUF_LIVE_STAGE_GAP_2026-06-15

## Scope

Recoverable Android-good live rerun using the V2463 dmabuf-capable observer.
This stayed inside the GOAL.md recoverable envelope: checked Android boot handoff,
temporary Magisk measurement staging intent, cleanup, and checked rollback to
V2321. No native calibration ioctl was issued.

Private run directory:

- `workspace/private/runs/audio/v2464-acdb-dmabuf-live-20260615-194724/`

## Decision

`v2464-acdb-dmabuf-live-stage2-adb-closed-before-staging-rollback-pass`

The run did not reach module file push, late observer startup, AudioTrack
playback, `/dev/msm_audio_cal` ioctl capture, or dmabuf capture. It failed at
`stage-2`, the root-side residue/setup shell gate, with ADB stderr:

```text
error: closed
```

This is an Android ADB transport/stage-gap, not audio evidence and not a dmabuf
negative result.

## Preflight evidence

Before live action:

- rollback V2321 image SHA-256 matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`;
- deeper V2237 fallback SHA-256 matched
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`;
- final V48 fallback existed with SHA-256
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`;
- bridge status selected `A90-LNX_A90_Linux_ARM64_A90NATIVE001-if00` on
  `/dev/ttyACM0`;
- resident native V2321 health passed with `selftest fail=0`;
- materialized dry-run reported `future_live_ready=True`, `command_safety_ok=True`,
  and `adds_private_dmabuf_payload_capture=True`.

## Live timeline summary

Successful steps before failure:

1. Checked flash of pinned Android boot image passed.
2. Android ADB post-handoff wait passed.
3. Android boot-complete recheck passed.
4. Magisk root check passed as `root-ready` with `uid=0`.
5. `stage-0` ADB wait plus read-only `su -c` Magisk cleanup probe passed.
6. `stage-1` ADB wait plus read-only `su -mm -c` Magisk cleanup probe passed.
7. `stage-2` ADB wait passed.
8. `stage-2` shell command failed immediately with `error: closed` and no stdout.

Cleanup and rollback:

- cleanup-finally removed any possible module/run-dir residue;
- residue check reported `A90_M1_CLEANUP_OK`;
- Android reboot to recovery succeeded;
- checked V2321 rollback succeeded;
- final native `version` reported `0.9.285 (v2321-usb-clean-identity-rodata)`;
- final native `selftest verbose` reported `fail=0`.

## Interpretation

V2464 reproduces the class of Android ADB stage instability previously seen in
older ACDB handoff attempts, but now after an explicit `adb wait-for-device`
immediately before the failing shell command. That means the remaining gap is not
"no wait before stage"; it is "ADB can close during the stage shell command after
wait returns".

The failed command is still pre-staging cleanup/residue setup. No module files
were pushed and no audio observer/playback action started, so this run provides
no signal about the V2463 dmabuf helper itself.

## Next safe unit

Host-only hardening is required before another live rerun:

- add bounded retry around stage `adb shell` / `adb push` / `adb install` commands
  when stderr/stdout contains transient transport markers such as `error: closed`
  or `no devices/emulators found`;
- keep command-specific retries bounded and report attempts;
- preserve fail-closed behavior for semantic failures like residue present,
  SHA mismatch, missing Magisk root, or non-idempotent cleanup errors;
- rerun the materialized dry-run and focused tests;
- then perform a fresh bounded Android-good dmabuf live rerun.

Do not treat V2464 as ACDB payload evidence, and do not issue native calibration
ioctls before the Android-good dmabuf payload is captured.
