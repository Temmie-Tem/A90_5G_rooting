# Native Init V3330 GPU Z3 KMS Dumb Imported Scanout Live EINVAL

- Cycle: `V3330`
- Decision: `v3330-gpu-z3-kms-dumb-imported-scanout-live-einval`
- Init: `A90 Linux init 0.11.98 (v3330-gpu-z3-kms-dumb-imported-scanout)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3330_gpu_z3_kms_dumb_imported_scanout.img`
- Boot SHA256: `1eae88dd18399bc98061f1fbb68b209884bbe59e5788b096fb7b320e756e9240`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3330 artifact.
- Post-flash version: `A90 Linux init 0.11.98 (v3330-gpu-z3-kms-dumb-imported-scanout)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- KMS dumb target was used: `buffer_kind=1`, `dumb_create_rc=0`, `pitch=3840`, `size=2764800`, `dumb_map_offset_rc=0`
- PRIME export, `ADDFB2`, KGSL import/info, and GPU render all passed.
- Render semantic proof: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Plane properties were available: `atomic_props_rc=0`, `atomic_prop_count=34`
- Plane selected: `plane_id=84`, `compatible=2`, `idle_xbgr=1`
- Cleanup: `rmfb_rc=0`, `dumb_destroy_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- Atomic plane commit returned `kms.atomic_commit_rc=-22`.
- Legacy fallback returned `kms.present_rc=-22`.
- This ruled out DRM msm GEM allocation as the direct cause; a KMS dumb buffer imported into KGSL also renders correctly but is not accepted by the selected plane.

## Follow-Up

V3331 filters for overlay planes rather than accepting the first idle XBGR-compatible plane.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
