# Native Init V3260 GPU H3 Visibility Packets Live Validation

## Summary

- Cycle: `V3260`
- Candidate built by: `V3259`
- Track: GPU H3 first-triangle sysmem-prep ordering before H4 readback proof.
- Result: FAIL for pixel proof, PASS for boot/health/safety envelope.
- Resident after flash: `A90 Linux init 0.11.56 (v3259-gpu-h3-visibility-packets-probe)`.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3259_gpu_h3_visibility_packets_probe.img`
- Boot SHA256: `48854bdd6d11d658254c364456f55e794c247484cb0b8f199065a9354f95f02a`

## Flash Gate

- Rollback `v2321` image exists and SHA256 matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper rollback `v2237` image exists and SHA256 matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` exists.
- TWRP/recovery artifacts are present under `workspace/private/inputs/firmware/twrp/`.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py` only.
- Flash readback SHA256 matched the local image SHA256.

## Health

- Pre-flash resident: `0.11.55 (v3257-gpu-h3-vpc-so-override-probe)`.
- Pre-flash selftest: `pass=12 warn=1 fail=0`.
- Post-flash `native_init_flash.py` version/status gate: passed.
- A transient post-flash serial framing issue dropped one `selftest` END marker; restarting the managed bridge and retrying sequentially recovered it.
- Post-flash selftest after retry: `pass=12 warn=1 fail=0`.
- Post-probe selftest: `pass=12 warn=1 fail=0`.

## Live Probe

- Command: `gpu h3-draw-envelope-probe --timeout-ms 5000 --materialize-devnode`
- Runs: `2`
- H3 scope: `first-triangle-h3-visibility-packets-vpc-so-override-off-sysmem-bin-control-sp-update-cntl-compiler-vs-instrlen-cache-invalidate-rb-render-cntl-r0-output-shader`
- Verified new packets:
  - `cp_skip_ib2_enable_global=0x1d`, value `0x0`
  - `cp_skip_ib2_enable_local=0x23`, value `0x1`
  - `cp_set_visibility_override=0x64`, value `0x1`
- PM4 dwords: `252`
- State register writes: `94`
- Both runs submitted and retired cleanly: `submit_rc=0`, `wait_rc=0`, `retired_timestamp=1`.
- Runtime durations: first run `total_elapsed_ms=29`, second run `total_elapsed_ms=11`.
- Readback result stayed unchanged in both runs:
  - `readback_changed_count=0`
  - `readback0=0x20202020`
  - `readback_center=0x20202020`

## Kernel Fault Check

- Focused `dmesg` filter for KGSL/GPU/GMU/A640 fault, hang, snapshot, or timeout signatures returned no matching lines after the probe.

## Conclusion

V3259 correctly inserted the Mesa sysmem-prep visibility/IB2 packet trio and the command stream still retires without a focused kernel fault. The H3 no-pixel symptom is unchanged, so the missing visibility packet trio is not the primary root cause.

Next bounded unit should switch from adding isolated fd6 sysmem-prep packets to a definitive Mesa-vs-H3 command-stream diff, or test the remaining concrete sysmem window-offset/order gap if a full captured diff is not yet available.
