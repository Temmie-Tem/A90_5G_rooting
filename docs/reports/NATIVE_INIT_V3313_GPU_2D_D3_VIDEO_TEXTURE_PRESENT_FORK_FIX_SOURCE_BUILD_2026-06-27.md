# Native Init V3313 GPU 2D D3 Video Texture Present Fork Fix Source Build

## Summary

- Cycle: `V3313`
- Track: GPU accelerated 2D D3, video texture blit into present path.
- Decision: `v3313-gpu-2d-d3-video-texture-present-fork-fix-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3313_gpu_2d_d3_video_texture_present_fork_fix.img`
- Boot SHA256: `35eea212e68573f7e2476cb17dbf62412cbb8ff5f6c8812ef518a24eb7aa0db3`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3312_gpu_2d_d3_video_texture_present_probe.img`
- Init: `A90 Linux init 0.11.85 (v3313-gpu-2d-d3-video-texture-present-fork-fix)`

## Included Delta

- Adds `gpu d3-video-texture-present-probe` to the native GPU command set.
- Reads the Bad Apple SD-cache mono1 stream frame-by-frame and uses the V3311 texture path as an actual video consumer.
- Reuses one child-owned KGSL session across frames, uploads each source frame as a 480x360 RGBA8 texture, renders a textured quad to a 960x720 target, A2D-linearizes it, copies it into the KMS dumb framebuffer, and presents.
- Fixes the V3312 fork child path so only the parent returns through the shell/A90P1 protocol; the child writes summary telemetry to the pipe and exits.
- Raises the D3 probe timeout ceiling to 120000 ms to match the long video-present validation command.
- Reports presented frames, fps, and per-stage read/texture/GPU-wait/readback/copy/present/total timings.

## D3 Gate

- Source preset: `badapple`, SHA256 `9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0`, geometry `480x360 mono1`.
- PASS requires `gpu.d3.video.result=video-texture-present-pass`, `presented>0`, `changed_total>0`, and timing telemetry.
- This first D3 gate is still a recoverable probe path, not a new default menu policy.

## Safety

- KGSL and KMS work runs in a timeout-guarded child; the parent can kill the worker on timeout.
- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, or forbidden partition work.
- Boot partition only through `native_init_flash.py` in the live step.

## Validation

- `py_compile`: V3313 builder and focused source test.
- `unittest`: V3313 D3 source contract plus V3311 D2 baseline coverage.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3313 identity plus D3 video texture present telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Textured FS SHA256: `4e8ad0a934d236149af999619a1fe99690e7b732d2e4ca69a2b345100d8d04a3`
- D0 reference: `v3304-fd6-texture-reference-recon`
- D1 shader gate: `v3305-verified-textured-fs-shader-bytes`
- D2 live baseline: `v3311-d2-realframe-texture-live-pass`
- Candidate type: `gpu-2d-d3-video-texture-present-fork-fix-candidate`.
