# Native Init V3270 GPU H3 SP Const / FS Output Source Build

## Summary

- Cycle: `V3270`
- Track: GPU H3 first-triangle shader config and FS output control before H4 readback proof.
- Decision: `v3270-gpu-h3-sp-const-fs-output-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3270_gpu_h3_sp_const_fs_output_probe.img`
- Boot SHA256: `dec8c8f956f75e0d035ec21919e5b2fd2d0fb16a81f191eb1b033d59a0138325`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3268_gpu_h3_raster_mode_probe.img`
- Init: `A90 Linux init 0.11.61 (v3270-gpu-h3-sp-const-fs-output-probe)`

## Included Delta

- Keeps the V3268 shader payload, direct-render marker, visibility packet trio, zero window offsets, CP_SET_MODE(0), A640 sysmem RB_CCU value, sysmem bin controls, pre-draw cache invalidation, draw-local `SP_UPDATE_CNTL=0x0000009f`, `VPC_SO_OVERRIDE(false)`, and triangle raster mode.
- Adds A6xx shader const enables: `SP_VS_CONST_CONFIG=0x100` and `SP_PS_CONST_CONFIG=0x100`.
- Changes `SP_PS_OUTPUT_CNTL` from `0x00000000` to `0xfcfcfc00`, matching fd6 invalid depth/sampmask/stencil regids for a color-only FS.
- Leaves `RB_PS_OUTPUT_CNTL=0`, `RB_PS_MRT_CNTL=1`, and `SP_PS_MRT_CNTL=1`; Mesa/fd6 uses RB flags only when depth/sampmask/stencil are written.
- Expected PM4 size rises from `266` to `270` dwords; expected 3D state register writes stay at `100`.
- Removes the preserved V3268 DOOM engine entry before packing V3270 to keep the boot image under the 64MiB gate.

## Source Basis

- Local Mesa fd6 program path enables `SP_VS_CONST_CONFIG` / `SP_PS_CONST_CONFIG`; the A640 triangle `.rd` summary shows `SP_PS_CONST_CONFIG=0x100` with zero FS constants.
- Local Mesa fd6 FS output path uses invalid register id `0xfc` for absent depth, sample-mask, and stencil-ref outputs; the A640 triangle `.rd` summary shows `SP_PS_OUTPUT_CNTL=0xfcfcfc00`.
- HLSQ round-4 audit: old `HLSQ_CONTROL_*` / `HLSQ_*_CNTL` offsets are not present in the A6xx XML/fd6 program path used locally; A6xx shader payload preload stays through the existing `CP_LOAD_STATE6` packets.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3270 builder and shader audit.
- `unittest`: V3270 GPU H3 SP const/output source contract and H3 source compatibility tests.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3270 identity plus SP const/output telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS before commit.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-sp-const-fs-output-probe-candidate`.
