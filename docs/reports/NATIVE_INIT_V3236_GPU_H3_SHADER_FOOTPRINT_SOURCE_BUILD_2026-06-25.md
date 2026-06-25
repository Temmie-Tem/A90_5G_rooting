# Native Init V3236 GPU H3 Shader Footprint Source Build

## Summary

- Cycle: `V3236`
- Track: GPU first-triangle H3.12: keep the V3234 r1 shader-output split and raise VS/PS full register footprint to cover r1.
- Decision: `v3236-gpu-h3-shader-footprint-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3236_gpu_h3_shader_footprint_probe.img`
- Boot SHA256: `f998a8a8adfb6d66da8163bfe53fae9020bdb5328379bb3bcffa08239319b3db`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3232_gpu_h3_static_context_probe.img`
- Init: `A90 Linux init 0.11.45 (v3236-gpu-h3-shader-footprint-probe)`

## Included Delta

- Keeps the V3234 hand-assembled r1 shader output split: VFD writes input `r0.xy`, VS outputs clip position through `r1.xyzw`, FS writes color through `r1.x`, and `SP_VS_OUTPUT_REG0`/`SP_PS_OUTPUT_REG0` point at regid `0x04`.
- Raises `GPU_H3_SP_FULLREGFOOTPRINT` from `1` to `2`, producing `SP_VS_CNTL_0=0x00100100` and `SP_PS_CNTL_0=0x81000100`, so the shader processor allocation covers r1.
- Records the Mesa source basis as `fd6_program.cc::emit_vpc()` and `emit_fs_outputs()`, where VS/FS output regids are programmed through SP/VPC maps rather than implicit shader terminator bits.
- Removes stale preserved-ramdisk DOOM engines before packing V3236 and gates the final boot image at 64MiB to protect the boot partition.
- This tests whether the V3234 timeout was caused by r1 output with the old `FULLREGFOOTPRINT=1`; H4 still requires live readback interior/exterior proof.

## Source Basis

- Mesa ir3 ISA documentation: `https://docs.mesa3d.org/drivers/freedreno/ir3-notes.html`.
- Mesa ir3 cat0 ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3-cat0.xml`.
- Mesa ir3 cat1 ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3-cat1.xml`.
- Mesa ir3 root ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3.xml`.
- A6xx register XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx.xml`.
- A6xx format enum XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx_enums.xml`.
- Mesa/freedreno shader program state: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_program.cc` (`emit_shader_regs`, `emit_fs_inputs`, `emit_vpc`).
- Mesa/freedreno draw emission state: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_emit.cc`.
- Mesa/freedreno draw path: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_draw.cc`.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3236 builder and focused H3 source test.
- `unittest`: V3236 GPU H3 shader-footprint source contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3236 identity plus Shader Footprint H3 markers.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-shader-footprint-probe-candidate`.
