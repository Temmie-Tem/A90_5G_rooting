# Native Init V3331 GPU Z3 Overlay Plane Filter Live EINVAL

- Cycle: `V3331`
- Decision: `v3331-gpu-z3-overlay-plane-filter-live-einval`
- Init: `A90 Linux init 0.11.99 (v3331-gpu-z3-overlay-plane-filter)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3331_gpu_z3_overlay_plane_filter.img`
- Boot SHA256: `485e0c6fbbae7b2471848293eb0b0ff107354e4dc3bba0a1706a5e5b4c130268`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3331 artifact.
- Post-flash version: `A90 Linux init 0.11.99 (v3331-gpu-z3-overlay-plane-filter)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- KMS dumb target, PRIME export, `ADDFB2`, KGSL import/info, and GPU render all passed.
- Render semantic proof: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Overlay plane selected: `plane_id=90`, `plane_count=16`, `compatible=4`, `overlay=1`, `idle_xbgr=1`, `selected_type=0`
- Plane properties were available: `atomic_props_rc=0`, `atomic_prop_count=34`
- Cleanup: `rmfb_rc=0`, `dumb_destroy_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- Atomic plane commit returned `kms.atomic_commit_rc=-22`.
- Legacy fallback returned `kms.present_rc=-22`.
- This ruled out accidentally selecting a primary/cursor plane. The failure persists on a real idle overlay plane.

## Follow-Up

V3332 adds optional overlay atomic state (`zpos`, `alpha`, `rotation`) where those properties exist.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
