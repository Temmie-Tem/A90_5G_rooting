# Native Init V3078 DOOMGENERIC Pageflip Presenter Live

## Summary

- Cycle: `V3078`
- Date: `2026-06-23`
- Type: rollback-gated live validation of the V3077 pageflip-presenter candidate.
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3077_doomgeneric_pageflip_presenter.img`
- Boot SHA256: `69cd60b67ccf7e89da8d1613641ca6dc5e8e943638e4116942148f887adc2455`
- Resident after flash: `A90 Linux init 0.10.95 (v3077-doomgeneric-pageflip-presenter)`
- Result: PASS, with a remaining cadence finding.

## Flash Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` matched the expected SHA256.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` matched the expected SHA256.
- Final fallback `boot_linux_v48.img` was present.
- TWRP recovery files were present.
- Flash used only `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Flash helper verified local image marker, local SHA256, recovery transfer SHA256, boot readback SHA256, reboot, and candidate `version`/`status`.
- No forbidden partition was touched.

## Health

Post-flash health check passed:

- `selftest: pass=12 warn=1 fail=0`
- `version`: `A90 Linux init 0.10.95 (v3077-doomgeneric-pageflip-presenter)`

## Resident Markers

`video demo doom status` showed the expected V3077 pageflip presenter contract:

- `video.demo.engine.bridge=v3077-doomgeneric-pageflip-presenter`
- `video.demo.engine.active=doomgeneric-private-link-v3077-pageflip-presenter`
- `video.demo.input.active=udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.input.udp_port=30570`
- `video.demo.doom.loop.frame_ms=28`
- `video.demo.doom.presenter.pacing=helper-frame-mtime`
- `video.demo.doom.presenter.poll_ms=4`
- `video.demo.doom.presenter.present_mode=pageflip`
- `video.demo.doom.presenter.present_path=kms-dumb-buffer-pageflip`
- `video.demo.doom.presenter.pageflip_timeout_ms=1000`
- `video.demo.doom.presenter.reader=reused-loop-buffer`
- `video.demo.doom.presenter.buffer_reuse=1`
- `video.demo.doom.dashboard.profile=minimal-fastdraw`
- `video.demo.doom.dashboard.metrics_pacing=disabled-minimal`
- `video.demo.doom.dashboard.large_frame=0`
- `video.demo.doom.dashboard.frame_mode=minimal-dashboard`

## Foreground Timing Probe

Foreground `video demo doom loop 300 --wad runtime-private --sha256 EXPECTED` passed with:

- `frames_presented=300`
- `poll_count=1168`
- `helper_done=0`
- `display.rc=0`
- `loop.rc=0`
- `presenter.buffer_allocations=1`

Stage timing, in microseconds:

| Stage | Average | Max |
| --- | ---: | ---: |
| alloc | 1 | 46 |
| frame-file read | 489 | 982 |
| KMS begin | 4526 | 4870 |
| dashboard/draw | 770 | 1102 |
| KMS present | 7521 | 12940 |
| total | 13306 | 18634 |

Pageflip telemetry:

- `present_mode=pageflip`
- `present_path=kms-dumb-buffer-pageflip`
- `flip_events=300`
- `flip_delta_count=299`
- `flip_delta_min_us=16615`
- `flip_delta_avg_us=33456`
- `flip_delta_max_us=49865`
- `pageflip_timeout_ms=1000`

## Comparison To V3076

| Metric | V3076 SETCRTC 300-frame sample | V3078 pageflip 300-frame sample |
| --- | ---: | ---: |
| frames presented | 300 | 300 |
| frame-file read max | 926 us | 982 us |
| dashboard/draw max | 873 us | 1102 us |
| KMS present average | 7033 us | 7521 us |
| KMS present max | 16878 us | 12940 us |
| total average | 12807 us | 13306 us |
| total max | 22782 us | 18634 us |
| flip events | not applicable | 300 |
| flip delta max | not available | 49865 us |

## Interpretation

V3077 did what it was designed to isolate: DOOM now uses the same DRM pageflip
primitive already proven by the video stream path, and every displayed DOOM frame
received a flip event.

The worst-case KMS present and total-frame timing improved versus the V3076
SETCRTC sample. The average timing is slightly higher because pageflip waits for
vblank instead of returning as soon as SETCRTC completes.

The remaining visible-stutter suspect is now stronger and more specific: the display
cadence is not perfectly fixed at two vblanks per source frame. The V3078 sample had
one-frame flip deltas near one, two, and three vblanks, with `flip_delta_max_us=49865`.
That matches the original priority item about producer/presenter pacing: the helper
still sleeps independently, and the presenter still polls the helper frame file instead
of owning a single vblank-based schedule.

## Continuous Functional Check

- Started continuous DOOM loop on V3077.
- `loop_status.active=1`
- `loop_status.continuous=1`
- Audio co-run start returned `rc=0`; this remains the bounded native tone path, not real DOOM SFX/music.
- NCM gadget was active after reboot, but the host-side IPv4 route was missing and was repaired with the checked `ncm_host_setup.py setup` helper.
- UDP input over NCM advanced the device input-state to `seq=1303` and returned to all-up state.
- Final `selftest` still reported `fail=0`.

## Operational Note

Serial command text corruption reproduced once after the long live run: `video demo doom loop-status`
arrived at the device with a missing character and was rejected. Restarting the managed
`a90_bridge.py` wrapper fixed the immediate issue, and the same short command then
succeeded. This remains a control-plane validation hazard, not the gameplay UDP input path.

## Next Suspect

The next V-iteration should target single-owner frame pacing:

- Keep pageflip enabled.
- Stop treating helper output cadence as the presentation clock.
- Let the presenter hold each source frame for a fixed two vblanks, or otherwise drive
  presentation from flip events instead of independent helper sleep plus presenter poll.
- Prefer a design where the helper produces latest frames as fast as practical, while
  the presenter owns vblank cadence and drops/reuses frames explicitly.

This directly addresses the original highest-priority remaining issue: independent
producer/presenter sleeps causing uneven output cadence.
