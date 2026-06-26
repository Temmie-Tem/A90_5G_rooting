# Native Init V3312 GPU 2D D3 Video Texture Present Live Fork Bug

## Summary

- Cycle: `V3312`
- Track: GPU accelerated 2D D3, video texture blit into present path.
- Candidate: `workspace/private/inputs/boot_images/boot_linux_v3312_gpu_2d_d3_video_texture_present_probe.img`
- Candidate SHA256: `f4a1c037b2e17d7b4b7ab372b0eceaa84fc6fddc626c96f3c8bc4f3ddaf10899`
- Init after flash: `A90 Linux init 0.11.84 (v3312-gpu-2d-d3-video-texture-present-probe)`
- Result: NOT CLOSED. Boot/health passed, but live D3 found a fork/protocol bug and a too-low timeout ceiling.

## Flash Gate

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Rollback image verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
  SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper fallback verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
  SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Final fallback verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v48.img`
  SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- Recovery/TWRP image verified before flash:
  `workspace/private/inputs/firmware/twrp/recovery.img`
  SHA256 `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`
- Flash verification matched local image SHA, remote staged image SHA, and boot-block readback-prefix SHA.

## Health

- Pre-flash resident: `A90 Linux init 0.11.83 (v3311-gpu-2d-d2-realframe-texture-probe)`
- Pre-flash selftest: `pass=12 warn=1 fail=0`
- Post-flash resident: `A90 Linux init 0.11.84 (v3312-gpu-2d-d3-video-texture-present-probe)`
- Flash-helper status selftest: `pass=12 warn=1 fail=0`
- Standalone post-flash selftest initially hit serial marker noise, then reran with slow input and passed:
  `pass=12 warn=1 fail=0`
- Post-D3-attempt selftest stayed clean: `pass=12 warn=1 fail=0`

## Live Findings

The source-build report's long validation command was rejected by the device:

```text
gpu d3-video-texture-present-probe --preset badapple --frames 60 --timeout-ms 120000 --hold-ms 5000 --materialize-devnode
gpu.d3.video.error=timeout-too-large max_ms=10000
A90P1 END seq=7 cmd=gpu rc=-22 errno=22 duration_ms=0 flags=0x0 status=error
```

A shorter command entered the D3 path but exposed a fork/protocol bug:

```text
gpu d3-video-texture-present-probe --preset badapple --frames 60 --timeout-ms 10000 --hold-ms 3000 --materialize-devnode
gpu.d3.video.child_pid=663
[done] gpu (5049ms)
A90P1 END seq=8 cmd=gpu rc=0 errno=0 duration_ms=5049 flags=0x0 status=ok
```

The missing `gpu.d3.video.result=*` and timing lines show the child returned through the normal shell command completion
path and emitted the first A90P1 END. The parent summary telemetry was not reliably captured. This is not a boot-health
failure, but it makes V3312 unsuitable as the D3 close image.

## Follow-Up

V3313 supersedes this image. It fixes the child path to write summary telemetry to the pipe and `_exit()`, and raises the
D3 timeout ceiling to `120000` ms.
