# Native Init V3184 GPU G0 Firmware Class Live Open Success

## Summary

- Cycle: `V3184`
- Track: GPU G0 KGSL open-hang diagnosis.
- Decision: `v3184-gpu-g0-fwclass-live-open-success`
- Result: PASS for G0 bounded open after firmware visibility fix.
- Device flash: no new flash in this unit; live work used the already-flashed V3180 image.
- Resident init: `A90 Linux init 0.11.20 (v3180-gpu-g0-fwpath-status)`.
- Private evidence directory: `workspace/private/runs/gpu/v3184-g0-fwclass-live/`.

## Firmware Preparation

The V3183 live probe proved `request_firmware(a630_sqe.fw)` was the current blocker. V3184 used the already-audited
private factory firmware payloads and staged only runtime copies under `/cache`:

- `a630_sqe.fw`
  - source: private stock AP vendor ext4 `/firmware/a630_sqe.fw`
  - size: `32304`
  - SHA256: `a0e1b583f620fabe32729ce367959d1960638663244d7d0cfc21b9a5215a018b`
- `a640_gmu.bin`
  - source: private stock AP vendor ext4 `/firmware/a640_gmu.bin`
  - size: `37680`
  - SHA256: `3ff0c02708bbe78641db887fa62f3a7f9337934d0c2ce0b961ef7c43172591d2`

The device-side unified GPU firmware directory was prepared at:

```text
/cache/a90-runtime/pkg/gpu-g0-fw
```

It contains runtime copies of:

- `a630_sqe.fw`
- `a640_gmu.bin`
- `a640_zap.mdt`
- `a640_zap.b00`
- `a640_zap.b01`
- `a640_zap.b02`

The ZAP files were copied from the already-mounted runtime firmware path. The `a90_fwpathctl` helper then changed
`/sys/module/firmware_class/parameters/path` from `/vendor/firmware_mnt/image` to the unified cache directory.

No raw firmware payload is committed by this report.

## Live Result

After the firmware class path update, `gpu g0-status` showed:

- `gpu.g0.fwclass_path=/cache/a90-runtime/pkg/gpu-g0-fw`
- `/dev/kgsl-3d0` existed as character device major/minor `502:0`.

One bounded open probe was run:

```text
gpu g0-open-probe --timeout-ms 5000 --materialize-devnode
```

Result:

- Parent did not enter `open()`.
- No ioctl, mmap, freedreno submit, or power write was attempted.
- Child `open("/dev/kgsl-3d0", O_RDONLY)` returned successfully.
- `gpu.g0.open.result=returned`
- `gpu.g0.open.timed_out=0`
- `gpu.g0.open.child_elapsed_ms=23`
- `gpu.g0.open.open_rc=0`
- Command duration: `26 ms`.

This closes the original G0 "first open hangs" blocker for the firmware-visible runtime state.

## Dmesg Notes

The post-success dmesg shows the secure GPU ZAP path reached:

```text
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
```

The same boot also contains modem SSR/fatal lines. At least one modem fatal event occurred before the successful G0
open, so V3184 cannot attribute modem SSR solely to KGSL open. A later modem SSR also appears after the ZAP load window.
Health checks still passed, but this is a G1 blocker until a fresh-boot repeat can separate baseline modem churn from
GPU-triggered side effects.

## Diagnosis

V3183's timeout was a firmware-class visibility problem, not an unavoidable KGSL open hang:

1. With `firmware_class.path=/vendor/firmware_mnt/image`, SQE/GMU were not visible and `request_firmware(a630_sqe.fw)`
   timed out.
2. With SQE/GMU plus ZAP exposed in a single runtime directory and firmware class pointed there, the same bounded open
   returned in `23 ms`.

The clean next source unit is to add a native `gpu g0-fwclass-prepare` command that:

- expects private SQE/GMU payloads already staged under the allowed runtime cache path;
- copies or verifies the ZAP files from `/vendor/firmware_mnt/image`;
- writes firmware class path through the same constrained helper logic;
- reports the complete runtime directory state before allowing another bounded `g0-open-probe`.

Do not move to G1/freedreno submit work until that source command is built, flashed, health-checked, and repeated on a
fresh boot with dmesg checked for modem side effects.

## Safety

- No new flash, no forbidden partition write, and no raw block write occurred in V3184.
- Runtime writes were confined to `/cache/a90-runtime/pkg/gpu-g0-fw`.
- The firmware class sysfs write was limited to the firmware search path and used the existing constrained helper.
- No KGSL ioctl, mmap, freedreno submit, G1 allocation, proprietary EGL/Bionic path, exploit path, or direct GMU/GDSC,
  regulator, PMIC, GPIO, or power-rail write was used.
- Raw dmesg, transport output, and private firmware payloads remain under `workspace/private/`.

## Validation

- Host extraction SHA matched the V3179 audit values.
- Device-side SHA for `a630_sqe.fw` and `a640_gmu.bin` matched the expected private payloads.
- Unified firmware directory listing showed all six required files.
- `a90_fwpathctl read` confirmed the updated firmware class path.
- `gpu g0-status`: PASS.
- `gpu g0-open-probe --timeout-ms 5000 --materialize-devnode`: PASS, open returned in `23 ms`.
- Post-open `status`: PASS.
- Post-open `selftest verbose`: `pass=12 warn=1 fail=0`.
