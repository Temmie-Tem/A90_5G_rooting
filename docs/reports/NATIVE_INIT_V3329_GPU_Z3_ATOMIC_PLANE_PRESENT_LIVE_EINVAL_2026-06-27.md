# Native Init V3329 GPU Z3 Atomic Plane Present Live EINVAL

- Cycle: `V3329`
- Decision: `v3329-gpu-z3-atomic-plane-present-live-einval`
- Init: `A90 Linux init 0.11.97 (v3329-gpu-z3-atomic-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3329_gpu_z3_atomic_plane_present.img`
- Boot SHA256: `9d198b815ff489aa71a07f6763396f2ea03c3563aac748f72854a3b7252efb24`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3329 artifact.
- Post-flash version: `A90 Linux init 0.11.97 (v3329-gpu-z3-atomic-plane-present)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- KMS master fd path was used: `kms.begin_rc=0`, `base_present_rc=0`, `info_initialized=1`
- DRM msm GEM, PRIME export, `ADDFB2`, KGSL import/info, and GPU render all passed.
- Render semantic proof: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Plane properties were available: `atomic_props_rc=0`, `atomic_prop_count=34`
- Plane selected: `plane_id=84`, `compatible=2`, `idle_xbgr=1`
- Cleanup: RMFB/handle/prime/fd all returned `0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- Atomic plane commit returned `kms.atomic_commit_rc=-22`.
- Legacy fallback also returned `kms.present_rc=-22`.
- V3329 closed the "legacy SETPLANE only" gap, but the selected plane/fb/rect tuple was still rejected by KMS.

## Follow-Up

V3330 switches the render target to a KMS dumb scanout buffer exported to KGSL, removing msm-GEM-specific scanout layout as the next variable.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
