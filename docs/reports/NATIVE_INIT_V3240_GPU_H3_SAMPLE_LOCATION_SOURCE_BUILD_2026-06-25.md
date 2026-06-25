# Native Init V3240 GPU H3 Sample Location Source Build

## Summary

- Cycle: `V3240`
- Track: GPU H3 first-triangle sample-location disable state before H4 readback proof.
- Decision: `v3240-gpu-h3-sample-location-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3240_gpu_h3_sample_location_probe.img`
- Boot SHA256: `9fc11231bc8267174a8ecc20bb7ba7aac77604ea5fdff8eba7fd406eb4b7501b`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3232_gpu_h3_static_context_probe.img`
- Init: `A90 Linux init 0.11.47 (v3240-gpu-h3-sample-location-probe)`

## Included Delta

- Adds the Mesa/freedreno A6xx `sample_locations_disable_stateobj` equivalent to H3: `GRAS_SC_MSAA_SAMPLE_POS_CNTL=0`, `RB_MSAA_SAMPLE_POS_CNTL=0`, and `TPL1_MSAA_SAMPLE_POS_CNTL=0`.
- Keeps the V3238 fresh-boot firmware-class materialize prep and the V3236 H3 r1 shader-output/fullregfootprint=2 candidate active, so this unit isolates the remaining sample-position/static-state gap.
- Records sample-location telemetry with `gpu.h3.draw.sample_location_source=mesa-freedreno-a6xx-fd6-context-sample-location-disable-stateobj` and the three programmed zero values.
- Expects H3 state emission to grow from 88 to 91 register writes and from 223 to 229 PM4 dwords.
- Removes stale preserved-ramdisk DOOM engines before packing V3240 and gates the final boot image at 64MiB to protect the boot partition.
- This tests the last known sample-position/static-state candidate before advancing to H4 interior/exterior readback proof.

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

- `py_compile`: V3240 builder and focused H3 source test.
- `unittest`: V3240 GPU H3 sample-location source contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3240 identity plus Sample Location H3 markers.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-sample-location-probe-candidate`.
