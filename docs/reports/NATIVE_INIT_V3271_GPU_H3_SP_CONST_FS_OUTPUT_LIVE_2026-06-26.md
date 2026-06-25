# Native Init V3271 GPU H3 SP Const / FS Output Live

## Summary

- Cycle: `V3271`
- Track: GPU H3 first-triangle shader config and FS output control live validation.
- Result: `draw-retired-readback-unchanged`
- H4 first-triangle proof: `not reached`
- Flashed image: `A90 Linux init 0.11.61 (v3270-gpu-h3-sp-const-fs-output-probe)`
- Boot SHA256: `dec8c8f956f75e0d035ec21919e5b2fd2d0fb16a81f191eb1b033d59a0138325`
- Source build report: `docs/reports/NATIVE_INIT_V3270_GPU_H3_SP_CONST_FS_OUTPUT_SOURCE_BUILD_2026-06-26.md`

## Flash Gate

- Built with the checked V3270 build script and recorded SHA256 before flash.
- Rollback images were present and SHA-verified for `v2321` and `v2237`; final fallback `v48` was present.
- TWRP/recovery artifacts were present under `workspace/private/inputs/firmware/twrp/`.
- Flashed only the boot partition via `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Remote boot readback SHA matched the local image SHA.
- Post-flash version confirmed `0.11.61 (v3270-gpu-h3-sp-const-fs-output-probe)`.
- Post-flash status/selftest passed after one managed bridge restart cleared host-side serial fragment noise.

## Live Probe

Command:

```text
python3 workspace/public/src/scripts/revalidation/a90ctl.py --hide-on-busy gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Run 1:

- `gpu.h3.draw.scope=first-triangle-h3-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader`
- `gpu.h3.draw.sp_const_config_source=mesa-freedreno-a6xx-fd6-program-config-stateobj`
- `gpu.h3.draw.sp_vs_const_config=0x100`
- `gpu.h3.draw.sp_ps_const_config=0x100`
- `gpu.h3.draw.fs_output_cntl_source=mesa-freedreno-a6xx-fd6-program-invalid-depth-sampmask-stencil-regids`
- `gpu.h3.draw.sp_ps_output_cntl=0xfcfcfc00`
- `gpu.h3.draw.pm4_dwords=270`
- `gpu.h3.draw.state_reg_writes=100`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.total_elapsed_ms=29`

Run 2:

- `gpu.h3.draw.sp_vs_const_config=0x100`
- `gpu.h3.draw.sp_ps_const_config=0x100`
- `gpu.h3.draw.sp_ps_output_cntl=0xfcfcfc00`
- `gpu.h3.draw.pm4_dwords=270`
- `gpu.h3.draw.state_reg_writes=100`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.total_elapsed_ms=12`

## Health

- Focused dmesg filter for `kgsl|gpu|gmu|a640|fault|hang|snapshot|timeout`: no matching fault/hang/snapshot/timeout lines.
- Post-probe `selftest verbose`: `pass=12 warn=1 fail=0`.

## Decision

Adding A6xx `SP_VS_CONST_CONFIG=0x100`, `SP_PS_CONST_CONFIG=0x100`, and `SP_PS_OUTPUT_CNTL=0xfcfcfc00` made the H3 program/output state match the confirmed fd6/A640 color-only defaults more closely, but it did not produce pixels. Missing SP const enable or invalid depth/sampmask/stencil FS output regids is therefore not the primary no-pixel root cause.

The round-4 HLSQ claim was source-audited before this live unit: the old `HLSQ_CONTROL_*` / `HLSQ_*_CNTL` style registers are not present in the local A6xx XML/fd6 path being mirrored here, and the A6xx shader payload binding remains through the existing `CP_LOAD_STATE6` preload packets. Next bounded unit should fall back to the real fd6 sysmem triangle `.rd`/cffdump register-packet diff against H3 instead of continuing isolated downstream register sweeps.
