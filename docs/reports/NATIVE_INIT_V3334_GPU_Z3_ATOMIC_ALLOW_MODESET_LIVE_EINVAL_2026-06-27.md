# Native Init V3334 GPU Z3 Atomic Allow Modeset Live EINVAL

- Cycle: `V3334`
- Decision: `v3334-gpu-z3-atomic-allow-modeset-live-einval`
- Init: `A90 Linux init 0.11.102 (v3334-gpu-z3-atomic-allow-modeset)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3334_gpu_z3_atomic_allow_modeset.img`
- Boot SHA256: `0d9bdbdf1165b37cabdaa77cbc2f2a91e32a648ecc0f22f29c241882ffdd00c7`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3334 artifact.
- Post-flash version: `A90 Linux init 0.11.102 (v3334-gpu-z3-atomic-allow-modeset)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- KMS dumb target, PRIME export, `ADDFB2`, KGSL import/info, and GPU render all passed.
- Render semantic proof: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Overlay plane selected: `plane_id=90`, `compatible=4`, `overlay=1`, `idle_xbgr=1`, `idle_xbgr_linear=1`, `selected_type=0`
- Modifier telemetry: `selected_linear=1`, `selected_tiled2=0`, `selected_tiled3=0`, `selected_compressed=0`, `in_formats_rc=-61`
- Atomic flags telemetry: `atomic_flags=0x400` (`DRM_MODE_ATOMIC_ALLOW_MODESET`)
- Atomic optional telemetry: `atomic_optional_count=3`, `zpos_prop=61`, `alpha_prop=62`, `rotation_prop=91`, `pixel_blend_prop=0`
- Cleanup: `rmfb_rc=0`, `dumb_destroy_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- Atomic plane commit still returned `kms.atomic_commit_rc=-22`.
- Legacy fallback still returned `kms.present_rc=-22`.
- This ruled out missing `DRM_MODE_ATOMIC_ALLOW_MODESET` as the direct cause.

## Conclusion

The Z2 render/import/readback path is sound. The Z3 overlay attach path is blocked specifically at msm/SDE plane validation, not at GPU rendering, DMA-buf import, framebuffer creation, modifier discovery, optional overlay state, or atomic flags.

## Next Candidate

Stop extending overlay guesses for now. The next bounded unit should try a primary scanout path: render into a full-screen KMS dumb buffer imported into KGSL, then pageflip or set the primary plane with that framebuffer, with the existing KMS framebuffer restored afterward.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
