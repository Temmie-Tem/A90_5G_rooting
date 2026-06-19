# Native Init V2899 Video Long Mono1 Cache Hit Live Validation

## Summary

- Cycle: `V2899`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2899-video-long-mono1-cache-hit-live-pass-before-rollback`
- Result: `PASS`
- Candidate: `v2897-video-long-mono1-stream` / `0.10.33`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2897_video_long_mono1_stream.img`
- Candidate SHA256: `1d93aa70bf01f9785ab63656cd45d456ec7e180f7510934fbe280082bb31ba32`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Fixture

- Manifest: `workspace/private/runs/video/v2899-video-long-mono1-cache-hit-live-20260620-000934/fixture/manifest.json`
- Stream: `workspace/private/runs/video/v2899-video-long-mono1-cache-hit-live-20260620-000934/fixture/frames.a90vstr`
- SHA256: `aca76424107d9cd89a68b8fd6a8f90cfe9aeb90db006868b44ee69ea15e816aa`
- Frame bytes: `324000`
- Stream bytes: `194733692`
- Format: `mono1`
- Frames/FPS: `601` @ `30/1`
- Cache root: `/mnt/sdext/a90/runtime/video/cache` enabled=`1`

## Runtime Install

- Selected transport: `none`
- Control channel: `serial`
- Cache source: `hit` hit=`1` adopted=`0` uploaded=`0`
- Cache policy: `required-hit`; a miss would fail before upload/stream.
- Remote manifest used: `/mnt/sdext/a90/runtime/video/cache/sha256-aca76424107d9cd89a68b8fd6a8f90cfe9aeb90db006868b44ee69ea15e816aa/manifest.json`
- Remote stream used: `/mnt/sdext/a90/runtime/video/cache/sha256-aca76424107d9cd89a68b8fd6a8f90cfe9aeb90db006868b44ee69ea15e816aa/frames.a90vstr`
- none

## Stream Result

- Presented frames: `601` / `601`
- Flip events: `601` / `601`
- Flip delta count: `600`
- Flip delta min/avg/max/target us: `16607` / `33321` / `49866` / `33333`
- Flip delta avg error / jitter span us: `12` / `33259`
- Present mode markers: requested=`1` active=`1`
- SHA checked/match: `1` / `1`
- Pixel format marker: `1`
- KMS page-flip path marker: `1`
- Stream stdout: `workspace/private/runs/video/v2899-video-long-mono1-cache-hit-live-20260620-000934/11_candidate-video-stream.txt`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.
- Generated frame payloads and raw command transcripts remain private under `workspace/private/`.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
- Post-run manual serial check also confirmed `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)` and `selftest fail=0`.
