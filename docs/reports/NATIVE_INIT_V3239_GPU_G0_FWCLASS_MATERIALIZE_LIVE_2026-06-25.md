# Native Init V3239 GPU G0 Fwclass Materialize Live

## Summary

- Cycle: `V3239`
- Track: GPU G0/H3 fresh-boot firmware-class materialization validation for V3238.
- Candidate boot: `workspace/private/inputs/boot_images/boot_linux_v3238_gpu_g0_fwclass_materialize_prep_probe.img`
- Candidate SHA256: `8633a52394949247ca541b0bdd5597931ac1d79b00ce5d6d194233c12085dfdb`
- Flashed init: `A90 Linux init 0.11.46 (v3238-gpu-g0-fwclass-materialize-prep-probe)`
- Decision: `v3239-gpu-g0-fwclass-materialize-live-pass-h3-retired-readback-unchanged`
- Result: PASS for the materialize-prep fix; H4 still not reached.

## Flash And Health

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash route: native init bridge to TWRP recovery, boot partition only.
- Remote pushed image SHA256: `8633a52394949247ca541b0bdd5597931ac1d79b00ce5d6d194233c12085dfdb`
- Boot block readback SHA256: `8633a52394949247ca541b0bdd5597931ac1d79b00ce5d6d194233c12085dfdb`
- Post-flash version/status: passed; device booted `0.11.46`.
- Post-flash selftest: `pass=12 warn=1 fail=0`.

## Fresh-Boot Precondition

After hiding the foreground menu, a read-only `gpu g0-status` confirmed the expected fresh-boot hazard:

```text
gpu.g0.fwclass_path=/vendor/firmware_mnt/image
gpu.g0.devnode.exists=0 errno=2
gpu.g0.fw_cache_a630_sqe.exists=1
gpu.g0.fw_cache_a640_gmu.exists=1
```

This recreated the V3237 false-timeout precondition without running a manual `gpu g0-fwclass-prepare`.

## H3 Auto-Materialize Probe

Command:

```text
gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Materialize telemetry proved the automatic preflight ran before KGSL open:

```text
gpu.g0.materialize.fwclass_prepare_attempted=1
gpu.g0.fwclass_prepare.verify_a630_sqe.rc=0
gpu.g0.fwclass_prepare.verify_a640_gmu.rc=0
gpu.g0.fwclass_prepare.fwpath.readback=/cache/a90-runtime/pkg/gpu-g0-fw
gpu.g0.fwclass_prepare.result=ok
gpu.g0.materialize.fwclass_prepare_rc=0
gpu.g0.materialize.sysfs_dev_rc=0
gpu.g0.materialize.rc=0
```

H3 result:

```text
gpu.h3.draw.scope=first-triangle-h3-fwclass-materialize-r1-footprint2-mov-f32-shader
gpu.h3.draw.result=draw-retired-readback-unchanged
gpu.h3.draw.timed_out=0
gpu.h3.draw.submit_rc=0
gpu.h3.draw.wait_rc=0
gpu.h3.draw.retired_timestamp=1
gpu.h3.draw.fence_poll_rc=1
gpu.h3.draw.total_elapsed_ms=31
gpu.h3.draw.readback_changed_count=0
gpu.h3.draw.readback0=0x20202020
gpu.h3.draw.readback_center=0x20202020
```

Post-probe `gpu g0-status` showed the expected prepared state:

```text
gpu.g0.fwclass_path=/cache/a90-runtime/pkg/gpu-g0-fw
gpu.g0.devnode.exists=1
```

Post-probe selftest remained `pass=12 warn=1 fail=0`.

## Dmesg Focus

Focused dmesg after the auto-materialized H3 run showed GPU ZAP load/reset, with no `a630_sqe` or KGSL fault/hang/snapshot
signature in the captured GPU-focused tail:

```text
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading from ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
```

The same tail also contained an unrelated WLAN firmware timeout; that is outside this GPU materialize validation and
does not affect the H3 result.

## Interpretation

- V3238 closes the fresh-boot validation hole: `--materialize-devnode` now brings the GPU firmware-class path into the
  known-good cache state before bounded KGSL open/submit.
- H3 no longer requires a separate manual `gpu g0-fwclass-prepare` step after every flash/reboot.
- H4 is still open because the draw retires but the offscreen color target remains unchanged.
- Next bounded unit should return to the remaining first-triangle packet/linkage gap, likely RB/CCU/FS-output or the
  shader-output contract, now without firmware-path false timeouts.

## Safety

- No forbidden partition was touched.
- Flash used only `native_init_flash.py`.
- Rollback images were present before flash; v2321 and v2237 SHA256 matched the AGENTS contract.
- No auto-rollback was triggered because boot, status, and selftest did not regress.
