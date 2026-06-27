# Native Init V3328 GPU Z3 KMS Master FD Plane Present Live SETPLANE EINVAL

- Cycle: `V3328`
- Decision: `v3328-gpu-z3-kms-master-fd-plane-present-live-setplane-einval`
- Init: `A90 Linux init 0.11.96 (v3328-gpu-z3-kms-master-fd-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3328_gpu_z3_kms_master_fd_plane_present.img`
- Boot SHA256: `fc17c9792b9477270e1e5479702ab09a418e96a5589ec17c787add7ce71fa392`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3328 artifact.
- Post-flash version: `A90 Linux init 0.11.96 (v3328-gpu-z3-kms-master-fd-plane-present)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- DRM msm scanout GEM create/export/`ADDFB2`: all `0`
- KGSL dma-buf import/info: all `0`
- Render: `gpu_create_rc=0`, `render_rc=0`, `pm4_dwords=409`
- Changed pixels: `changed_count=691200`
- Semantic sample: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- KMS base: `begin_rc=0`, `base_present_rc=0`, `info_initialized=1`
- KMS plane select: `plane_select_rc=0`, `plane_id=84`, `plane_count=16`, `compatible=2`, `idle_xbgr=1`
- Destination: `60,840 960x720`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- V3328 fixed the V3327 non-master-fd `EACCES`: the failure moved from `-13` to `-22`.
- Legacy `DRM_IOCTL_MODE_SETPLANE` returned `-22` (`EINVAL`) for the selected plane/fb/rect tuple.
- The existing KMS scaled-plane path uses atomic commit first, so V3329 adds atomic plane commit before the legacy fallback.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
