# Native Init V3274 GPU H3 Clip Guardband SU Source Build

## Summary

- Cycle: `V3274`
- Track: GPU H3 first-triangle clip/guardband/SU rasterizer state before H4 readback proof.
- Decision: `v3274-gpu-h3-clip-guardband-su-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3274_gpu_h3_clip_guardband_su_probe.img`
- Boot SHA256: `b9f85b95fda81edd77f2bc121c940275c4122f5842ba929400c7f49b43bdb313`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3268_gpu_h3_raster_mode_probe.img`
- Init: `A90 Linux init 0.11.63 (v3274-gpu-h3-clip-guardband-su-probe)`

## Included Delta

- Keeps the V3272 shader payload, direct-render marker, visibility packet trio, zero window offsets, CP_SET_MODE(0), A640 sysmem RB_CCU value, sysmem bin controls, pre-draw cache invalidation, draw-local `SP_UPDATE_CNTL=0x0000009f`, `VPC_SO_OVERRIDE(false)`, triangle raster mode, SP const enables, `SP_PS_OUTPUT_CNTL=0xfcfcfc00`, `RB_PS_MRT_CNTL=1`, `SP_PS_MRT_CNTL=1`, and SP front-end program-id state.
- Replaces H3's zeroed clip/guardband/SU rasterizer defaults with the direct fd6/cffdump values: `GRAS_CL_CNTL=0xc0`, `GRAS_CL_GUARDBAND_CLIP_ADJ=0x0007fdff`, and `GRAS_SU_CNTL=0x814`.
- Adds the rest of the fd6 rasterizer state emitted with `GRAS_SU_CNTL`: `GRAS_SU_POINT_MINMAX=0xffc00001`, `GRAS_SU_POINT_SIZE=0x10`, and zero `GRAS_SU_POLY_OFFSET_*` registers.
- Re-audits the round-4 HLSQ claim against the local A6xx XML/fd6 sources and does not emit guessed legacy `HLSQ_CONTROL_*` or `HLSQ_*_CNTL` registers; the A6xx program config path here is `SP_*_CONST_CONFIG`, `SP_*_CONFIG`, and `CP_LOAD_STATE6`.
- Leaves interpolation/varying state unchanged because H3's current FS is constant-color and does not use the cffdump reference's `bary.f` inputs.
- Expected PM4 size rises from `282` to `292` dwords; expected 3D state register writes rise from `106` to `111`.
- Removes the preserved V3268 DOOM engine entry before packing V3274 to keep the boot image under the 64MiB gate.

## Source Basis

- Local A6xx XML defines `GRAS_CL_CNTL` at `0x8000`, `GRAS_CL_GUARDBAND_CLIP_ADJ` at `0x8006`, and `GRAS_SU_CNTL` at `0x8090` as A6xx draw registers.
- Local Mesa `fd6_rasterizer.cc` emits `GRAS_CL_CNTL`, `GRAS_SU_CNTL`, point size/minmax, and poly-offset registers as one rasterizer state object.
- Local Mesa `fd6_emit.cc` emits `GRAS_CL_GUARDBAND_CLIP_ADJ` from the current guardband values when viewport/program state is dirty.
- The A640 triangle `.rd` summary confirms `GRAS_CL_CNTL=0xc0`, `GRAS_CL_GUARDBAND_CLIP_ADJ=0x0007fdff`, `GRAS_SU_CNTL=0x814`, `GRAS_SU_POINT_MINMAX=0xffc00001`, and `GRAS_SU_POINT_SIZE=0x10` in a real fd6 draw.
- Local Mesa `fd6_program.cc` and `tu_pipeline.cc` emit A6xx program config through `SP_UPDATE_CNTL`, `SP_*_CONST_CONFIG`, `SP_*_CONFIG`, and `CP_LOAD_STATE6`; the requested legacy `HLSQ_CONTROL_*`/`HLSQ_*_CNTL` draw register block is not present in the local A6xx XML/fd6 draw path.
- Local Mesa `fd6_emit.cc` keeps `RB_PS_OUTPUT_CNTL=0` for a color-only FS and sets `RB_PS_MRT_CNTL=1`/`SP_PS_MRT_CNTL=1`; local `fd6_program.cc` uses invalid `0xfc` regids for absent depth, sample-mask, and stencil-ref outputs.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3274 builder and focused source contract test.
- `unittest`: V3274 GPU H3 clip/guardband/SU source contract and H3 source compatibility tests.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3274 identity plus clip/guardband/SU telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS before commit.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-clip-guardband-su-probe-candidate`.
