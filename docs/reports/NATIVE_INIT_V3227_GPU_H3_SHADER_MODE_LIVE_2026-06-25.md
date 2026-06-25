# Native Init V3227 GPU H3 Shader Mode Live Validation

## Summary

- Cycle: `V3227`
- Candidate under test: `V3226`
- Track: GPU first-triangle H3.7 live validation.
- Decision: `v3227-gpu-h3-shader-mode-live-no-pixel`
- Result: PASS for boot health and H3 command retirement; still NOT H4 triangle proof.
- Resident after validation: `A90 Linux init 0.11.40 (v3226-gpu-h3-shader-mode-probe)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3226_gpu_h3_shader_mode_probe.img`
- Boot SHA256: `99cf5b0f15d1cc508bfe5fa0968a0578a8ae4dbc731428b31ef9c6c37129d394`

## Flash

Pre-flash gates passed:

- Rollback V2321 SHA256 matched the pinned clean USB-identity checkpoint.
- Deeper fallback V2237 SHA256 matched the pinned supplicant checkpoint.
- Final fallback V48 was present.
- TWRP recovery artifacts were present.
- Current resident before flash was V3224 and version/status/selftest were clean, `fail=0`.

The V3226 image was flashed through `workspace/public/src/scripts/revalidation/native_init_flash.py` only. The helper
confirmed the local marker, image size `66052096`, pinned SHA256, recovery-side remote SHA256, boot write, and boot
readback SHA256. The device rebooted to system and native-init version/status verification passed.

## Health

- Resident after flash: `0.11.40 / v3226-gpu-h3-shader-mode-probe`.
- Post-flash status from the flash helper: boot OK, storage mounted RW, transport ready, display `1080x2400`,
  selftest `pass=12 warn=1 fail=0`.
- Post-flash `selftest`: `pass=12 warn=1 fail=0`.
- `gpu g0-fwclass-prepare` completed with `gpu.g0.fwclass_prepare.result=ok`.
- Post-probe `selftest`: `pass=12 warn=1 fail=0`.

Device-specific serial, storage UUID, and network endpoint values were intentionally omitted from this report.

## H3 Live Result

Command:

```text
gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Key telemetry:

```text
gpu.h3.draw.scope=first-triangle-h3-shader-mode-mov-f32-shader
gpu.h3.draw.shader_payload=hand-assembled-ir3-mov-f32-vs-position-fs-color-no-full-compiler
gpu.h3.draw.shader_mode_source=mesa-freedreno-a6xx-fd6-emit-shader-regs-sp-tpl1-mode
gpu.h3.draw.sp_mode_cntl=0x5
gpu.h3.draw.tpl1_mode_cntl=0xa2
gpu.h3.draw.sp_cntl0_source=mesa-freedreno-a6xx-sp-footprint-mergedregs
gpu.h3.draw.sp_vs_cntl0=0x100080
gpu.h3.draw.sp_ps_cntl0=0x81000080
gpu.h3.draw.raster_coverage_source=mesa-freedreno-a6xx-gras-rb-msaa-defaults
gpu.h3.draw.gras_sc_ras_msaa_cntl=0x0
gpu.h3.draw.gras_sc_dest_msaa_cntl=0x4
gpu.h3.draw.gras_sc_screen_scissor_cntl=0x0
gpu.h3.draw.vpc_linkage_source=mesa-freedreno-a6xx-position-psizeloc-clip-cull-linkage
gpu.h3.draw.vpc_vs_cntl=0xff0004
gpu.h3.draw.vpc_vs_clip_cull_cntl=0xffff00
gpu.h3.draw.vpc_vs_clip_cull_cntl_v2=0xffff00
gpu.h3.draw.gras_cl_vs_clip_cull_distance=0x0
gpu.h3.draw.mrt_component_mask_source=mesa-freedreno-a6xx-mrt-components-full-rt0
gpu.h3.draw.ir3_mov_f32f32_r0x_hi=0x20444000
gpu.h3.draw.fs_color_f32_bits=0x3f800000
gpu.h3.draw.color_output_mask=0xf
gpu.h3.draw.result=draw-retired-readback-unchanged
gpu.h3.draw.timed_out=0
gpu.h3.draw.submit_rc=0
gpu.h3.draw.wait_rc=0
gpu.h3.draw.retired_timestamp=1
gpu.h3.draw.fence_poll_rc=1
gpu.h3.draw.pm4_dwords=186
gpu.h3.draw.state_reg_writes=68
gpu.h3.draw.vfd_reg_writes=8
gpu.h3.draw.readback_changed_count=0
gpu.h3.draw.readback0=0x20202020
gpu.h3.draw.readback_center=0x20202020
gpu.h3.draw.total_elapsed_ms=30
```

Latest bridge log scan showed no `GPU PAGE FAULT`, CP opcode fault, KGSL fault, Adreno fault, SMMU/IOMMU fault, or GPU
hang signature in the current bridge log.

## Interpretation

V3226 proves the H3 envelope still retires after adding the Mesa-derived shader mode registers emitted by
`fd6_program.cc::emit_shader_regs()`:

- `SP_MODE_CNTL=0x00000005`.
- `TPL1_MODE_CNTL=0x000000a2`.

Because readback remains unchanged despite `readback_change_expected=1`, the tested shader-mode setup gap is not the
remaining primary blocker. The next bounded unit should continue the Mesa-equivalent first-draw packet diff and test a
small, draw-relevant missing static/init state group such as `RB_INTERP_CNTL`/`RB_PS_INPUT_CNTL`/sample-position or the
minimal `VPC_VARYING_LM_TRANSFER_CNTL`/SIV path, rather than widening to blobs or a full compiler.

H4 remains unclaimed until interior pixels change and exterior pixels remain clear.

## Safety

- Boot partition only; no forbidden partition write.
- Flash path only: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- No rollback was needed for V3226.
- No PMIC, regulator, GDSC, GPIO, power-rail, proprietary blob, EGL, OpenCL, exploit, or full Mesa compiler path was
  attempted.
- KGSL work stayed child-bounded with timeout/reap cleanup.
