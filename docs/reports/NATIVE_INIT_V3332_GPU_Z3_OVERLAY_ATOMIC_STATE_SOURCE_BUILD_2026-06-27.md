# Native Init V3332 GPU Z3 Overlay Atomic State Source Build

- Cycle: `V3332`
- Decision: `v3332-gpu-z3-overlay-atomic-state-source-build-pass`
- Init: `A90 Linux init 0.11.100 (v3332-gpu-z3-overlay-atomic-state)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3332_gpu_z3_overlay_atomic_state.img`
- Boot SHA256: `cd61b360eab962b26c900cd24d938695feb22ced8379c69a2710a195e6cf13b4`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3331_gpu_z3_overlay_plane_filter.img`

## Change

- Keeps the V3331 overlay-plane filter and V3330 KMS dumb imported scanout target.
- Extends the atomic plane commit payload with optional `zpos=1`, `alpha=0xffff`, and `rotation=DRM_MODE_ROTATE_0` when those properties exist.
- Adds telemetry for optional atomic state property IDs and count.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires KMS dumb create/map, PRIME export, KGSL import, GPU render semantic proof, overlay plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/dumb cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3332 builder and focused source test.
- Unit tests: V3332 focused source contract plus Z3 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3332 identity plus optional atomic state telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-overlay-atomic-state-candidate`.
