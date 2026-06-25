# Native Init V3241 GPU H3 Sample Location Live Validation

## Summary

- Cycle: `V3241`
- Source build: `V3240`
- Track: GPU H3 first-triangle sample-location disable state.
- Result: PASS for bounded boot/probe safety; H4 not reached.
- Flashed image: `workspace/private/inputs/boot_images/boot_linux_v3240_gpu_h3_sample_location_probe.img`
- Boot SHA256: `9fc11231bc8267174a8ecc20bb7ba7aac77604ea5fdff8eba7fd406eb4b7501b`
- Init: `A90 Linux init 0.11.47 (v3240-gpu-h3-sample-location-probe)`

## Flash Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img`: SHA256 matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Fallback image `boot_linux_v2237_supplicant_terminate_poll.img`: SHA256 matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img`: present.
- Pre-flash resident: `0.11.46 (v3238-gpu-g0-fwclass-materialize-prep-probe)`.
- Pre-flash health: `selftest pass=12 warn=1 fail=0`.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py` only.

## Flash Result

- Local image passed Android boot magic and expected version marker checks.
- Remote pushed image SHA256 matched the local candidate SHA256.
- Boot partition readback prefix SHA256 matched the candidate SHA256.
- Post-reboot native verification passed as `0.11.47 (v3240-gpu-h3-sample-location-probe)`.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.
- Note: the first manual serial command after flash had a host-side bridge/input-line mismatch and no `A90P1 END`; restarting the managed bridge restored clean cmdv1 responses. Device health was already verified by the flash helper before this host-side bridge restart.

## Probe Result

- Fresh-boot `gpu g0-status` before H3 still showed the expected hazard state:
  - `gpu.g0.fwclass_path=/vendor/firmware_mnt/image`
  - `/dev/kgsl-3d0` missing
  - SQE/GMU firmware present in `/cache/a90-runtime/pkg/gpu-g0-fw`
- H3 command: `gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode`
- Materialize prep ran automatically:
  - `gpu.g0.materialize.fwclass_prepare_attempted=1`
  - `gpu.g0.fwclass_prepare.result=ok`
  - `gpu.g0.materialize.fwclass_prepare_rc=0`
  - `/dev/kgsl-3d0` created
- Sample-location state telemetry matched V3240:
  - `gpu.h3.draw.sample_location_source=mesa-freedreno-a6xx-fd6-context-sample-location-disable-stateobj`
  - `gpu.h3.draw.gras_sc_msaa_sample_pos_cntl=0x0`
  - `gpu.h3.draw.rb_msaa_sample_pos_cntl=0x0`
  - `gpu.h3.draw.tpl1_msaa_sample_pos_cntl=0x0`
- H3 retired cleanly:
  - `gpu.h3.draw.result=draw-retired-readback-unchanged`
  - `timed_out=0`
  - `submit_rc=0`
  - `wait_rc=0`
  - `retired_timestamp=1`
  - `fence_poll_rc=1`
  - `total_elapsed_ms=31`
  - `pm4_dwords=229`
  - `state_reg_writes=91`
- Readback remained unchanged:
  - `readback_changed_count=0`
  - `readback0=0x20202020`
  - `readback_center=0x20202020`

## Post-Probe Health

- Post-probe selftest: `pass=12 warn=1 fail=0`.
- Post-probe `gpu g0-status` showed:
  - `gpu.g0.fwclass_path=/cache/a90-runtime/pkg/gpu-g0-fw`
  - `/dev/kgsl-3d0` exists as `major=502 minor=0`
- Focused dmesg filter showed only `a640_zap` load/reset lines from KGSL bring-up; no timeout/fault/hang/snapshot signature was found.

## Decision

- V3240/V3241 removes the Mesa `sample_locations_disable_stateobj` gap as the primary first-triangle blocker.
- The fresh-boot materialization fix from V3238 remains effective.
- H3 is still not H4: command retirement is clean, but no pixels changed.
- Next bounded unit should continue the Mesa first-draw packet/linkage diff around the remaining RB/CCU/FS-output or shader-output contract before claiming triangle proof.
