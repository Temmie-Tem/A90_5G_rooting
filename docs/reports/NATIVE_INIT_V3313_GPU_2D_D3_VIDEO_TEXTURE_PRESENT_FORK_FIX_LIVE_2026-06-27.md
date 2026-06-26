# Native Init V3313 GPU 2D D3 Video Texture Present Fork Fix Live

## Summary

- Cycle: `V3313`
- Track: GPU accelerated 2D D3, video texture blit into present path.
- Candidate: `workspace/private/inputs/boot_images/boot_linux_v3313_gpu_2d_d3_video_texture_present_fork_fix.img`
- Candidate SHA256: `35eea212e68573f7e2476cb17dbf62412cbb8ff5f6c8812ef518a24eb7aa0db3`
- Init after flash: `A90 Linux init 0.11.85 (v3313-gpu-2d-d3-video-texture-present-fork-fix)`
- Result: PASS for D3 telemetry live validation. Operator visual confirmation of the held demo frame remains the final
  sensory close checkpoint for rung ②.

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

- Pre-flash resident: `A90 Linux init 0.11.84 (v3312-gpu-2d-d3-video-texture-present-probe)`
- Pre-flash selftest after the V3312 fork-bug attempt: `pass=12 warn=1 fail=0`
- Post-flash resident: `A90 Linux init 0.11.85 (v3313-gpu-2d-d3-video-texture-present-fork-fix)`
- Flash-helper status selftest: `pass=12 warn=1 fail=0`
- Standalone post-flash selftest required one bridge restart after AT/noise marker loss, then passed:
  `pass=12 warn=1 fail=0`
- Post-probe selftest: `pass=12 warn=1 fail=0`

## Cache Gate

`video cache preset badapple status` passed after hiding the auto menu:

- `video.cache.preset=badapple`
- `video.cache.preset.sha256=9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0`
- `video.cache.manifest_ok=1`
- `video.cache.stream_exists=1`
- `video.cache.stream_size=150490668`
- `video.cache.stream_expected_size=150490668`
- `video.cache.stream_size_match=1`
- `video.cache.format=mono1`
- `video.cache.frames=6962`
- `video.cache.fps=30/1`
- `video.cache.size=480x360`
- `video.cache.stride=60`
- `video.cache.frame_bytes=21600`

## D3 Probe

Command:

```text
gpu d3-video-texture-present-probe --preset badapple --frames 60 --timeout-ms 120000 --hold-ms 5000 --materialize-devnode
```

Key telemetry:

- `gpu.d3.video.result=video-texture-present-pass`
- `gpu.d3.video.timed_out=0`
- `gpu.d3.video.child_killed=0`
- `gpu.d3.video.child_reaped=1`
- `gpu.d3.video.child_status=0x0`
- `gpu.d3.video.result_rc=0`
- `gpu.d3.video.manifest_rc=0`
- `gpu.d3.video.stream_open_rc=0 errno=0`
- `gpu.d3.video.header_rc=0`
- `gpu.d3.video.gpu_create_rc=0`
- `gpu.d3.video.source_size=480x360`
- `gpu.d3.video.source_stride=60`
- `gpu.d3.video.source_frame_bytes=21600`
- `gpu.d3.video.target_size=960x720`
- `gpu.d3.video.target_stride=3840`
- `gpu.d3.video.target_bytes=2764800`
- `gpu.d3.video.pm4_dwords=409`
- `gpu.d3.video.presented=60`
- `gpu.d3.video.stream_bytes=1296000`
- `gpu.d3.video.elapsed_ns=2002066458`
- `gpu.d3.video.fps_milli=29969`
- `gpu.d3.video.timing.read.avg_us=29`
- `gpu.d3.video.timing.texture.avg_us=653`
- `gpu.d3.video.timing.gpu_wait.avg_us=536`
- `gpu.d3.video.timing.readback.avg_us=0`
- `gpu.d3.video.timing.copy.avg_us=16653`
- `gpu.d3.video.timing.present.avg_us=13924`
- `gpu.d3.video.timing.total.avg_us=33365`
- `gpu.d3.video.changed_total=41472000`
- `gpu.d3.video.last_first_word=0xff000000`
- `gpu.d3.video.last_center_word=0xff000000`
- `gpu.d3.video.kms_begin_rc=0`
- `gpu.d3.video.present_rc=0`
- `gpu.d3.video.close_rc=0 errno=0`
- `A90P1 END seq=7 cmd=gpu rc=0 errno=0 duration_ms=7048 flags=0x0 status=ok`

## Kernel Log Check

Focused dmesg tail filter showed no GPU fault, hang, snapshot, opcode, SMMU/IOMMU, or page-fault signature. It only
matched the expected `a640_zap` first-use load/reset lines:

```text
subsys-restart: __subsystem_get(): __subsystem_get: a640_zap count:0
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
```

## Conclusion

V3313 proves the D3 telemetry gate: Bad Apple mono1 cache frames are uploaded as textures, rendered through the KGSL
textured-quad path into a 960x720 target, A2D-linearized, copied into the KMS dumb framebuffer, and presented at roughly
30 fps with stage timings. The final D3/② close condition still needs operator visual confirmation that the held demo
frame looked correct on the panel.
