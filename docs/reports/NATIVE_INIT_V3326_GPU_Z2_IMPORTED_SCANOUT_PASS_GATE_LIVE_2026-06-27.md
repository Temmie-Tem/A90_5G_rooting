# Native Init V3326 GPU Z2 Imported Scanout Pass Gate Live

- Cycle: `V3326`
- Decision: `v3326-gpu-z2-imported-scanout-pass-gate-live-pass`
- Init: `A90 Linux init 0.11.94 (v3326-gpu-z2-imported-scanout-pass-gate)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3326_gpu_z2_imported_scanout_pass_gate.img`
- Boot SHA256: `9a63d1f1c8c2ad8aac6cdf63232d71466b2bcf97b5bec5ad7fb62f45601d39d4`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Rollback precondition: V2321, V2237, and V48 rollback images were present before flash.
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3326 artifact.
- Post-flash version: `A90 Linux init 0.11.94 (v3326-gpu-z2-imported-scanout-pass-gate)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode`
- Result marker: `gpu.z2.import.result=z2-imported-scanout-render-target-pass`
- Result rc: `0`
- Child status: `0x0`
- Elapsed: `39525781ns`

## Z2 Evidence

- Buffer: DRM msm scanout GEM, `960x720`, stride `3840`, bytes `2764800`, format `XBGR8888`
- DRM open: `0`
- DRM GEM create: `drm.msm_gem_new_rc=0`, handle `1`
- DRM mmap offset: `drm.offset_rc=0`
- PRIME export: `drm.prime_export_rc=0`
- KMS framebuffer attach: `drm.addfb2_rc=0`, `fb_id=30`
- KGSL dma-buf import/info: `kgsl.import_rc=0`, `kgsl.info_rc=0`
- KGSL imported target: `gpuaddr=0x500300000`, size `2764800`, flags `0x140080`, `va_len=2764800`
- Render: `gpu_create_rc=0`, `render_rc=0`, `pm4_dwords=409`
- Monitor graph: `graph_pixels_set=2178`, `graph_points=2`
- Changed pixels: `changed_count=691200`
- Semantic sample: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Timing: `texture_us=3653`, `gpu_wait_us=714`, `readback_us=4`, `sample_us=34694`
- No copy/present: `kms_copy_attempted=0`, `kms_present_attempted=0`
- Cleanup: `rmfb_rc=0`, `close_drm_handle_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Decision

Z2 is closed: the same KMS-acceptable scanout-linear DRM GEM can be imported into KGSL and used as the GPU render target with correct readback semantics, without the existing KMS CPU-copy present path.

The next rung is Z3: page-flip/present this imported framebuffer directly, hold it for operator visual confirmation, and record the CPU-copy removal or latency delta before closing the GPU epic.

## Safety

- Flash used only `native_init_flash.py`.
- Persistent device write was limited to the boot partition.
- KMS present was intentionally not attempted in this rung.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
