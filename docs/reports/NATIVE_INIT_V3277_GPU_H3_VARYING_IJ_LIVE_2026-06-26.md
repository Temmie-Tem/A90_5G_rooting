# Native Init V3277 GPU H3 Varying / IJ Live

## Summary

- Cycle: `V3277`
- Track: GPU H3 first-triangle varying/IJ and VPC linkage live validation.
- Result: `draw-retired-readback-unchanged`
- H4 first-triangle proof: `not reached`
- Flashed image: `A90 Linux init 0.11.64 (v3276-gpu-h3-varying-ij-probe)`
- Boot SHA256: `1cfada71599befc2cd47c5ffb53f1eab4673d5200bbe92c77f8137ed0e86471e`
- Source build report: `docs/reports/NATIVE_INIT_V3276_GPU_H3_VARYING_IJ_SOURCE_BUILD_2026-06-26.md`

## Flash Gate

- Built with the checked V3276 build script and recorded SHA256 before flash.
- Rollback images were present and SHA-verified for `v2321` and `v2237`; final fallback `v48` was present.
- Recovery/TWRP availability was confirmed by `native_init_flash.py --from-native` entering ADB recovery before flashing.
- Flashed only the boot partition via `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Remote boot readback SHA matched the local image SHA.
- Post-flash version confirmed `0.11.64 (v3276-gpu-h3-varying-ij-probe)`.
- Post-flash status passed through the flash helper; post-flash `selftest verbose` passed with `pass=12 warn=1 fail=0`.
- One normal-input `selftest verbose` attempt lost the `A90P1 END` marker after boot; rerunning with `--input-mode slow` resynchronized the serial path and passed.

## Live Probe

Command:

```text
python3 workspace/public/src/scripts/revalidation/a90ctl.py --input-mode slow gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Run 1:

- `gpu.h3.draw.scope=first-triangle-h3-varying-ij-vpc-linkage-cffdump-diff-clip-guardband-su-rasterizer-a6xx-output-routing-sp-frontend-prog-id-state-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader`
- `gpu.h3.draw.shader_payload=verified-ir3-vs-r0xy-to-r2-position-plus-r0-varying-and-cffdump-bary-fs`
- `gpu.h3.draw.vs_position_output_regid=0x8`
- `gpu.h3.draw.vs_varying_output_regid=0x0`
- `gpu.h3.draw.ps_output_regid=0x2`
- `gpu.h3.draw.sp_vs_cntl0=0x80100180`
- `gpu.h3.draw.sp_ps_cntl0=0x81500100`
- `gpu.h3.draw.sp_vs_output_cntl=0x2`
- `gpu.h3.draw.sp_vs_output_reg0=0xf000f08`
- `gpu.h3.draw.sp_vs_vpc_dest_reg0=0x400`
- `gpu.h3.draw.vpc_vs_cntl=0xff0408`
- `gpu.h3.draw.vpc_ps_cntl=0xff01ff04`
- `gpu.h3.draw.sp_ps_initial_tex_load_cntl=0x7fc0`
- `gpu.h3.draw.sp_ps_wave_cntl=0x3`
- `gpu.h3.draw.sp_reg_prog_id_1=0xfcfcfc00`
- `gpu.h3.draw.vfd_cntl_1=0xfcfcfcfc`
- `gpu.h3.draw.pc_mode_cntl=0x1f`
- `gpu.h3.draw.pc_vs_cntl=0x8`
- `gpu.h3.draw.pm4_dwords=306`
- `gpu.h3.draw.state_reg_writes=118`
- `gpu.h3.draw.vfd_reg_writes=14`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.total_elapsed_ms=29`

Run 2:

- `gpu.h3.draw.vs_position_output_regid=0x8`
- `gpu.h3.draw.vs_varying_output_regid=0x0`
- `gpu.h3.draw.ps_output_regid=0x2`
- `gpu.h3.draw.sp_vs_cntl0=0x80100180`
- `gpu.h3.draw.sp_ps_cntl0=0x81500100`
- `gpu.h3.draw.vpc_vs_cntl=0xff0408`
- `gpu.h3.draw.vpc_ps_cntl=0xff01ff04`
- `gpu.h3.draw.sp_ps_initial_tex_load_cntl=0x7fc0`
- `gpu.h3.draw.sp_ps_wave_cntl=0x3`
- `gpu.h3.draw.sp_reg_prog_id_1=0xfcfcfc00`
- `gpu.h3.draw.pm4_dwords=306`
- `gpu.h3.draw.state_reg_writes=118`
- `gpu.h3.draw.vfd_reg_writes=14`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.total_elapsed_ms=12`

## Health

- Post-probe `selftest verbose`: `pass=12 warn=1 fail=0`.
- Broad dmesg filter contained normal boot-time KGSL/GMU bring-up plus an unrelated modem firmware wait timeout.
- Focused GPU fault filter produced no KGSL/GPU/GMU/A640 fault, hang, snapshot, timeout, CP opcode, or hardware-error signature. The only matched line was the existing boot-time `gpuss-1-usr` sensor read error.

## Decision

The V3276 source delta made H3 use the cffdump-grounded varying/IJ shader path and matching VPC/SP/VFD linkage: VS writes position to `r2`, preserves four varying components from `r0`, FS consumes IJ barycentric inputs, MRT0 color comes from FS regid `2`, and the command stream grew to `306` PM4 dwords / `118` state writes / `14` VFD sideband writes. The draw still submits, retires, and frees cleanly, but readback remains unchanged.

This removes the cffdump varying/IJ linkage group as the primary no-pixel cause. The next bounded unit should stop adding isolated HLSQ/output/raster guesses and compare a real fd6 sysmem single-triangle `.rd`/cffdump packet stream against H3, then admit only direct-sysmem-compatible missing packet groups.
