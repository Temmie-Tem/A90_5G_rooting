# Native Init V3281 GPU H3 flag-MRT Live Validation

## Summary

- Cycle: `V3281`
- Track: GPU H3 first-triangle flag-MRT color-target live validation.
- Candidate flashed: `A90 Linux init 0.11.66 (v3280-gpu-h3-flag-mrt-probe)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3280_gpu_h3_flag_mrt_probe.img`
- Boot SHA256: `e295699879f3bb30bff85cfebaeb46b9c4ffd3909d0289bd882e3b2a9decfc19`
- Decision: `v3281-gpu-h3-flag-mrt-live-no-pixel`
- Result: H3 draw retires cleanly, but color readback and color-flag readback both remain unchanged. H4 is not reached.

## Flash Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` verified:
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` verified:
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` present with SHA256
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
- TWRP recovery image present: `workspace/private/inputs/firmware/twrp/recovery.img`,
  SHA256 `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Local image SHA, remote pushed image SHA, and boot readback-prefix SHA all matched
  `e295699879f3bb30bff85cfebaeb46b9c4ffd3909d0289bd882e3b2a9decfc19`.

## Health

- Pre-flash resident: `0.11.65 (v3278-gpu-h3-rgba8-mrt-probe)`, `status ok`, `selftest pass=12 warn=1 fail=0`.
- Post-flash resident: `0.11.66 (v3280-gpu-h3-flag-mrt-probe)`.
- Post-flash `status`: `ok`.
- Post-flash `selftest`: `pass=12 warn=1 fail=0`.
- One verbose selftest attempt after flash lost the serial `END` marker after partial output; a short selftest rerun completed cleanly. Subsequent `version`, H3 probes, dmesg filter, and post-probe selftest used normal A90P1 framing successfully.

## H3 Probe Results

Command:

```text
gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Common state confirmed in both runs:

- `rb_render_cntl=0x10010`
- `rb_mrt0_buf_info=0x330`
- `color_flag_buffer_pitch=0x4001`
- `pm4_dwords=311`
- `state_reg_writes=121`
- `vfd_reg_writes=14`
- `submit_rc=0`
- `wait_rc=0`
- `retired_timestamp=1`
- `readback_sync_rc=0`
- `color_flag_alloc_rc=0`
- `color_flag_free_rc=0`

Run 1:

- `result=draw-retired-readback-unchanged`
- `total_elapsed_ms=31`
- `readback_changed_count=0`
- `readback0=0x20202020`
- `readback_center=0x20202020`
- `color_flag_changed_count=0`
- `color_flag0=0x0`

Run 2:

- `result=draw-retired-readback-unchanged`
- `total_elapsed_ms=12`
- `readback_changed_count=0`
- `readback0=0x20202020`
- `readback_center=0x20202020`
- `color_flag_changed_count=0`
- `color_flag0=0x0`

## Kernel Log Filter

Focused dmesg filter after both H3 runs found no KGSL/GPU fault, hang, snapshot, timeout, opcode, SMMU/IOMMU, or page-fault signature. The only matching GPU lines were expected first-use `a640_zap` subsystem load/reset messages.

## Conclusion

The coherent A640 cffdump flag-MRT color-target group is now tested in the live H3 stream and is not sufficient to produce any color or color-flag memory change. This removes the flag-MRT color-target mismatch as the primary no-pixel root cause.

Next bounded unit should continue from a real fd6 sysmem single-triangle `.rd`/cffdump diff against the current H3 stream. Avoid isolated HLSQ/output/raster guesses unless the diff shows a direct-sysmem-compatible packet group that H3 still lacks.
