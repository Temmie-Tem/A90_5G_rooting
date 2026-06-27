# Native Init V3333 GPU Z3 Overlay Linear Modifier Source Build

- Cycle: `V3333`
- Decision: `v3333-gpu-z3-overlay-linear-modifier-source-build-pass`
- Init: `A90 Linux init 0.11.101 (v3333-gpu-z3-overlay-linear-modifier)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3333_gpu_z3_overlay_linear_modifier.img`
- Boot SHA256: `d374fb84dbd705aa22de1b960452d230b541ced6d68f63e1ed2d3cdd7c34f12f`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3332_gpu_z3_overlay_atomic_state.img`

## Change

- Keeps the V3332 overlay atomic state and V3330 KMS dumb imported scanout target.
- Parses the selected overlay plane `IN_FORMATS` blob and requires `XBGR8888 + DRM_FORMAT_MOD_LINEAR` before scanout.
- Extends optional atomic state with `pixel blend mode=None` when the property exists.
- Adds telemetry for LINEAR/tiled/compressed modifier support and the pixel-blend property ID.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires KMS dumb create/map, PRIME export, KGSL import, GPU render semantic proof, LINEAR-capable overlay plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/dumb cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3333 builder and focused source test.
- Unit tests: V3333 focused source contract plus Z3 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3333 identity plus LINEAR modifier and pixel blend telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-overlay-linear-modifier-candidate`.
