# Native Init V3330 GPU Z3 KMS Dumb Imported Scanout Source Build

- Cycle: `V3330`
- Decision: `v3330-gpu-z3-kms-dumb-imported-scanout-source-build-pass`
- Init: `A90 Linux init 0.11.98 (v3330-gpu-z3-kms-dumb-imported-scanout)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3330_gpu_z3_kms_dumb_imported_scanout.img`
- Boot SHA256: `1eae88dd18399bc98061f1fbb68b209884bbe59e5788b096fb7b320e756e9240`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3329_gpu_z3_atomic_plane_present.img`

## Change

- Fixes the V3329 Z3 `DRM_IOCTL_MODE_ATOMIC`/legacy `SETPLANE` `-22` path by using a KMS-native dumb framebuffer as the scanout target.
- Exports that KMS dumb buffer as PRIME, imports it into KGSL, renders the monitor graph directly into it, then presents the same FB on the overlay plane.
- Keeps the V3329 atomic-first plane commit and legacy fallback, with new dumb-buffer telemetry.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires KMS dumb create/map, PRIME export, KGSL import, GPU render semantic proof, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/dumb cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3330 builder and focused source test.
- Unit tests: V3330 focused source contract plus Z3 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3330 identity plus KMS dumb imported scanout telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-kms-dumb-imported-scanout-candidate`.
