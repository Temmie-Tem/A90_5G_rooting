# Native Init V3334 GPU Z3 Atomic Allow Modeset Source Build

- Cycle: `V3334`
- Decision: `v3334-gpu-z3-atomic-allow-modeset-source-build-pass`
- Init: `A90 Linux init 0.11.102 (v3334-gpu-z3-atomic-allow-modeset)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3334_gpu_z3_atomic_allow_modeset.img`
- Boot SHA256: `0d9bdbdf1165b37cabdaa77cbc2f2a91e32a648ecc0f22f29c241882ffdd00c7`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3333_gpu_z3_overlay_linear_modifier.img`

## Change

- Keeps the V3333 LINEAR overlay selection and optional atomic state telemetry.
- Sets `DRM_MODE_ATOMIC_ALLOW_MODESET` on the overlay atomic commit.
- Adds `gpu.z3.scanout.kms.atomic_flags=0x...` telemetry for the submitted atomic flags.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires KMS dumb create/map, PRIME export, KGSL import, GPU render semantic proof, LINEAR-capable overlay plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/dumb cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3334 builder and focused source test.
- Unit tests: V3334 focused source contract plus Z3 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3334 identity plus atomic flags telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-atomic-allow-modeset-candidate`.
