# Native Init V3226 GPU H3 Shader Mode Source Build

## Summary

- Cycle: `V3226`
- Track: GPU first-triangle H3.7: keep the V3224 shader/SP/raster/VPC/MRT path and add Mesa's shader mode registers.
- Decision: `v3226-gpu-h3-shader-mode-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3226_gpu_h3_shader_mode_probe.img`
- Boot SHA256: `99cf5b0f15d1cc508bfe5fa0968a0578a8ae4dbc731428b31ef9c6c37129d394`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3224_gpu_h3_mrt_component_mask_probe.img`
- Init: `A90 Linux init 0.11.40 (v3226-gpu-h3-shader-mode-probe)`

## Included Delta

- Keeps the V3224 H3 command envelope, VFD state, direct non-indexed `CP_DRAW_INDX_OFFSET`, timeout guard, readback telemetry, hand-encoded shader payloads, SP CNTL0 values, GRAS/RB coverage defaults, VPC linkage sentinels, and full RT0 component mask.
- Adds Mesa-derived shader mode setup before the VS/FS program registers: `SP_MODE_CNTL=0x00000005` and `TPL1_MODE_CNTL=0x000000a2` from `fd6_program.cc::emit_shader_regs()`.
- Removes stale preserved-ramdisk DOOM engines before packing V3226 and gates the final boot image at 64MiB to protect the boot partition.
- This tests a bounded shader execution mode gap; H4 still requires live readback interior/exterior proof.

## Source Basis

- Mesa ir3 ISA documentation: `https://docs.mesa3d.org/drivers/freedreno/ir3-notes.html`.
- Mesa ir3 cat0 ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3-cat0.xml`.
- Mesa ir3 cat1 ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3-cat1.xml`.
- Mesa ir3 root ISA XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/isa/ir3.xml`.
- A6xx register XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx.xml`.
- A6xx format enum XML: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx_enums.xml`.
- Mesa/freedreno shader program state: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_program.cc` (`emit_shader_regs`).
- Mesa/freedreno draw emission state: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_emit.cc`.
- Mesa/freedreno draw path: `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_draw.cc`.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3226 builder and focused H3 source test.
- `unittest`: V3226 GPU H3 shader-mode source contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3226 identity plus shader-mode H3 markers.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-shader-mode-probe-candidate`.
