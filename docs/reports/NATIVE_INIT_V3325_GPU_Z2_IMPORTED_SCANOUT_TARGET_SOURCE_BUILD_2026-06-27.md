# Native Init V3325 GPU Z2 Imported Scanout Target Source Build

- Cycle: `V3325`
- Decision: `v3325-gpu-z2-imported-scanout-target-source-build-pass`
- Init: `A90 Linux init 0.11.93 (v3325-gpu-z2-imported-scanout-target)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3325_gpu_z2_imported_scanout_target.img`
- Boot SHA256: `3c0d2180627c6fd35f8997e5a720931bb44c3793e83929a5ad66f8b6dd341112`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3321_gpu_m3_hold_timeout_budget.img`

## Change

- Adds `gpu z2-imported-scanout-target-probe [--timeout-ms N] [--materialize-devnode]`.
- Creates a DRM msm `MSM_BO_SCANOUT|MSM_BO_WC` linear GEM, exports it as PRIME, attaches it as an XBGR8888 KMS FB with `ADDFB2`, imports the same dma-buf into KGSL, then renders the M3 textured monitor graph into that imported scanout GEM.
- The probe intentionally does not copy to the existing KMS dumb framebuffer and does not present/pageflip yet; it proves the render target is shared and scanout-eligible before the Z3 pageflip step.

## Validation Contract

- Command: `gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode`
- PASS requires `gpu.z2.import.result=z2-imported-scanout-render-target-pass`, `changed_count>0`, semantic match count `64`, semantic output-other count `0`, KGSL import success, KMS `ADDFB2` success, no KMS copy, no KMS present, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3325 builder and focused source test.
- Compile: focused AArch64 native-init compile with existing baseline warnings only.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3325 identity plus Z2 imported scanout target telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Z2 baseline: `v3324-z2-kgsl-dmabuf-import-preflight-pass`
- Candidate type: `gpu-z2-imported-scanout-target-candidate`.
