# Native Init V3324 GPU Z2 KGSL Dmabuf Import Preflight

- Date: 2026-06-27
- Cycle: `V3324`
- Track: GPU rung ④ zero-copy KMS/dmabuf scanout.
- Decision: `v3324-z2-kgsl-dmabuf-import-preflight-pass`

## Scope

This was a no-flash Z2 preflight. The helper creates one DRM msm
`MSM_BO_SCANOUT | MSM_BO_WC` GEM, exports it as a PRIME dma-buf fd,
registers it as an `XBGR8888` KMS framebuffer object, then imports the
same dma-buf fd into `/dev/kgsl-3d0` via `IOCTL_KGSL_GPUOBJ_IMPORT` and
queries `IOCTL_KGSL_GPUOBJ_INFO`. It does not submit GPU commands, modeset,
pageflip, present, or write power/panel controls.

## Safety

- Flash/reboot: `0`
- Partition/firmware writes: `0`
- Display mutation: `0` (FB object creation/removal only; no present/modeset/pageflip)
- GPU submit: `0`
- PMIC/GDSC/regulator/GPIO/backlight writes: `0`

## Build

- Helper source: `workspace/public/src/native-init/helpers/a90_kgsl_dmabuf_import_probe_z2.c`
- Helper SHA-256: `02ab83482f3f86231e65015a8cfe963b4fc7deebd5e12d888d7ab209da719d15`
- Helper size: `663456` bytes
- Install path: `bridge-nc`

## Live Result

- Resident version: `A90 Linux init 0.11.92 (v3321-gpu-m3-hold-timeout-budget)`
- Pre selftest fail=0: `True`
- Post selftest fail=0: `True`
- Target: `960`x`720` stride=`3840` bytes=`2764800` format=`XB24` flags=`MSM_BO_SCANOUT|MSM_BO_WC`
- DRM open: rc=`0` node=`/dev/dri/card0`
- DRM PRIME cap: `0x3` import=`1` export=`1`
- DRM GEM new: rc=`0` handle=`1`
- DRM GEM offset: rc=`0` value=`0x1013ec000`
- DRM GEM IOVA: rc=`-22` value=`0x0`
- DRM mmap: rc=`0` sample=`first=0xff102030 middle=0xff405060 last=0xff708090 words=691200`
- DRM PRIME export: rc=`0` fd_valid=`1`
- DRM ADDFB2: rc=`0` fb_id=`30`
- KGSL open: rc=`0` node=`/dev/kgsl-3d0`
- KGSL import: rc=`0` id=`1` type=`dmabuf` flags=`0x140080`
- KGSL info: rc=`0` id=`1` gpuaddr=`0x500000000` size=`2764800` flags=`0x140080` va_len=`2764800`
- Cleanup: kgsl_free=`0` rmfb=`0` close_drm_handle=`0`
- Helper result: `z2-kgsl-dmabuf-import-preflight-pass`

## Interpretation

The zero-copy allocator bridge is proven through both sides: the same DRM
msm scanout GEM can become a KMS framebuffer and a KGSL GPU object with a
non-zero KGSL gpuaddr. Z2 can now be a bounded source/build unit that
replaces the current `session->linear` KGSL allocation with the imported
dma-buf object for the final render target, then keeps the existing CPU-copy
path as fallback until a one-frame direct pageflip proof passes.

## Source Grounding

- Samsung kernel UAPI exposes `KGSL_USER_MEM_TYPE_DMABUF=3` and
  `IOCTL_KGSL_GPUOBJ_IMPORT` at ioctl number `0x48`.
- Samsung KGSL source wires that ioctl to `kgsl_ioctl_gpuobj_import()`,
  whose dma-buf path calls `dma_buf_get(fd)` and `kgsl_setup_dma_buf()`.
- Mesa Turnip KGSL path imports dma-buf by filling `kgsl_gpuobj_import_dma_buf`
  and then querying `IOCTL_KGSL_GPUOBJ_INFO` for the KGSL iova.
- Existing extracted KGSL present path: `workspace/public/src/native-init/v319/80_shell_dispatch.inc.c`.

## Validation

- Runner: `workspace/public/src/scripts/revalidation/native_gpu_z2_kgsl_dmabuf_import_preflight.py`
- Private summary: `workspace/private/runs/gpu/v3324-gpu-z2-kgsl-dmabuf-import-preflight-20260627-162628/summary.json`
- Pass: `True`
