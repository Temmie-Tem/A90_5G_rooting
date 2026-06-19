# Native Init V2891 Video Fixture Cache Live Validation

## Summary

- Cycle: `V2891`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2891-video-fixture-cache-live-pass-before-rollback`
- Result: `PASS`
- Candidate: `v2889-video-cadence` / `0.10.30`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2889_video_cadence.img`
- Candidate SHA256: `6e946878aaf749de333ac27ab229e199a64ae4d07096079c1743f92a05a43a4f`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Fixture

- Manifest: `workspace/private/runs/video/v2891-video-fixture-cache-live-20260619-225215/fixture/manifest.json`
- Stream: `workspace/private/runs/video/v2891-video-fixture-cache-live-20260619-225215/fixture/frames.a90vstr`
- SHA256: `4282fc520ff8d805333fcc313b4d9e76e3a5274454b25b556502405da2647488`
- Frame bytes: `10444800`
- Stream bytes: `313344556`
- Frames/FPS: `30` @ `30/1`
- Cache root: `/mnt/sdext/a90/runtime/video/cache` enabled=`1`

## Runtime Install

- Selected transport: `none`
- Control channel: `serial`
- Cache source: `hit` hit=`1` adopted=`0` uploaded=`0`
- Remote manifest used: `/mnt/sdext/a90/runtime/video/cache/sha256-4282fc520ff8d805333fcc313b4d9e76e3a5274454b25b556502405da2647488/manifest.json`
- Remote stream used: `/mnt/sdext/a90/runtime/video/cache/sha256-4282fc520ff8d805333fcc313b4d9e76e3a5274454b25b556502405da2647488/frames.a90vstr`
- none

## Stream Result

- Presented frames: `30` / `30`
- Flip events: `30` / `30`
- Flip delta count: `29`
- Flip delta min/avg/max/target us: `16620` / `32661` / `33252` / `33333`
- Flip delta avg error / jitter span us: `672` / `16632`
- Present mode markers: requested=`1` active=`1`
- SHA checked/match: `1` / `1`
- Pixel format marker: `1`
- KMS page-flip path marker: `1`
- Stream stdout: `workspace/private/runs/video/v2891-video-fixture-cache-live-20260619-225215/11_candidate-video-stream.txt`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.
- Generated frame payloads and raw command transcripts remain private under `workspace/private/`.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
