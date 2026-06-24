# Native Init V3183 GPU G0 Live Firmware Timeout

## Summary

- Cycle: `V3183`
- Track: GPU G0 KGSL open-hang diagnosis.
- Decision: `v3183-gpu-g0-live-firmware-timeout`
- Result: LIVE ROOT CAUSE ADVANCED; bounded open still timed out.
- Device flash: yes, boot partition only via `native_init_flash.py`.
- Candidate flashed: `workspace/private/inputs/boot_images/boot_linux_v3180_gpu_g0_fwpath_status.img`
- Candidate SHA256: `9ae222ea5a878d6b6233023f92223af2de4ad01d7955f47bab7c362d045ca2d7`
- Init after flash: `A90 Linux init 0.11.20 (v3180-gpu-g0-fwpath-status)`
- Private evidence directory: `workspace/private/runs/gpu/v3183-g0-live/`

## Flash Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` exists with SHA256
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` exists with SHA256
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` exists.
- Recovery/TWRP was available and the flash helper completed its checked recovery write/readback flow.
- Post-flash health passed: `version`, `status`, and `selftest verbose` all returned successfully.
- Selftest remained `pass=12 warn=1 fail=0`.

## Live G0 Evidence

`gpu g0-status` showed KGSL sysfs present and firmware class pointed at the mounted firmware image path:

- `gpu.g0.sysfs_class.exists=1`
- `gpu.g0.sysfs_dev=502:0`
- `gpu.g0.fwclass_path=/vendor/firmware_mnt/image`

Runtime firmware visibility was split:

- SQE and GMU files were not visible at `/vendor/firmware/*` or `/firmware/*`:
  - `a630_sqe.fw`: missing
  - `a640_gmu.bin`: missing
- ZAP PIL segments were visible under `/vendor/firmware_mnt/image/`:
  - `a640_zap.mdt`
  - `a640_zap.b00`
  - `a640_zap.b01`
  - `a640_zap.b02`
- `/firmware_mnt/image/a640_zap.*` was not present as a second alias.

One bounded open probe was then run:

```text
gpu g0-open-probe --timeout-ms 2000 --materialize-devnode
```

Result:

- `/dev/kgsl-3d0` was materialized from sysfs major/minor `502:0`.
- Parent did not enter `open()`.
- No ioctl, mmap, or power write was attempted.
- Child `open("/dev/kgsl-3d0", O_RDONLY)` timed out after the 2000 ms guard.
- Command result: `rc=-110 errno=110`.

The post-probe kernel log identified the current blocking edge:

```text
firmware a630_sqe.fw: _request_firmware_load: firmware state wait timeout: rc = -512
kgsl kgsl-3d0: |_load_firmware| request_firmware(a630_sqe.fw) failed: -4
```

## Diagnosis

G0 is still blocked before any clean freedreno/KGSL user path can be attempted, but the blocker is now narrower than
the original "KGSL open hangs" class. The first open is reaching the stock KGSL firmware load path and waiting on
`request_firmware(a630_sqe.fw)`. The factory firmware audit already proved the private AP vendor image contains both
`a630_sqe.fw` and `a640_gmu.bin`; V3183 proves those files are not visible through the runtime firmware class path used
by native init.

This keeps G0 on the clean firmware-visibility path. It does not yet justify direct GMU, GDSC, regulator, PMIC, GPIO, or
power-rail writes.

## Next Step

Prepare a unified GPU firmware class directory that exposes:

- `a630_sqe.fw`
- `a640_gmu.bin`
- `a640_zap.mdt`
- `a640_zap.b00`
- `a640_zap.b01`
- `a640_zap.b02`

Then point firmware class at that directory and repeat exactly one bounded `g0-open-probe`. If SQE/GMU become visible
and the bounded open still times out, the next G0 blocker moves from firmware visibility to GMU/power-domain startup.

## Safety

- Boot partition only; no forbidden partition was touched.
- Flash used only `native_init_flash.py`.
- G0 probe remained bounded and parent-guarded.
- No KGSL ioctl, mmap, freedreno submit, G1 allocation, proprietary EGL/Bionic path, exploit path, or direct power write
  was used.
- Raw logs and device-specific transport details remain under `workspace/private/` and are not committed.

## Validation

- Flash helper completed image SHA check, recovery write, readback prefix check, reboot, and post-verify.
- Post-flash `version`: `A90 Linux init 0.11.20 (v3180-gpu-g0-fwpath-status)`.
- Post-flash `status`: PASS.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.
- `gpu g0-status`: PASS.
- `gpu g0-open-probe --timeout-ms 2000 --materialize-devnode`: bounded timeout as expected.
- Dmesg after probe: `request_firmware(a630_sqe.fw)` wait timeout.
