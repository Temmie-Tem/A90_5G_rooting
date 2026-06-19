# Native Init V2877 Video Page-Flip Probe Live Validation

## Summary

- Cycle: `V2877`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2877-video-flipprobe-live-pass-before-rollback`
- Result: `PASS`
- Candidate: `v2876-video-flipprobe` / `0.10.24`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2876_video_flipprobe.img`
- Candidate SHA256: `2431eac000e5591709d6203130ab57e44d27d8597686aa8775dfc1b471fe759a`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Flipprobe Result

- Frames requested: `12`
- Presented frames: `12` / `12`
- Flip events: `12` / `12`
- IOCTL marker: `1`
- Pixel format marker: `1`
- Page-flip path marker: `1`
- Flipprobe stdout: `workspace/private/runs/video/v2877-video-flipprobe-live-20260619-200142/07_candidate-video-flipprobe.txt`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.
- The command exercised DRM page-flip on the existing KMS dumb-buffer path only.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
