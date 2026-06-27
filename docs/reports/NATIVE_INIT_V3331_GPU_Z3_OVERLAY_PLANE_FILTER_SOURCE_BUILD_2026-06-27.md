# Native Init V3331 GPU Z3 Overlay Plane Filter Source Build

- Cycle: `V3331`
- Decision: `v3331-gpu-z3-overlay-plane-filter-source-build-pass`
- Init: `A90 Linux init 0.11.99 (v3331-gpu-z3-overlay-plane-filter)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3331_gpu_z3_overlay_plane_filter.img`
- Boot SHA256: `485e0c6fbbae7b2471848293eb0b0ff107354e4dc3bba0a1706a5e5b4c130268`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3330_gpu_z3_kms_dumb_imported_scanout.img`

## Change

- Keeps the V3330 KMS dumb scanout target and KGSL import path.
- Fixes plane selection by reading each candidate plane `type` property and choosing only `DRM_PLANE_TYPE_OVERLAY`.
- Adds plane type telemetry: compatible count, overlay count, idle XBGR overlay count, and selected type.

## Validation Contract

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- PASS requires KMS dumb create/map, PRIME export, KGSL import, GPU render semantic proof, overlay plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/dumb cleanup, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3331 builder and focused source test.
- Unit tests: V3331 focused source contract plus Z3 regression contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3331 identity plus overlay-plane-filter telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z3-overlay-plane-filter-candidate`.
