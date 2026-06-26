# Native Init V3311 GPU 2D D2 Realframe Texture Live

## Summary

- Cycle: `V3311`
- Track: GPU accelerated 2D D2, SD-cache real frame texture readback.
- Candidate: `workspace/private/inputs/boot_images/boot_linux_v3311_gpu_2d_d2_realframe_texture_probe.img`
- Candidate SHA256: `1f70bbb99e87c20d2c9b9034055801caa6a2daee4fd110125ae3fe4201ad71f6`
- Init after flash: `A90 Linux init 0.11.83 (v3311-gpu-2d-d2-realframe-texture-probe)`
- Result: PASS. The GPU sampled a real Bad Apple SD-cache frame as a 480x360 RGBA8 texture, rendered it into the 128x128 target, linearized it, and matched all 64 bbox-local source-frame samples.

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

- Pre-flash resident: `A90 Linux init 0.11.82 (v3310-gpu-2d-d1-bbox-checkerboard-probe)`
- Pre-flash selftest: `pass=12 warn=1 fail=0`
- Pre-flash status: serial ready, NCM ready, SD mounted read/write.
- Post-flash resident: `A90 Linux init 0.11.83 (v3311-gpu-2d-d2-realframe-texture-probe)`
- Flash-helper status selftest: `pass=12 warn=1 fail=0`
- Standalone post-flash selftest: `pass=12 warn=1 fail=0`
- Post-probe selftest: `pass=12 warn=1 fail=0`
- Final status: resident still `0.11.83`, display `1080x2400`, autohud `stopped`, transport `ready`, SD mounted read/write.

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
- `video.cache.size=480x360`
- `video.cache.stride=60`
- `video.cache.frame_bytes=21600`

One earlier cache-status attempt was invalid because two host `a90ctl` commands were launched in parallel and their serial input interleaved. It produced a corrupted `cmdv1T vide...` command before the actual device handler. This was host-side command contention, not a device failure; the command was rerun sequentially and passed.

## D2 Probe

Command:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --input-mode slow --timeout 120 \
  gpu d2-realframe-texture-probe --preset badapple --frame-index 515 --timeout-ms 5000 --materialize-devnode
```

Key telemetry:

- `gpu.d2.realframe.result=realframe-texture-readback-pass`
- `gpu.d2.realframe.manifest_rc=0`
- `gpu.d2.realframe.open_stream_rc=0 errno=0`
- `gpu.d2.realframe.header_rc=0`
- `gpu.d2.realframe.record_rc=0`
- `gpu.d2.realframe.read_rc=0`
- `gpu.d2.realframe.close_stream_rc=0 errno=0`
- `gpu.d2.realframe.requested_frame_index=515`
- `gpu.d2.realframe.record_index=515`
- `gpu.d2.realframe.payload_bytes=21600`
- `gpu.d2.realframe.source_size=480x360`
- `gpu.d2.realframe.source_stride=60`
- `gpu.d2.realframe.source_frame_bytes=21600`
- `gpu.d2.realframe.source_dark_count=86381`
- `gpu.d2.realframe.source_light_count=86419`
- `gpu.d2.realframe.source_other_count=0`
- `gpu.d2.realframe.texture_size=480x360`
- `gpu.d2.realframe.texture_stride=1920`
- `gpu.d2.realframe.texture_bytes=691200`
- `gpu.d2.realframe.texture_write_rc=0`
- `gpu.d2.realframe.texture_desc_write_rc=0`
- `gpu.d2.realframe.pm4_dwords=409`
- `gpu.d2.realframe.sync_rc=0`
- `gpu.d2.realframe.submit_rc=0`
- `gpu.d2.realframe.wait_rc=0`
- `gpu.d2.realframe.retired_timestamp=1`
- `gpu.d2.realframe.readback_sync_rc=0`
- `gpu.d2.realframe.linear_readback_changed_count=16384`
- `gpu.d2.realframe.linear_readback_bbox_found=1`
- `gpu.d2.realframe.linear_readback_bbox=0,0,127,127`
- `gpu.d2.realframe.output_dark_count=8195`
- `gpu.d2.realframe.output_light_count=8189`
- `gpu.d2.realframe.output_other_count=0`
- `gpu.d2.realframe.texture_bbox_sample_count=64`
- `gpu.d2.realframe.texture_bbox_sample_match_count=64`
- `gpu.d2.realframe.texture_bbox_sample_mismatch_count=0`
- `gpu.d2.realframe.realframe_bbox_sample_count=64`
- `gpu.d2.realframe.realframe_bbox_sample_match_count=64`
- `gpu.d2.realframe.realframe_bbox_sample_mismatch_count=0`
- `gpu.d2.realframe.destroy_rc=0`
- `gpu.d2.realframe.close_rc=0`
- `gpu.d2.realframe.total_elapsed_ms=241`
- `A90P1 END seq=7 cmd=gpu rc=0 errno=0 duration_ms=256 flags=0x0 status=ok`

## Kernel Log Check

Focused dmesg tail filter:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --input-mode slow --timeout 120 \
  busybox sh -c "dmesg | tail -n 250 | grep -Ei 'kgsl|gpu|adreno|a6xx|a640|iommu|smmu|fault|hang|snapshot|timeout|opcode|page fault|gmu' || true"
```

The focused tail contained no GPU fault, hang, snapshot, opcode, SMMU/IOMMU, or page-fault signature. It showed the expected first-use `a640_zap` load/reset lines and an unrelated modem firmware wait timeout.

## Conclusion

V3311 closes D2. A real SD-cache Bad Apple frame is now the texture source, not a synthetic checkerboard. The sampled/scaled readback proves the D1 texture pipe can consume existing demo frame data through the GPU. The next rung is D3: wire the GPU textured-quad blit into the demo player's present path, present, and measure CPU/fps impact.
