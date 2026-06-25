# Native Init V3259 GPU H3 Visibility Packets Source Build

## Summary

- Cycle: `V3259`
- Track: GPU H3 first-triangle sysmem-prep ordering before H4 readback proof.
- Decision: `v3259-gpu-h3-visibility-packets-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3259_gpu_h3_visibility_packets_probe.img`
- Boot SHA256: `48854bdd6d11d658254c364456f55e794c247484cb0b8f199065a9354f95f02a`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3257_gpu_h3_vpc_so_override_probe.img`
- Init: `A90 Linux init 0.11.56 (v3259-gpu-h3-visibility-packets-probe)`

## Included Delta

- Keeps the V3257 shader payload, direct-render marker, A640 sysmem RB_CCU value, sysmem bin controls, pre-draw cache invalidation, draw-local `SP_UPDATE_CNTL=0x0000009f`, and `VPC_SO_OVERRIDE(false)`.
- Adds Mesa sysmem-prep packets after the direct-render marker and before H3 3D state: `CP_SKIP_IB2_ENABLE_GLOBAL=0`, `CP_SKIP_IB2_ENABLE_LOCAL=1`, and `CP_SET_VISIBILITY_OVERRIDE=1`.
- Expected PM4 size rises from `246` to `252` dwords; expected register writes stay `94`.
- Removes the preserved V3257 DOOM engine entry before packing V3259 to keep the boot image under the 64MiB gate.

## Source Basis

- Local Mesa sysmem prep: `/tmp/a90-mesa-h3-sparse/src/gallium/drivers/freedreno/a6xx/fd6_gmem.cc` (`fd6_emit_sysmem_prep`).
- Local Mesa PM4 XML: `/tmp/a90-mesa-h3-sparse/src/freedreno/registers/adreno/adreno_pm4.xml` (`CP_SKIP_IB2_ENABLE_GLOBAL=0x1d`, `CP_SKIP_IB2_ENABLE_LOCAL=0x23`, `CP_SET_VISIBILITY_OVERRIDE=0x64`).
- V3258 live result left these sysmem-prep packets as the next concrete Mesa/H3 command-stream mismatch.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3259 builder and shader audit.
- `unittest`: V3259 GPU H3 visibility-packets source contract and H3 source compatibility tests.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3259 identity plus visibility packet telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS before commit.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-visibility-packets-probe-candidate`.
