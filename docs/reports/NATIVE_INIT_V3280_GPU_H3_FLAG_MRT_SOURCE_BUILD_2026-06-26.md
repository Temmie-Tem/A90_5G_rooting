# Native Init V3280 GPU H3 flag-MRT Source Build

## Summary

- Cycle: `V3280`
- Track: GPU H3 first-triangle cffdump flag-MRT color-target probe before H4 readback proof.
- Decision: `v3280-gpu-h3-flag-mrt-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3280_gpu_h3_flag_mrt_probe.img`
- Boot SHA256: `e295699879f3bb30bff85cfebaeb46b9c4ffd3909d0289bd882e3b2a9decfc19`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3268_gpu_h3_raster_mode_probe.img`
- Init: `A90 Linux init 0.11.66 (v3280-gpu-h3-flag-mrt-probe)`

## Included Delta

- Keeps the V3278 direct-render/sysmem/rasterizer/varying-IJ/RGBA8 baseline intact.
- Changes H3 MRT0 color target from linear RGBA8 (`RB_MRT0_BUF_INFO=0x30`) to the A640 cffdump draw[2] flag-MRT group: `RB_RENDER_CNTL=0x10010`, `RB_MRT0_BUF_INFO=0x330`, and `RB_COLOR_FLAG_BUFFER[0]`.
- Adds a bounded 4 KiB color-flag BO and explicit telemetry for flag BO address, pitch, and flag readback changed-count.
- Does not emit speculative A6XX HLSQ program-control registers: the local A6XX XML/generated headers expose only HLSQ load-state/static unknowns, and the local cffdump triangle does not show a legacy HLSQ control block.
- Expected PM4 size is `311` dwords; expected 3D state register writes are `121`; VFD draw-local writes remain `14`.

## Source Basis

- Local A640 cffdump draw[2] uses `SP_PS_MRT[0].REG=0x00000030`, `RB_MRT[0].BUF_INFO=0x00000330`, `RB_RENDER_CNTL=0x00010010`, and `RB_COLOR_FLAG_BUFFER[0].PITCH=0x00004001` for the color target.
- Local cffdump and `fd6_program.cc` agree that `RB_PS_OUTPUT_CNTL=0` is normal when depth/samplemask/stencil are not written, while `SP_PS_OUTPUT_CNTL=0xfcfcfc00` and `RB/SP_PS_MRT_CNTL=1` are already present in H3.
- The shader bytes and current flag-MRT color-target contract are checked by the updated H3 shader audit using the local Mesa `ir3-disasm` path when present.

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- Child-only KGSL open/ioctl; parent remains outside KGSL and kills the child on timeout.
- No PMIC/GDSC/regulator/GPIO write, proprietary blob, full Mesa compiler port, KMS presentation, or forbidden partition work.

## Validation

- `py_compile`: V3280 builder, shader audit, and focused source contract tests.
- `unittest`: V3280 GPU H3 flag-MRT source contract and H3 shader-byte audit.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3280 identity plus flag-MRT telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-h3-flag-mrt-probe-candidate`.
