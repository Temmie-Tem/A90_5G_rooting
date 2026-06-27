# Native Init V3327 GPU Z3 Imported Scanout Plane Present Live EACCES

- Cycle: `V3327`
- Decision: `v3327-gpu-z3-imported-scanout-plane-present-live-eacces`
- Init: `A90 Linux init 0.11.95 (v3327-gpu-z3-imported-scanout-plane-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3327_gpu_z3_imported_scanout_plane_present.img`
- Boot SHA256: `891ea3ae86eba09f4384a034a6ef24edafae5051f72bdd80c1c3082fbda13240`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3327 artifact.
- Post-flash version: `A90 Linux init 0.11.95 (v3327-gpu-z3-imported-scanout-plane-present)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`
- Bridge note: the first post-flash selftest had serial prompt noise; restarting `a90_bridge.py` produced clean `version` and `selftest` output.

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-13`
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

- KMS plane present failed: `kms.present_rc=-13`
- Plane disable also returned `-13` because the same non-master fd was used for the mode operation.
- Diagnosis: V3327 created the DRM framebuffer on a newly opened `/dev/dri/card0` fd, while the KMS master fd was already owned by `a90_kms`. `DRM_IOCTL_MODE_SETPLANE` on the non-master fd returned `EACCES`.

## Follow-Up

V3328 exposes `a90_kms_drm_fd()` and reuses that master fd for the DRM msm GEM, `ADDFB2`, and `SETPLANE` calls.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
