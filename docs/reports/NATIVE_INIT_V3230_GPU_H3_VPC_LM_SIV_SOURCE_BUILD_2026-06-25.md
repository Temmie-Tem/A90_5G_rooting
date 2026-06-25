# Native Init V3230 GPU H3 VPC LM SIV Source Build

## Summary

- Cycle: `V3230`
- Track: GPU first-triangle H3.9: keep the V3228 shader/SP/raster/VPC/MRT/fragment-input path and add Mesa's VPC LM/SIV linkage state.
- Decision: `v3230-gpu-h3-vpc-lm-siv-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3230_gpu_h3_vpc_lm_siv_probe.img`
- Boot SHA256: `af1fb128ab0f8983745855e45045fddd648e1e37e38e4bdd89731833a4cfbad4`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3228_gpu_h3_fragment_input_probe.img`
- Init: `A90 Linux init 0.11.42 (v3230-gpu-h3-vpc-lm-siv-probe)`

## Included Delta

- Keeps the V3228 H3 command envelope, VFD state, direct non-indexed `CP_DRAW_INDX_OFFSET`, timeout guard, readback telemetry, hand-encoded shader payloads, SP CNTL0 values, GRAS/RB coverage defaults, VPC linkage sentinels, full RT0 component mask, shader-mode setup, and fragment-input defaults.
- Adds Mesa-derived VPC LM/SIV state for the current position-only linkage: `VPC_VARYING_LM_TRANSFER_CNTL[0..3]={0xfffffff0,0xffffffff,0xffffffff,0xffffffff}`, `VPC_VS_SIV_CNTL=0x0000ffff`, `VPC_VS_SIV_CNTL_V2=0x0000ffff`, and `GRAS_SU_VS_SIV_CNTL=0` from `fd6_program.cc::emit_vpc()`.
- Removes stale preserved-ramdisk DOOM engines before packing V3230 and gates the final boot image at 64MiB to protect the boot partition.
- This tests a bounded VPC linkage/SIV state gap; H4 still requires live readback interior/exterior proof.

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

- `py_compile`: V3230 builder and focused H3 source test.
- `unittest`: V3230 GPU H3 vpc-lm-siv source contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3230 identity plus VPC LM/SIV H3 markers.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-vpc-lm-siv-probe-candidate`.
