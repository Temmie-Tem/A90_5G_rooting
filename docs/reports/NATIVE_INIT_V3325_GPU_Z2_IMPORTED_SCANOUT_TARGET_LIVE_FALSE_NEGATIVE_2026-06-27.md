# Native Init V3325 GPU Z2 Imported Scanout Target Live False Negative

- Cycle: `V3325`
- Decision: `v3325-gpu-z2-imported-scanout-target-live-functional-pass-gate-false-negative`
- Init: `A90 Linux init 0.11.93 (v3325-gpu-z2-imported-scanout-target)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3325_gpu_z2_imported_scanout_target.img`
- Boot SHA256: `3c0d2180627c6fd35f8997e5a720931bb44c3793e83929a5ad66f8b6dd341112`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Precondition: rollback images re-confirmed before flash; no forbidden partition path used.
- Flash result: write/readback SHA matched the exact V3325 artifact.
- Post-flash health: `version` and `selftest verbose` passed; `selftest fail=0`.
- First probe attempt returned `rc=-16 busy` because the menu was active; `hide` cleared the menu.

## Live Probe

- Command: `gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode`
- Result marker: `gpu.z2.import.result=z2-imported-scanout-render-target-failed`
- Result rc: `-5`
- Child status: `0x100`

## Functional Evidence

- DRM msm scanout GEM create: `drm.msm_gem_new_rc=0`
- PRIME export: `drm.prime_export_rc=0`
- KMS framebuffer attach: `drm.addfb2_rc=0`
- KGSL dma-buf import/info: `kgsl.import_rc=0`, `kgsl.info_rc=0`
- Imported GPU address: `gpuaddr=0x500300000`
- Render: `gpu_create_rc=0`, `render_rc=0`, `pm4_dwords=409`
- Changed pixels: `changed_count=691200`
- Semantic sample: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- No KMS copy or present was attempted.
- Cleanup: `rmfb_rc=0`, `close_drm_handle_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest fail=0`

## Diagnosis

The live render/import path functionally passed, but the pass predicate required `summary.result_rc == 0` before the child process assigned the final result. Since `summary.result_rc` was still initialized to `-EIO`, the command reported failure even though the objective metrics were all passing.

V3326 fixes only that pass-gate self-reference and keeps the render path unchanged.

## Safety

- KMS present was not attempted in this rung.
- KMS copy was not attempted in this probe.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
