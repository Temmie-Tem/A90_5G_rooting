# Native Init V3237 GPU H3 Shader Footprint Live

## Summary

- Cycle: `V3237`
- Track: GPU first-triangle H3 live validation for V3236.
- Candidate boot: `workspace/private/inputs/boot_images/boot_linux_v3236_gpu_h3_shader_footprint_probe.img`
- Candidate SHA256: `f998a8a8adfb6d66da8163bfe53fae9020bdb5328379bb3bcffa08239319b3db`
- Flashed init: `A90 Linux init 0.11.45 (v3236-gpu-h3-shader-footprint-probe)`
- Decision: `v3237-gpu-h3-shader-footprint-live-retired-readback-unchanged`
- Result: PASS for boot health and H3 retirement after GPU firmware-class prep; H4 still not reached.

## Flash And Health

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash route: native init bridge to TWRP recovery, boot partition only.
- Remote pushed image SHA256: `f998a8a8adfb6d66da8163bfe53fae9020bdb5328379bb3bcffa08239319b3db`
- Boot block readback SHA256: `f998a8a8adfb6d66da8163bfe53fae9020bdb5328379bb3bcffa08239319b3db`
- Post-flash version/status: passed; device booted `0.11.45`.
- Post-flash selftest: `pass=12 warn=1 fail=0`.

## Initial H3 Attempt

Command:

```text
gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Key telemetry:

```text
gpu.h3.draw.scope=first-triangle-h3-shader-footprint-r1-footprint2-mov-f32-shader
gpu.h3.draw.sp_fullregfootprint=2
gpu.h3.draw.sp_vs_cntl0=0x100100
gpu.h3.draw.sp_ps_cntl0=0x81000100
gpu.h3.draw.result=timeout
gpu.h3.draw.timed_out=1
gpu.h3.draw.child_killed=1
gpu.h3.draw.child_status=0x9
```

Focused dmesg captured the root cause of the timeout:

```text
firmware a630_sqe.fw: _request_firmware_load: firmware state wait timeout: rc = -512
kgsl kgsl-3d0: |_load_firmware| request_firmware(a630_sqe.fw) failed: -4
```

`gpu g0-status` then showed `firmware_class.path=/vendor/firmware_mnt/image` while `a630_sqe.fw`
and `a640_gmu.bin` were present in `/cache/a90-runtime/pkg/gpu-g0-fw`, not in the vendor firmware
mount. The first H3 timeout was therefore a GPU firmware visibility precondition miss, not proof
against the V3236 shader-footprint candidate.

## Firmware Prep And Retest

Command:

```text
gpu g0-fwclass-prepare
```

Result:

```text
gpu.g0.fwclass_prepare.verify_a630_sqe.rc=0
gpu.g0.fwclass_prepare.verify_a640_gmu.rc=0
gpu.g0.fwclass_prepare.fwpath.readback=/cache/a90-runtime/pkg/gpu-g0-fw
gpu.g0.fwclass_prepare.result=ok
```

Low-rung sanity after prep:

```text
gpu.g0.open.result=returned
gpu.g0.open.child_elapsed_ms=26
gpu.g3.noop.result=submitted-fenced-retired
gpu.g3.noop.total_elapsed_ms=9
```

H3 retest after prep:

```text
gpu.h3.draw.result=draw-retired-readback-unchanged
gpu.h3.draw.timed_out=0
gpu.h3.draw.submit_rc=0
gpu.h3.draw.wait_rc=0
gpu.h3.draw.retired_timestamp=1
gpu.h3.draw.fence_poll_rc=1
gpu.h3.draw.pm4_dwords=223
gpu.h3.draw.state_reg_writes=88
gpu.h3.draw.vfd_reg_writes=8
gpu.h3.draw.total_elapsed_ms=12
gpu.h3.draw.readback_changed_count=0
gpu.h3.draw.readback0=0x20202020
gpu.h3.draw.readback_center=0x20202020
```

Post-prep dmesg focus showed ZAP firmware load/reset with no GPU fault/hang/snapshot signature:

```text
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading from ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
```

Post-probe selftest remained `pass=12 warn=1 fail=0`.

## Interpretation

- V3236 fixes the V3234 r1-output timeout once the known GPU firmware-class prep precondition is applied.
- The initial timeout also exposes a validation hazard: fresh boot images can reset `firmware_class.path` away
  from the cache directory, so H3/H4 live validation must run `gpu g0-fwclass-prepare` before KGSL open/submit,
  or the probe can falsely fail in firmware load rather than in 3D state.
- H3 still does not reach H4 because the draw retires but the offscreen color target remains unchanged.
- The next bounded unit should either make GPU probe materialization include the G0 firmware-class prep, or add
  a separate boot-time/validation gate for it, then continue with the remaining Mesa first-draw packet deltas
  around RB/CCU/FS-output or shader-output linkage.

## Safety

- No forbidden partition was touched.
- Flash used only `native_init_flash.py`.
- Rollback images were present before flash; v2321 and v2237 SHA256 matched the AGENTS contract.
- No auto-rollback was triggered because boot, status, and selftest did not regress.
