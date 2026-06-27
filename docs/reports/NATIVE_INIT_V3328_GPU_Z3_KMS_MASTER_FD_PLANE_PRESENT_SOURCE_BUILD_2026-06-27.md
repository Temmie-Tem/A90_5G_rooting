# Native Init V3328 GPU Z3 KMS Master FD Plane Present Source Build

- Cycle: `V3328`
- Decision: `v3328-gpu-z3-kms-master-fd-plane-present-source-build-pass`
- Init: `A90 Linux init 0.11.96 (v3328-gpu-z3-kms-master-fd-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3328_gpu_z3_kms_master_fd_plane_present.img`
- Boot SHA256: `fc17c9792b9477270e1e5479702ab09a418e96a5589ec17c787add7ce71fa392`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3327_gpu_z3_imported_scanout_plane_present.img`

## Change

- Fixes the V3327 Z3 plane-present failure by exposing `a90_kms_drm_fd()` and reusing the KMS master fd for the DRM msm GEM, `ADDFB2`, and `DRM_IOCTL_MODE_SETPLANE` calls.
- V3327 selected a valid idle XBGR8888 plane but used a newly opened non-master DRM fd for `SETPLANE`, which returned `-13` (`EACCES`).
- The GPU render/import path remains unchanged: DRM msm scanout GEM -> PRIME -> KGSL dma-buf import -> monitor graph render -> semantic readback -> direct plane present.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires the Z2 imported render-target proof, KMS plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/GEM cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3328 builder and focused source test.
- Unit tests: V3328 focused source contract plus V3327/V3326/V3325 source contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3328 identity plus Z3 KMS-master-fd telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-kms-master-fd-plane-present-candidate`.
