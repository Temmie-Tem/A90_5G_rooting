# Native Init V2901 Video Bad Apple Scale Mono1 Cache Hit Live Validation

## Summary

- Cycle: `V2901`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2901-video-badapple-scale-mono1-cache-hit-live-pass-before-rollback`
- Result: `PASS`
- Candidate: `v2897-video-long-mono1-stream` / `0.10.33`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2897_video_long_mono1_stream.img`
- Candidate SHA256: `1d93aa70bf01f9785ab63656cd45d456ec7e180f7510934fbe280082bb31ba32`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Fixture

- Manifest: `workspace/private/runs/video/v2901-video-badapple-scale-mono1-cache-hit-live-20260620-005219/fixture/manifest.json`
- Stream: `workspace/private/runs/video/v2901-video-badapple-scale-mono1-cache-hit-live-20260620-005219/fixture/frames.a90vstr.cache-hit-only-not-generated`
- SHA256: `878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890`
- Frame bytes: `324000`
- Stream bytes: `2106428092`
- Format: `mono1`
- Frames/FPS: `6501` @ `30/1`
- Cache root: `/mnt/sdext/a90/runtime/video/cache` enabled=`1`

## Runtime Install

- Selected transport: `none`
- Control channel: `serial`
- Cache source: `hit` hit=`1` adopted=`0` uploaded=`0`
- Cache policy: `required-hit`; a miss fails before upload/stream.
- Remote manifest used: `/mnt/sdext/a90/runtime/video/cache/sha256-878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890/manifest.json`
- Remote stream used: `/mnt/sdext/a90/runtime/video/cache/sha256-878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890/frames.a90vstr`
- none

## Stream Result

- Presented frames: `6501` / `6501`
- Flip events: `6501` / `6501`
- Flip delta count: `6500`
- Flip delta min/avg/max/target us: `16611` / `33331` / `49900` / `33333`
- Flip delta avg error / jitter span us: `2` / `33289`
- Present mode markers: requested=`1` active=`1`
- SHA checked/match: `1` / `1`
- Pixel format marker: `1`
- KMS page-flip path marker: `1`
- Stream stdout: `workspace/private/runs/video/v2901-video-badapple-scale-mono1-cache-hit-live-20260620-005219/10_candidate-video-stream.txt`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.
- Generated frame payloads and raw command transcripts remain private under `workspace/private/`.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
