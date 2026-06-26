# Native Init V3302 GPU Compute C2 Pattern Source Build

## Summary

- Cycle: `V3302`
- Track: GPU compute demo C2, 128x128 visible-pattern compute readback probe.
- Decision: `v3302-gpu-compute-c2-pattern-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3302_gpu_compute_c2_pattern_probe.img`
- Boot SHA256: `3f437360d9c428548fb1d89dfa90d56091313375c0b04578c45d95021d43af5a`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3268_gpu_h3_raster_mode_probe.img`
- Init: `A90 Linux init 0.11.76 (v3302-gpu-compute-c2-pattern-probe)`

## Included Delta

- Embeds the V3302 verified FD640 workgroup-id pattern CS words in native-init.
- Adds `gpu c2-compute-pattern-probe` with KGSL cmd/shader/UAV/descriptor/event objects.
- Emits the Mesa computerator-style `SP_CS_*`, `LOAD_STATE6` shader/constants/UAV, `RM6_COMPUTE`, and `CP_EXEC_CS` sequence.
- Verifies the 16384-word 128x128 UAV readback contract: `buf[i] == i`.

## Safety

- KGSL userspace path only; no KMS present in C2.
- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, or forbidden partition work.
- Boot partition only through `native_init_flash.py` in the live step.

## Validation

- `py_compile`: V3302 builder and focused source test.
- `unittest`: V3302 C2 source contract plus V3302 shader-byte coverage.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3302 identity plus C2 compute readback telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Shader SHA256: `9259cd6e225aba4d1e86fb88527494404617b2aaf753c948379ade2edb18a6d1`
- ASM SHA256: `1f7f223c66a97975e416dce96b0a960933b7fa21b7bf4c6d380b3eb63e31b0d6`
- Candidate type: `gpu-compute-c2-pattern-probe-candidate`.
