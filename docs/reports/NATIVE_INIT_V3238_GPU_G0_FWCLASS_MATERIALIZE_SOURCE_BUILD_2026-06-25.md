# Native Init V3238 GPU G0 Fwclass Materialize Prep Source Build

## Summary

- Cycle: `V3238`
- Track: GPU G0/H3 validation preflight: make KGSL materialization run firmware-class prep before devnode/open.
- Decision: `v3238-gpu-h3-fwclass-materialize-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3238_gpu_g0_fwclass_materialize_prep_probe.img`
- Boot SHA256: `8633a52394949247ca541b0bdd5597931ac1d79b00ce5d6d194233c12085dfdb`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3232_gpu_h3_static_context_probe.img`
- Init: `A90 Linux init 0.11.46 (v3238-gpu-g0-fwclass-materialize-prep-probe)`

## Included Delta

- Adds firmware-class prep to `gpu_g0_materialize_devnode()`: every `--materialize-devnode` KGSL probe now verifies staged SQE/GMU firmware, copies ZAP pieces to the runtime cache, and writes `firmware_class.path` to `/cache/a90-runtime/pkg/gpu-g0-fw` before opening KGSL.
- Records the prep attempt in materialize telemetry with `gpu.g0.materialize.fwclass_prepare_attempted=1` and `gpu.g0.materialize.fwclass_prepare_rc=<rc>`.
- Keeps the V3236 H3 r1 shader-output/fullregfootprint=2 candidate unchanged apart from the scope string, so this unit isolates the fresh-boot firmware visibility preflight hole.
- Removes stale preserved-ramdisk DOOM engines before packing V3238 and gates the final boot image at 64MiB to protect the boot partition.
- This tests whether fresh boot H3 can run without a separate manual `gpu g0-fwclass-prepare`; H4 still requires live readback interior/exterior proof.

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

- `py_compile`: V3238 builder and focused H3 source test.
- `unittest`: V3238 GPU H3 fwclass-materialize source contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3238 identity plus Fwclass Materialize H3 markers.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-g0-fwclass-materialize-prep-probe-candidate`.
