# Native Init V3156 Video Player HUD Cadence Live

## Summary

- Cycle: `V3156`
- Decision: `v3156-video-player-hud-cadence-live-pass`
- Init: `A90 Linux init 0.10.138 (v3156-video-player-hud-cadence)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3156_video_player_hud_cadence.img`
- Boot SHA256: `a1544a56bbb0f5aee867477029891e42cc59a20f5d2f97ba8f1f45324fe925ca`
- Result: PASS for the Bad Apple/Nyan Player HUD cadence blocker.

## Change Validated

V3156 keeps the V3155 DOOM/SFX behavior and changes the video Player HUD path used by
Bad Apple and Nyan. Static HUD strings are no longer erased and redrawn every frame,
full-screen Player HUD repaint cadence is reduced from 60-frame intervals to 300-frame
intervals, and `video.stream.timing.*` metrics are emitted for live stage attribution.

## Safety Gates

- Rollback `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper rollback `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 matched
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed.
- TWRP recovery artifacts existed under `workspace/private/inputs/firmware/twrp/`.
- Bridge was managed and listening on `127.0.0.1:54321`, selected `/dev/ttyACM0`.
- Pre-flash resident was healthy: V3155 `status` showed `selftest: pass=12 warn=1 fail=0`.

## Flash

Command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-version '0.10.138' \
  --expect-sha256 a1544a56bbb0f5aee867477029891e42cc59a20f5d2f97ba8f1f45324fe925ca \
  workspace/private/inputs/boot_images/boot_linux_v3156_video_player_hud_cadence.img
```

Result:

- Local image marker and SHA256 matched.
- TWRP push SHA256 matched.
- Boot block readback SHA256 matched.
- Post-flash native-init verify passed for `version/status`.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.

## Video-Only Results

| Demo | Frames | Elapsed ns | FPS milli | Dropped | Render avg/max us | Present avg/max us | Total avg/max us | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bad Apple Player HUD | 300 | 9973733070 | 30079 | 0 | 9462 / 66024 | 8174 / 16780 | 33241 / 70715 | pass |
| Nyan Player HUD | 300 | 9971793017 | 30084 | 0 | 13595 / 71555 | 7407 / 16273 | 33234 / 75293 | pass |

V3155 live baselines for the same 300-frame Player HUD path were roughly 13.3-13.6s
and 22fps. V3156 restores the Player HUD path to the expected 10s/30fps cadence.

## A/V Sync Results

| Demo | Frames | Elapsed ns | FPS milli | Dropped | Audio Sync | Audio Worker | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| Nyan Player HUD + PCM | 300 | 9976660204 | 30070 | 0 | ready, first frame 0 | `done=1 rc=0` | pass |
| Bad Apple Player HUD + PCM | 300 | 9982845100 | 30051 | 0 | ready, first frame 0 | `done=1 rc=0` | pass |

The earlier perceived audio issue is consistent with the old Player HUD video cadence:
audio ran on the 10s PCM clock while the video path took about 13.5s. With V3156, both
Bad Apple and Nyan stay at about 30fps with audio sync active.

## Residual Risk

- `late_frames=300` remains expected with the current post-present accounting because
  frames are evaluated after the setcrtc present call. The useful V3156 signal is the
  restored elapsed time, zero drops, and stage timing.
- Max render spikes still reach about 66-126ms during Player HUD, so this is a cadence
  fix rather than a full jitter elimination. The added timing fields give the next unit
  a direct target if the operator still sees isolated hitches.
- Legacy test `tests.test_native_video_badapple_player_hud_fastpath_v2952` still has a
  stale command-help expectation from before the `nyan|doom` demo expansion; it is not a
  V3156 runtime failure.
