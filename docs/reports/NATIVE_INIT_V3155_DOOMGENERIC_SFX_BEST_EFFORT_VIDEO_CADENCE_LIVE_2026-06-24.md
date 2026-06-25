# Native Init V3155 DOOMGENERIC SFX Best-Effort Video Cadence Live

- Date: 2026-06-24
- Cycle: `V3155`
- Decision: `v3155-doomgeneric-sfx-best-effort-video-cadence-live-pass`
- Init: `A90 Linux init 0.10.137 (v3155-doomgeneric-sfx-best-effort-video-cadence)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3155_doomgeneric_sfx_best_effort_video_cadence.img`
- Boot SHA256: `37ef94580015bce491a4ffecaf9c408443716a5228c72827ca728680b29ff70f`

## Summary

V3155 was flashed and health-checked successfully. The live DOOM video cadence regression
was traced to a separate audio-path stall, not to the already-fixed shared-frame/HUD path.
V3154 could still block the video loop on the SFX FIFO when the audio worker was absent or
backpressured. V3155 changes the SFX writer to best-effort nonblocking behavior so video
cadence wins over sound completeness.

## Safety Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` existed and matched
  SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` existed and matched
  SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed.
- TWRP/recovery artifacts existed under `workspace/private/inputs/firmware/twrp/`.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Partition scope: boot image only.

## Flash Result

- Local artifact SHA256 matched the expected V3155 boot SHA256.
- Recovery handoff completed.
- Remote staging SHA256 matched.
- Boot write completed.
- Readback SHA256 matched `37ef94580015bce491a4ffecaf9c408443716a5228c72827ca728680b29ff70f`.
- TWRP reboot completed.
- Post-boot cmdv1 verify passed.

## Health

Health was re-run after restarting the managed bridge and using slow serial input to avoid
ACM command coalescing observed immediately after the flash.

- `version`: `A90 Linux init 0.10.137 (v3155-doomgeneric-sfx-best-effort-video-cadence)`
- `status`: boot OK, selftest summary `pass=12 warn=1 fail=0`, autohud running, transport ready.
- `selftest verbose`: `pass=12 warn=1 fail=0`; only `helpers` remained warn with `manifest=no`.

## Live Timing

| Scenario | Frames | Shared missed | Draw max us | Total max us | Flip delta avg us | Flip delta max us | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V3154 foreground with no audio FIFO | 0 | n/a | n/a | n/a | n/a | n/a | presenter timed out before first frame |
| V3155 foreground with no audio FIFO | 180 | 0 | 44990 | 47335 | 19798 | 33293 | pass |
| V3154 audio-worker path | 240 | 0 | 406487 | 408995 | 27428 | 66558 | audio backpressure stalled video |
| V3155 audio-worker path | 240 | 0 | 4762 | 17523 | 19979 | 33291 | pass |

V3155 removed the pathological roughly 400 ms audio/SFX stall from the DOOM video loop.
The remaining cadence is consistent with pageflip and DOOM tick pacing rather than FIFO
backpressure.

## Commands

Pre-flash health:

```sh
A90CTL_INPUT_CHAR_DELAY_SEC=0.05 python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 30 --input-mode slow version
A90CTL_INPUT_CHAR_DELAY_SEC=0.05 python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 40 --input-mode slow status
A90CTL_INPUT_CHAR_DELAY_SEC=0.05 python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 60 --input-mode slow selftest verbose
```

Flash:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-version '0.10.137' \
  --expect-sha256 37ef94580015bce491a4ffecaf9c408443716a5228c72827ca728680b29ff70f \
  --expect-readback-sha256 37ef94580015bce491a4ffecaf9c408443716a5228c72827ca728680b29ff70f \
  workspace/private/inputs/boot_images/boot_linux_v3155_doomgeneric_sfx_best_effort_video_cadence.img
```

Functional checks:

```sh
A90CTL_INPUT_CHAR_DELAY_SEC=0.03 python3 workspace/public/src/scripts/revalidation/a90ctl.py \
  --timeout 90 --input-mode slow --hide-on-busy --allow-error \
  video demo doom loop 180 --wad runtime-private \
  --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771

A90CTL_INPUT_CHAR_DELAY_SEC=0.03 python3 workspace/public/src/scripts/revalidation/a90ctl.py \
  --timeout 30 --input-mode slow --hide-on-busy --allow-error \
  video demo doom loop-start 60 --wad runtime-private \
  --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771

A90CTL_INPUT_CHAR_DELAY_SEC=0.03 python3 workspace/public/src/scripts/revalidation/a90ctl.py \
  --timeout 90 --input-mode slow --allow-error \
  video demo doom loop 240 --wad runtime-private \
  --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771

A90CTL_INPUT_CHAR_DELAY_SEC=0.03 python3 workspace/public/src/scripts/revalidation/a90ctl.py \
  --timeout 30 --input-mode slow --allow-error video demo doom loop-stop

A90CTL_INPUT_CHAR_DELAY_SEC=0.03 python3 workspace/public/src/scripts/revalidation/a90ctl.py \
  --timeout 20 --input-mode slow --allow-error screenmenu
```

## Residual Notes

- Classic DOOM logic still runs on its own tick cadence, so every 60 Hz pageflip is not a
  unique simulation step.
- Sound is now best-effort. If the audio worker cannot keep up, dropping SFX samples is
  preferred over blocking the video loop.
- Serial ACM command coalescing was observed when commands were sent too aggressively after
  flashing. Managed bridge restart plus slow input recovered cleanly; device health was not
  regressed.
