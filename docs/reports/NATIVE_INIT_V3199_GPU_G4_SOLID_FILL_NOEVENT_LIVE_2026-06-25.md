# Native Init V3199 GPU G4 Solid Fill No-Event Live

## Summary

- Cycle: `V3199`
- Resident under test: `A90 Linux init 0.11.27 (v3198-gpu-g4-solid-fill-noevent-probe)`
- Source/build commit: `34b97834 Build V3198 GPU G4 no-event solid fill probe`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3198_gpu_g4_solid_fill_noevent_probe.img`
- Boot SHA256: `91cd7113f507d3e935aceb07a41bdb8efd7243ab79caf6413b5c74fa00fc4af6`
- Decision: V3198 live is safe enough to keep as resident, but not a G4 render/readback pass.

## Flash And Health

- Rollback gate: confirmed `v2321` rollback SHA, `v2237` fallback SHA, `v48` fallback presence, and TWRP recovery image before flash.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py` only.
- Post-flash verify: `version` and `status` returned V3198 with `selftest pass=12 warn=1 fail=0`.
- Post-probe health: `selftest verbose` remained `pass=12 warn=1 fail=0`.

## Live Probe Results

- `gpu g0-fwclass-prepare`: PASS, `gpu.g0.fwclass_prepare.result=ok`.
- `gpu g1-context-probe --timeout-ms 5000 --materialize-devnode`: PASS, `created-destroyed`, elapsed about `27ms`.
- `gpu g2-mmap-probe --timeout-ms 5000 --materialize-devnode`: PASS, `mapped-unmapped`, elapsed about `8ms`.
- `gpu g3-noop-submit-probe --timeout-ms 5000 --materialize-devnode`: PASS, `submitted-fenced-retired`, elapsed about `9ms`.
- `gpu g4-solid-fill-probe --timeout-ms 5000 --materialize-devnode`: command completed without timeout or child kill, but returned `returned-error`.

## G4 Evidence

- PM4 source marker: `mesa-freedreno-a6xx-fd6-clear-buffer-cp-blit-a2d-no-event-write-tail`.
- `GPU_COMMAND` submitted successfully with timestamp `1`.
- KGSL timestamp wait and retired timestamp read both succeeded.
- Destination cache sync from GPU succeeded.
- Readback did not verify: `readback_verified=0`, `readback_mismatch_count=16`.
- First readback words stayed sentinel: `0x11111111`.
- PM4 dwords dropped to `29`, confirming the V3196 post-blit event-write tail was removed.

## Dmesg

- Focused post-G4 dmesg filter found no V3197-style signatures:
  - no `GPU PAGE FAULT`
  - no `CP opcode`
  - no `a6xx_cp_hw_err`
  - no `adreno_hang`
  - no `GPU hang`
  - no `fault ctx`

## Interpretation

- Removing all post-blit events eliminated the V3196 CP fault/hang path.
- It also left the A2D result invisible to CPU readback, consistent with Mesa's note that `CP_BLIT` writes through CCU and needs a CCU flush before sysmem readback.
- Next candidate should restore only the minimal post-blit CCU color flush (`PC_CCU_FLUSH_COLOR_TS`, raw event `0x1d`) plus `CP_WAIT_FOR_IDLE`, while continuing to exclude `CACHE_INVALIDATE` (`0x31`) and the debug label event.

## Next

- Build V3200 as a bounded G4 CCU-flush probe.
- Keep G0/G1/G2/G3 prerequisites unchanged.
- Validate that readback changes from sentinel to fill pattern and that the focused dmesg fault filter remains empty.
