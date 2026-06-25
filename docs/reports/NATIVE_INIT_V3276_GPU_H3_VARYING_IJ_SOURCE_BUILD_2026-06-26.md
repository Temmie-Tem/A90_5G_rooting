# Native Init V3276 GPU H3 Varying IJ Source Build

## Summary

- Cycle: `V3276`
- Track: GPU H3 first-triangle cffdump varying/IJ VPC-linkage probe before H4 readback proof.
- Decision: `v3276-gpu-h3-varying-ij-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3276_gpu_h3_varying_ij_probe.img`
- Boot SHA256: `1cfada71599befc2cd47c5ffb53f1eab4673d5200bbe92c77f8137ed0e86471e`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3268_gpu_h3_raster_mode_probe.img`
- Init: `A90 Linux init 0.11.64 (v3276-gpu-h3-varying-ij-probe)`

## Included Delta

- Keeps the V3274 direct-render/sysmem/rasterizer/output-routing baseline and replaces the H3 constant-FS path with a coherent fd6/cffdump varying path.
- VS now copies VFD `r0.xy` to position output `r2.xy`, writes `r2.zw=(0,1)`, and exposes `r0` as the non-position varying at VPC loc0.
- FS now uses the A640 cffdump-verified `bary.f r0.z/r0.w/r1.x/r1.y` sequence and routes MRT0 from `r0.z`.
- Enables the matching fd6 state as a group: `SP_PS_CNTL_0=0x81500100`, `SP_PS_WAVE_CNTL=3`, `SP_REG_PROG_ID_1=0xfcfcfc00`, `GRAS_CL_INTERP_CNTL=1`, `RB_INTERP_CNTL=0x401`, `VPC_PS_CNTL=0xff01ff04`, `VPC_VS_CNTL=0x00ff0408`, `PC_MODE_CNTL=0x1f`, and `PC_VS_CNTL=8`.
- Emits `SP_PS_OUTPUT[0..7]` with MRT0=`r0.z` and the rest invalid `0xfc`, and emits VFD sideband `CNTL_1..6` invalid-reg defaults so stale sideband state cannot override the vertex attributes.
- Expected PM4 size rises from `292` to `306` dwords; expected 3D state register writes rise from `111` to `118`; VFD draw-local writes rise from `8` to `14`.

## Source Basis

- Local A640 cffdump sysmem triangle uses `SP_PS_CNTL_0=0x81500100`, `SP_PS_WAVE_CNTL=3`, `GRAS_CL_INTERP_CNTL=1`, `RB_INTERP_CNTL=0x401`, `VPC_PS_CNTL=0xff01ff04`, `SP_PS_OUTPUT[0].REG=2`, `SP_VS_OUTPUT[0].REG=0x0f000f08`, and `SP_VS_VPC_DEST[0]=0x00000400`.
- Local Mesa `fd6_program.cc` emits the corresponding PS input state from `emit_fs_inputs()` when the FS reads `IJ_PERSP_PIXEL` and has varyings.
- The shader bytes are checked by the updated H3 shader audit using the local Mesa `ir3-disasm` path when present.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3276 builder, shader audit, and focused source contract tests.
- `unittest`: V3276 GPU H3 varying/IJ source contract and H3 shader-byte audit.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3276 identity plus varying/IJ telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-varying-ij-probe-candidate`.
