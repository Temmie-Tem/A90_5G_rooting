# Native Init V3258 GPU H3 VPC_SO_OVERRIDE Live

## Summary

- Cycle: `V3258`
- Live target: `V3257` image, `0.11.55 (v3257-gpu-h3-vpc-so-override-probe)`
- Boot image SHA256: `c308eee87756e5417b6b356a83c4c9c3721b056b4b9f37797b2a3269596db7e1`
- Result: BOOT/HEALTH PASS, H3 PIXEL PROOF FAIL
- Decision: `vpc-so-override-not-primary-no-pixel-root-cause`

## Flash Gate

- Rollback `v2321` SHA256 matched the required value.
- Deeper fallback `v2237` SHA256 matched the required value.
- Final fallback `boot_linux_v48.img` was present.
- TWRP recovery artifacts were present under the private firmware input path.
- Current resident before flash was `0.11.54 (v3255-gpu-h3-sysmem-bin-control-probe)` with `selftest pass=12 warn=1 fail=0`.
- Flash path: checked helper `workspace/public/src/scripts/revalidation/native_init_flash.py` only.
- Boot partition prefix readback SHA256 matched the V3257 image SHA256.

## Post-Flash Health

- Native-init flash verify reached `0.11.55 (v3257-gpu-h3-vpc-so-override-probe)`.
- The first explicit manual health command after a bridge restart hit one host-side connection reset. A short wait and sequential retry restored normal cmdv1 framing.
- After retry, `version`, `status`, and `selftest verbose` all passed with `selftest pass=12 warn=1 fail=0`.
- Explicit post-probe `selftest verbose` again reported `pass=12 warn=1 fail=0`.

## H3 Live Probe

Command:

```text
gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode
```

Verified V3257 telemetry:

- `gpu.h3.draw.scope=first-triangle-h3-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader`
- `gpu.h3.draw.sp_update_cntl=0x9f`
- `gpu.h3.draw.rb_ccu_cntl=0x10000000`
- `gpu.h3.draw.gras_sc_bin_cntl=0x2c00000`
- `gpu.h3.draw.rb_cntl=0x2c00000`
- `gpu.h3.draw.vpc_so_override_source=mesa-freedreno-a6xx-fd6-sysmem-prep-enable-streamout-false`
- `gpu.h3.draw.vpc_so_override=0x0`
- `gpu.h3.draw.pm4_dwords=246`
- `gpu.h3.draw.state_reg_writes=94`

First live run:

- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.total_elapsed_ms=30`

Second warm-run check:

- `gpu.h3.draw.result=draw-retired-readback-unchanged`
- `gpu.h3.draw.submit_rc=0`
- `gpu.h3.draw.wait_rc=0`
- `gpu.h3.draw.retired_timestamp=1`
- `gpu.h3.draw.readback_changed_count=0`
- `gpu.h3.draw.readback0=0x20202020`
- `gpu.h3.draw.readback_center=0x20202020`
- `gpu.h3.draw.total_elapsed_ms=12`

Focused dmesg fault filter found no KGSL/GPU/GMU/A640 fault, hang, snapshot, or timeout signature.

## Interpretation

V3257 proves the Mesa sysmem-prep `VPC_SO_OVERRIDE(false)` value was emitted and reached live code:
telemetry reported `vpc_so_override=0x0`, while the command stream size and state register count stayed unchanged
at `pm4_dwords=246` and `state_reg_writes=94`. The H3 draw still submitted and retired cleanly, but sysmem readback
stayed unchanged across cold and warm runs.

This removes `VPC_SO_OVERRIDE=0x1` as the primary no-pixel root cause. The next bounded packet delta should continue
from `fd6_emit_sysmem_prep()` rather than broad register sweeping: Mesa emits `CP_SKIP_IB2_ENABLE_GLOBAL=0`,
`CP_SKIP_IB2_ENABLE_LOCAL=1`, and `CP_SET_VISIBILITY_OVERRIDE=1` before the large draw-state CRB, and current H3
does not emit those packets.
