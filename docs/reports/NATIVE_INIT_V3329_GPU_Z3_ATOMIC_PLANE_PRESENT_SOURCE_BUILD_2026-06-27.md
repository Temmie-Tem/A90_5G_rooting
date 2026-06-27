# Native Init V3329 GPU Z3 Atomic Plane Present Source Build

- Cycle: `V3329`
- Decision: `v3329-gpu-z3-atomic-plane-present-source-build-pass`
- Init: `A90 Linux init 0.11.97 (v3329-gpu-z3-atomic-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3329_gpu_z3_atomic_plane_present.img`
- Boot SHA256: `9d198b815ff489aa71a07f6763396f2ea03c3563aac748f72854a3b7252efb24`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3328_gpu_z3_kms_master_fd_plane_present.img`

## Change

- Fixes the V3328 Z3 legacy `SETPLANE` `-22` path by fetching plane atomic properties and trying `DRM_IOCTL_MODE_ATOMIC` first.
- Keeps the V3328 KMS master fd fix and leaves legacy `DRM_IOCTL_MODE_SETPLANE` as a fallback if atomic commit is unavailable.
- The GPU render/import path remains unchanged: DRM msm scanout GEM -> PRIME -> KGSL dma-buf import -> monitor graph render -> semantic readback -> direct plane present.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires the Z2 imported render-target proof, KMS plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/GEM cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3329 builder and focused source test.
- Unit tests: V3329 focused source contract plus Z3/Z2 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3329 identity plus Z3 atomic plane-present telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-atomic-plane-present-candidate`.
