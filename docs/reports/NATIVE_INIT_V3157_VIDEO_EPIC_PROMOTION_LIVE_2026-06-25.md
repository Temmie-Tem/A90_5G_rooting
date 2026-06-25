# Native Init V3157 Video Epic Promotion Live

## Summary

- Cycle: `V3157`
- Decision: `v3157-video-epic-promotion-live-pass`
- Init: `A90 Linux init 0.11.0 (v3157-video-epic-promotion)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3157_video_epic_promotion.img`
- Boot SHA256: `cc458455e64af62720eebe2f80d7f8b49ea8c8bd3a96368b8a5311b685c4ad33`
- Result: PASS; Video 0.11.0 promotion is closed.

## Safety Gates

- Rollback `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper rollback `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 matched
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed.
- TWRP recovery artifacts existed under `workspace/private/inputs/firmware/twrp/`.
- Bridge was managed and listening on `127.0.0.1:54321`, selected `/dev/ttyACM0`.
- Pre-flash V3156 health: `selftest: pass=12 warn=1 fail=0`.

## Flash

Command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-version '0.11.0' \
  --expect-sha256 cc458455e64af62720eebe2f80d7f8b49ea8c8bd3a96368b8a5311b685c4ad33 \
  workspace/private/inputs/boot_images/boot_linux_v3157_video_epic_promotion.img
```

Result:

- Local image marker and SHA256 matched.
- TWRP push SHA256 matched.
- Boot block readback SHA256 matched.
- Post-flash native-init verify passed for `version/status`.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.

## Three-Demo Promotion Validation

| Demo | Command Surface | Frames | FPS milli | Dropped | Key Evidence | Result |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Bad Apple | Player HUD, video-only | 300 | 30065 | 0 | elapsed `9978373121ns`, render avg/max `9313/48605us`, present avg/max `8802/16785us` | pass |
| Nyan Cat | Player HUD, video-only | 300 | 30053 | 0 | elapsed `9982248694ns`, render avg/max `13358/51917us`, present avg/max `7910/16790us` | pass |
| DOOM | WAD verify | - | - | - | SHA256 match `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`, `magic=IWAD`, `ok=1` | pass |
| DOOM | Foreground loop | 120 | - | 0 missed shared frames | `frames_presented=120`, `display.rc=0`, `loop.rc=0`, `flip_events=120`, `pace_socket.failures=0` | pass |
| DOOM | Background loop + SFX stream | 120 | - | - | `loop_start.rc=0`, `audio_stream_prepare_rc=0`, `audio_rc=0`, `loop_status.active=0` after bounded run | pass |

After the DOOM background/SFX check, `audio stop internal-speaker-safe --execute` returned
`audio.stop.done=1 rc=0`; `/proc/658/status` was absent, confirming the tracked worker exited.

## Final Health

- Final resident: `A90 Linux init 0.11.0 (v3157-video-epic-promotion)`.
- Final status: `selftest: pass=12 warn=1 fail=0`.
- Storage: SD runtime mounted read/write.
- Transport: serial ready, NCM ready, tcpctl ready.

## Decision

The Video epic promotion criteria are satisfied on a single 0.11.0 image bundling Bad Apple,
Nyan Cat, and DOOM. The reserved GPU epic may now activate at Gate G0, limited to host-side
source/DTS diagnosis and strictly timeout-guarded bounded probes.
