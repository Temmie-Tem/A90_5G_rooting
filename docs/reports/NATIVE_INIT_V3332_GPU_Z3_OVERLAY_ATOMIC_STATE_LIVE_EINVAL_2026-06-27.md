# Native Init V3332 GPU Z3 Overlay Atomic State Live EINVAL

- Cycle: `V3332`
- Decision: `v3332-gpu-z3-overlay-atomic-state-live-einval`
- Init: `A90 Linux init 0.11.100 (v3332-gpu-z3-overlay-atomic-state)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3332_gpu_z3_overlay_atomic_state.img`
- Boot SHA256: `cd61b360eab962b26c900cd24d938695feb22ced8379c69a2710a195e6cf13b4`

## Flash And Health

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash result: local SHA, remote pushed SHA, boot write, and boot readback SHA all matched the exact V3332 artifact.
- Post-flash version: `A90 Linux init 0.11.100 (v3332-gpu-z3-overlay-atomic-state)`
- Post-flash health: `selftest pass=12 warn=1 fail=0`

## Live Probe

- Command: `gpu z3-imported-scanout-plane-probe --timeout-ms 60000 --hold-ms 12000 --materialize-devnode`
- Result marker: `gpu.z3.scanout.result=z3-imported-scanout-plane-present-failed`
- Result rc: `-22`
- Child status: `0x100`

## Passed Evidence

- KMS dumb target, PRIME export, `ADDFB2`, KGSL import/info, and GPU render all passed.
- Render semantic proof: `sample_count=64`, `match_count=64`, `exact_match_count=64`, `mismatch_count=0`, `output_other_count=0`
- Overlay plane selected: `plane_id=90`, `compatible=4`, `overlay=1`, `idle_xbgr=1`, `selected_type=0`
- Optional atomic properties were present and included: `atomic_optional_count=3`, `zpos_prop=61`, `alpha_prop=62`, `rotation_prop=91`
- Plane properties were available: `atomic_props_rc=0`, `atomic_prop_count=34`
- Cleanup: `rmfb_rc=0`, `dumb_destroy_rc=0`, `close_prime_rc=0`, `close_drm_fd_rc=0`
- Post-probe health: `selftest pass=12 warn=1 fail=0`

## Failure

- Atomic plane commit returned `kms.atomic_commit_rc=-22`.
- Legacy fallback returned `kms.present_rc=-22`.
- This ruled out missing `zpos`/`alpha`/`rotation` as the direct cause.

## Follow-Up

V3333 parses overlay `IN_FORMATS` and requires `XBGR8888 + LINEAR` where modifier data exists. It also records whether `pixel blend mode` exists.

## Safety

- Device health stayed clean after the failed probe; no rollback was required.
- No PMIC/GDSC/regulator/GPIO/backlight write was introduced.
- No proprietary blob, EGL/GLES/OpenCL path, forbidden partition, or raw flash path was used.
