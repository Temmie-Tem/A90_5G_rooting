# Native Init V3311 GPU 2D D2 Realframe Texture Source Build

## Summary

- Cycle: `V3311`
- Track: GPU accelerated 2D D2, SD-cache real frame texture sample readback.
- Decision: `v3311-gpu-2d-d2-realframe-texture-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3311_gpu_2d_d2_realframe_texture_probe.img`
- Boot SHA256: `1f70bbb99e87c20d2c9b9034055801caa6a2daee4fd110125ae3fe4201ad71f6`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3310_gpu_2d_d1_bbox_checkerboard_probe.img`
- Init: `A90 Linux init 0.11.83 (v3311-gpu-2d-d2-realframe-texture-probe)`

## Included Delta

- Adds `gpu d2-realframe-texture-probe` to the native GPU command set.
- Reads the SD cache Bad Apple mono1 A90VSTR1 manifest/stream, default frame `515`, and expands it into a 480x360 RGBA8 texture.
- Reuses the V3310-proven textured quad path: one sampler descriptor, one TEXMEMOBJ descriptor, the V3305 sampled FS, and TILE6_3-to-linear readback.
- Linearizes the rendered target and requires all 64 bbox-local samples to match the expected source-frame bits.

## Real-Frame Gate

- Source preset: `badapple`, SHA256 `9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0`, frame index `515`, geometry `480x360 mono1`.
- PASS requires positive dark/light source counts, positive dark/light output counts, a non-empty `linear_readback_bbox`, `realframe_bbox_sample_count=64`, `realframe_bbox_sample_match_count=64`, and `realframe_bbox_sample_mismatch_count=0`.
- This is readback only. D3 owns wiring the GPU textured blit into the live demo presenter.
- This source/build report records the gate; the live report must record the device-side readback counts.

## Safety

- KGSL userspace readback only; no KMS present in D2.
- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, or forbidden partition work.
- Boot partition only through `native_init_flash.py` in the live step.

## Validation

- `py_compile`: V3311 builder and focused source test.
- `unittest`: V3311 D2 source contract plus V3310 D1 baseline and V3304/V3305 coverage.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3311 identity plus D2 realframe telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Textured FS SHA256: `4e8ad0a934d236149af999619a1fe99690e7b732d2e4ca69a2b345100d8d04a3`
- D0 reference: `v3304-fd6-texture-reference-recon`
- D1 shader gate: `v3305-verified-textured-fs-shader-bytes`
- D1 live baseline: `v3310-d1-bbox-checkerboard-live-pass`
- Candidate type: `gpu-2d-d2-realframe-texture-probe-candidate`.
