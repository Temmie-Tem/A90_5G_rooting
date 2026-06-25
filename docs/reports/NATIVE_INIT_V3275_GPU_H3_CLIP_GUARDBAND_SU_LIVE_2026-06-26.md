# Native Init V3275 GPU H3 Clip Guardband SU Live

## Summary

- Cycle: `V3275`
- Track: GPU H3 first-triangle clip/guardband/SU rasterizer state live validation.
- Source build report: `docs/reports/NATIVE_INIT_V3274_GPU_H3_CLIP_GUARDBAND_SU_SOURCE_BUILD_2026-06-26.md`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3274_gpu_h3_clip_guardband_su_probe.img`
- Boot SHA256: `b9f85b95fda81edd77f2bc121c940275c4122f5842ba929400c7f49b43bdb313`
- Init: `A90 Linux init 0.11.63 (v3274-gpu-h3-clip-guardband-su-probe)`
- Result: BOOT/HEALTH PASS, H3 PIXEL PROOF FAIL
- H4 first-triangle proof: `not reached`

## Flash And Health

- Rollback gates were reconfirmed before flash:
  `v2321` SHA matched, `v2237` SHA matched, `v48` existed, and TWRP recovery artifacts were present.
- Flashed only the checked V3274 boot artifact through `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Flash helper confirmed local SHA, recovery push SHA, boot block readback SHA, and post-reboot native-init version/status.
- Post-flash health:
  `version` reported `0.11.63`; `status` reported `BOOT OK`; `selftest verbose` reported `pass=12 warn=1 fail=0`.
- Validation note: one immediate post-flash selftest attempt hit serial prompt fragment noise (`ATAT`) without running `cmdv1`. A sequential `version` command re-synchronized the bridge, and the repeated `status`/`selftest` passed.

## Live H3 Result

Two H3 runs were executed with:

```text
python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 30 --hide-on-busy gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Both runs applied the V3274 state delta:

- `gpu.h3.draw.scope=first-triangle-h3-clip-guardband-su-rasterizer-a6xx-hlsq-negative-audit-output-routing-sp-frontend-prog-id-state-sp-const-fs-output-cntl-raster-mode-cp-set-mode-window-offset-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader`
- `gpu.h3.draw.hlsq_round4_audit=local-a6xx-fd6-uses-sp-program-config-not-legacy-hlsq-control-regs`
- `gpu.h3.draw.gras_cl_cntl=0xc0`
- `gpu.h3.draw.gras_cl_guardband_clip_adj=0x7fdff`
- `gpu.h3.draw.gras_su_cntl=0x814`
- `gpu.h3.draw.gras_su_point_minmax=0xffc00001`
- `gpu.h3.draw.gras_su_point_size=0x10`
- `gpu.h3.draw.rb_ps_output_cntl=0x0`
- `gpu.h3.draw.rb_ps_mrt_cntl=0x1`
- `gpu.h3.draw.sp_ps_output_cntl=0xfcfcfc00`
- `gpu.h3.draw.sp_ps_mrt_cntl=0x1`
- `gpu.h3.draw.pm4_dwords=292`
- `gpu.h3.draw.state_reg_writes=111`

Both runs retired without timeout:

- Run 1: `submit_rc=0`, `wait_rc=0`, `retired_timestamp=1`, `readback_changed_count=0`,
  `readback0=0x20202020`, `readback_center=0x20202020`, `total_elapsed_ms=30`.
- Run 2: `submit_rc=0`, `wait_rc=0`, `retired_timestamp=1`, `readback_changed_count=0`,
  `readback0=0x20202020`, `readback_center=0x20202020`, `total_elapsed_ms=12`.

Post-probe `selftest verbose` stayed clean: `pass=12 warn=1 fail=0`.

Host-side dmesg filtering over `busybox dmesg` showed no new KGSL page fault, GPU hang, or IOMMU fault signature around the H3 runs. Visible GPU lines were boot-time setup plus `a640_zap` loading/reset; an unrelated CMA allocation failure appeared before the first H3 draw and did not block the probe from retiring.

## Conclusion

V3274 removed the source-grounded clip/guardband/SU rasterizer-state gap and made the fd6 output routing state explicit. The draw still retired with unchanged readback, so missing clip/guardband/SU rasterizer state and the already-audited legacy HLSQ/output-control hypotheses are not the primary H3 no-pixel root cause.

Next bounded unit should stop isolated register sweeps and generate or mine a real fd6 sysmem single-triangle `.rd`/cffdump diff against H3, keeping only direct-sysmem-compatible missing packet groups in scope.
