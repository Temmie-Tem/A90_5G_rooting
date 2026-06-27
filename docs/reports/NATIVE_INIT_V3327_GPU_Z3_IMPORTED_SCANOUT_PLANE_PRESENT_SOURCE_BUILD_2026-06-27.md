# Native Init V3327 GPU Z3 Imported Scanout Plane Present Source Build

- Cycle: `V3327`
- Decision: `v3327-gpu-z3-imported-scanout-plane-present-source-build-pass`
- Init: `A90 Linux init 0.11.95 (v3327-gpu-z3-imported-scanout-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3327_gpu_z3_imported_scanout_plane_present.img`
- Boot SHA256: `891ea3ae86eba09f4384a034a6ef24edafae5051f72bdd80c1c3082fbda13240`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3326_gpu_z2_imported_scanout_pass_gate.img`

## Change

- Adds `gpu z3-imported-scanout-plane-probe [--timeout-ms N] [--hold-ms N] [--materialize-devnode]`.
- Reuses the V3326 DRM msm scanout GEM -> PRIME -> KGSL dma-buf imported render target path, then presents the same `ADDFB2` framebuffer directly on an idle XBGR8888 KMS plane using `DRM_IOCTL_MODE_SETPLANE`.
- The probe clears/presents a black primary base, centers the `960x720` imported framebuffer on the panel without a CPU copy, holds it for operator visual confirmation, then disables the plane before cleanup.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires the Z2 imported render-target proof, KMS plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/GEM cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3327 builder and focused source test.
- Unit tests: V3327 focused source contract plus V3326/V3325 source contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3327 identity plus Z3 imported scanout plane-present telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-imported-scanout-plane-present-candidate`.
