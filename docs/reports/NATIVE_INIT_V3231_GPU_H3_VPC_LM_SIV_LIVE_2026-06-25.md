# Native Init V3231 GPU H3 VPC LM/SIV Live Validation

## Summary

- Cycle: `V3231`
- Candidate under test: `V3230`
- Track: GPU first-triangle H3.9 live validation.
- Decision: `v3231-gpu-h3-vpc-lm-siv-live-no-pixel`
- Result: PASS for boot health and H3 command retirement; still NOT H4 triangle proof.
- Resident after validation: `A90 Linux init 0.11.42 (v3230-gpu-h3-vpc-lm-siv-probe)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3230_gpu_h3_vpc_lm_siv_probe.img`
- Boot SHA256: `af1fb128ab0f8983745855e45045fddd648e1e37e38e4bdd89731833a4cfbad4`

## Flash

Pre-flash gates passed:

- Rollback V2321 SHA256 matched the pinned clean USB-identity checkpoint.
- Deeper fallback V2237 SHA256 matched the pinned supplicant checkpoint.
- Final fallback V48 was present.
- TWRP recovery artifacts were present.
- Current resident before flash was V3228 and version/status/selftest were clean, `fail=0`.

The V3230 image was flashed through `workspace/public/src/scripts/revalidation/native_init_flash.py` only. The helper
confirmed the local marker, image size `66052096`, pinned SHA256, recovery-side remote SHA256, boot write, and boot
readback SHA256. The device rebooted to system and native-init version/status verification passed.

## Health

- Resident after flash: `0.11.42 / v3230-gpu-h3-vpc-lm-siv-probe`.
- Post-flash status from the flash helper: boot OK, storage mounted RW, transport ready, display `1080x2400`,
  selftest `pass=12 warn=1 fail=0`.
- Post-flash `selftest`: first read showed `pass=12 warn=1 fail=0` but serial framing noise dropped the END marker;
  immediate retry returned `pass=12 warn=1 fail=0`.
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
gpu.h3.draw.scope=first-triangle-h3-vpc-lm-siv-mov-f32-shader
gpu.h3.draw.shader_payload=hand-assembled-ir3-mov-f32-vs-position-fs-color-no-full-compiler
gpu.h3.draw.shader_mode_source=mesa-freedreno-a6xx-fd6-emit-shader-regs-sp-tpl1-mode
gpu.h3.draw.sp_mode_cntl=0x5
gpu.h3.draw.tpl1_mode_cntl=0xa2
gpu.h3.draw.fragment_input_state_source=mesa-freedreno-a6xx-emit-fs-inputs-default-zero
gpu.h3.draw.gras_cl_interp_cntl=0x0
gpu.h3.draw.rb_interp_cntl=0x0
gpu.h3.draw.rb_ps_input_cntl=0x0
gpu.h3.draw.rb_ps_samplefreq_cntl=0x0
gpu.h3.draw.gras_lrz_ps_input_cntl=0x0
gpu.h3.draw.gras_lrz_ps_samplefreq_cntl=0x0
gpu.h3.draw.vpc_linkage_source=mesa-freedreno-a6xx-position-psizeloc-clip-cull-linkage
gpu.h3.draw.vpc_vs_cntl=0xff0004
gpu.h3.draw.vpc_vs_clip_cull_cntl=0xffff00
gpu.h3.draw.vpc_vs_clip_cull_cntl_v2=0xffff00
gpu.h3.draw.gras_cl_vs_clip_cull_distance=0x0
gpu.h3.draw.vpc_lm_siv_source=mesa-freedreno-a6xx-emit-vpc-position-only-siv
gpu.h3.draw.vpc_varying_lm_transfer_cntl0=0xfffffff0
gpu.h3.draw.vpc_varying_lm_transfer_cntl1=0xffffffff
gpu.h3.draw.vpc_varying_lm_transfer_cntl2=0xffffffff
gpu.h3.draw.vpc_varying_lm_transfer_cntl3=0xffffffff
gpu.h3.draw.vpc_vs_siv_cntl=0xffff
gpu.h3.draw.vpc_vs_siv_cntl_v2=0xffff
gpu.h3.draw.gras_su_vs_siv_cntl=0x0
gpu.h3.draw.result=draw-retired-readback-unchanged
gpu.h3.draw.timed_out=0
gpu.h3.draw.submit_rc=0
gpu.h3.draw.wait_rc=0
gpu.h3.draw.retired_timestamp=1
gpu.h3.draw.fence_poll_rc=1
gpu.h3.draw.pm4_dwords=209
gpu.h3.draw.state_reg_writes=81
gpu.h3.draw.vfd_reg_writes=8
gpu.h3.draw.readback_changed_count=0
gpu.h3.draw.readback0=0x20202020
gpu.h3.draw.readback_center=0x20202020
gpu.h3.draw.total_elapsed_ms=31
```

Kernel log filtering after the probe showed normal boot-time KGSL/GMU/SMMU inventory and the A640 ZAP load. No KGSL,
Adreno, GMU, SMMU/IOMMU GPU fault, snapshot, or GPU hang signature was observed. The filter also matched an unrelated
`modem.mdt` firmware timeout; it is outside the GPU path and did not regress selftest.

## Interpretation

V3230 proves the H3 envelope still retires after adding the Mesa-derived VPC LM/SIV state emitted by
`fd6_program.cc::emit_vpc()` for the current position-only linkage:

- `VPC_VARYING_LM_TRANSFER_CNTL[0..3]={0xfffffff0,0xffffffff,0xffffffff,0xffffffff}`.
- `VPC_VS_SIV_CNTL=0x0000ffff`.
- `VPC_VS_SIV_CNTL_V2=0x0000ffff`.
- `GRAS_SU_VS_SIV_CNTL=0x00000000`.

Because readback remains unchanged despite `readback_change_expected=1`, this VPC LM/SIV state group is not the
remaining primary blocker. The next bounded unit should continue the Mesa-equivalent first-draw packet diff and test a
small sample-position/static state group or revisit the hand-assembled shader output contract before claiming H4.

H4 remains unclaimed until interior pixels change and exterior pixels remain clear.

## Safety

- Boot partition only; no forbidden partition write.
- Flash path only: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- No rollback was needed for V3230.
- No PMIC, regulator, GDSC, GPIO, power-rail, proprietary blob, EGL, OpenCL, exploit, or full Mesa compiler path was
  attempted.
- KGSL work stayed child-bounded with timeout/reap cleanup.
