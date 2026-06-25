# Native Init V3301 GPU Compute C1 Invocationid Live Validation

## Summary

- Cycle: `V3301`
- Track: GPU compute demo C1 live proof.
- Result: PASS
- Flashed boot image: `workspace/private/inputs/boot_images/boot_linux_v3301_gpu_compute_c1_invocationid_probe.img`
- Boot SHA256: `c4128f367a17f2481866142d79942d958ea19fa34528937dece6edf3d04e7dfa`
- Resident after flash: `A90 Linux init 0.11.75 (v3301-gpu-compute-c1-invocationid-probe)`
- Device identifiers, serials, MAC/BSSID/IP values: redacted/omitted.

## Flash Gate

- Pre-flash bridge: running and connected.
- Pre-flash resident: `0.11.74 (v3297-gpu-h5-visual-triangle-hold-probe)`.
- Pre-flash selftest: `pass=12 warn=1 fail=0`.
- Rollback images verified before flash:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - `boot_linux_v2237_supplicant_terminate_poll.img`: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - `boot_linux_v48.img`: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
  - TWRP recovery image: `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Flash result: helper wrote only boot, readback SHA matched, and post-flash `version`/`status` verify passed.

## C1 Probe

- Command: `gpu c1-compute-invocationid-probe --timeout-ms 5000 --materialize-devnode`
- Probe result: `gpu.c1.compute.result=invocationid-uav-readback-pass`
- Materialize devnode: `rc=0`
- Submit/wait/readback:
  - `submit_rc=0`
  - `wait_rc=0`
  - `readtimestamp_rc=0`
  - `readback_sync_rc=0`
  - `retired_timestamp=1`
- UAV proof:
  - `readback0=0`
  - `readback1=1`
  - `readback2=2`
  - `readback3=3`
  - `readback31=31`
  - `changed_count=32`
  - `expected_match_count=32`
  - `mismatch_count=0`
  - `pass=1`
- Timing: `total_elapsed_ms=28`, command duration `44ms`.

## Post-Probe Health

- Post-probe selftest: `pass=12 warn=1 fail=0`.
- Bridge capture C1 markers confirmed:
  - `gpu.c1.compute.result=invocationid-uav-readback-pass`
  - `gpu.c1.compute.expected_match_count=32`
  - `gpu.c1.compute.mismatch_count=0`
  - `gpu.c1.compute.pass=1`
- GPU fault filter over the bridge capture found no `kgsl` fault/hang/snapshot/IOMMU/page-fault, GPU fault, CP error/fault/hang, GMU fault/hang/error, or ringbuffer fault match.

## Safety

- No forbidden partition write was attempted.
- No PMIC/regulator/GDSC/GPIO/backlight/panel re-init write was attempted.
- No proprietary blob/EGL/OpenCL path was used; the probe stayed on freedreno/KGSL-direct userspace command submission.
- No rollback was required.

## Next

- C1 is closed.
- Next rung: C2 visible compute buffer pattern, then C3 present via the proven H5 KMS path.
