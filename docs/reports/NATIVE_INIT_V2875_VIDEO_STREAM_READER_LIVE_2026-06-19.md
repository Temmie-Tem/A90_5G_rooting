# Native Init V2875 Video Stream Reader Live Validation

## Summary

- Cycle: `V2875`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2875-video-stream-reader-live-pass-before-rollback`
- Result: `PASS`
- Candidate: `v2874-video-stream-reader` / `0.10.23`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2874_video_stream_reader.img`
- Candidate SHA256: `da69a7e1402b5eb5a84e4a62560f291af5373c2d63aca817263f7a841bbcbfa7`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Fixture

- Manifest: `workspace/private/runs/video/v2875-video-stream-reader-live-20260619-194746/fixture/manifest.json`
- Stream: `workspace/private/runs/video/v2875-video-stream-reader-live-20260619-194746/fixture/frames.a90vstr`
- SHA256: `e84656951e1e64f6c5b3502fc84776be6dbb7f9a23a88c9bf536f56f37ee7e41`
- Frame bytes: `10444800`
- Stream bytes: `62668972`
- Frames/FPS: `6` @ `6/1`

## Runtime Install

- Selected transport: `tcpctl`
- Control channel: `tcpctl`
- `manifest` -> `/cache/a90-runtime/pkg/video/v2875/manifest.json` ok=`1`
- `stream` -> `/cache/a90-runtime/pkg/video/v2875/frames.a90vstr` ok=`1`

## Stream Result

- Presented frames: `6` / `6`
- SHA checked/match: `1` / `1`
- Pixel format marker: `1`
- KMS path marker: `1`
- Stream stdout: `workspace/private/runs/video/v2875-video-stream-reader-live-20260619-194746/16_candidate-video-stream.txt`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.
- Generated frame payloads and raw command transcripts remain private under `workspace/private/`.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
