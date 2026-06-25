# Native Init V3257 GPU H3 VPC_SO_OVERRIDE Source Build

## Summary

- Cycle: `V3257`
- Track: GPU H3 first-triangle sysmem-prep ordering before H4 readback proof.
- Decision: `v3257-gpu-h3-vpc-so-override-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3257_gpu_h3_vpc_so_override_probe.img`
- Boot SHA256: `c308eee87756e5417b6b356a83c4c9c3721b056b4b9f37797b2a3269596db7e1`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3255_gpu_h3_sysmem_bin_control_probe.img`
- Init: `A90 Linux init 0.11.55 (v3257-gpu-h3-vpc-so-override-probe)`

## Included Delta

- Keeps the V3255 shader payload, direct-render marker, A640 sysmem RB_CCU value, sysmem bin controls, pre-draw cache invalidation, and draw-local `SP_UPDATE_CNTL=0x0000009f`.
- Changes `VPC_SO_OVERRIDE` from `0x00000001` to Mesa sysmem prep's `0x00000000` (`VPC_SO_OVERRIDE(false)`).
- Removes the preserved V3255 DOOM engine entry before packing V3257 to keep the boot image under the 64MiB gate.

## Source Basis

- Local Mesa sysmem prep: `/tmp/a90-mesa-h3-sparse/src/gallium/drivers/freedreno/a6xx/fd6_gmem.cc` (`fd6_emit_sysmem_prep`, `VPC_SO_OVERRIDE(CHIP, false)`).
- Local Mesa register XML: `/tmp/a90-mesa-h3-sparse/src/freedreno/registers/adreno/a6xx.xml` (`VPC_SO_OVERRIDE`, offset `0x9306`).
- V3256 live report identified current H3 `vpc_so_override=0x1` as a remaining concrete sysmem-prep mismatch.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3257 builder and shader audit.
- `unittest`: V3257 GPU H3 VPC_SO_OVERRIDE source contract and H3 source compatibility tests.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3257 identity plus VPC_SO_OVERRIDE telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.
- `git diff --check`: PASS before commit.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-vpc-so-override-probe-candidate`.
