# Native Init V2212 Raw Frame Slots Live Capture

## Decision

- Decision: `v2212-raw-frame-slots-captured`
- Pass: `true`
- Samples: `320`
- Read errors: `2`
- Selftest fail=0: `true`

## Method

- Uses a read-only `BPF_PROG_TYPE_TRACEPOINT` program attached to `sched:sched_switch`.
- Filters the current task to the helper process pid/tgid before reading.
- Reads `task + THREAD_CPU_CONTEXT + {fp,sp,pc}` and then `*(fp)`, `*(fp+8)`, `*(sp)`, `*(sp+8)` using `bpf_probe_read` only.
- Does not use `probe_write_user`, cgroup attach, Wi-Fi, flash, reboot, or partition/firmware writes.

## Interpretation Guard

- `sched_switch` fires before `arm64 cpu_switch_to()` saves the outgoing task context.
- Therefore V2212 is a saved-context/raw-slot discriminator, not a direct current-register x29 read.
- Nonzero raw slots are still useful for deciding whether V2195 stackmap IPs hid encoded-but-canonical frame data.

## Live Summary

- Helper comm: `a90_bpf_raw_fra`
- Last pid/tgid: `3347` / `3347`
- Task pointer: `0xffffffc089c18000`

| Field | Value | kernel_text | aligned_4 | aligned_16 |
| --- | --- | --- | --- | --- |
| `thread_fp` | `0xffffff801394bc80` | `false` | `true` | `true` |
| `thread_sp` | `0xffffff801394bc80` | `false` | `true` | `true` |
| `thread_pc` | `0xffffff8008106428` | `true` | `true` | `false` |
| `fp_slot_next` | `0x0000000000000000` | `false` | `true` | `true` |
| `fp_slot_raw_lr` | `0xffffffc08182c1c0` | `false` | `true` | `true` |
| `fp2_slot_next` | `0x0000000000000000` | `false` | `true` | `true` |
| `fp2_slot_raw_lr` | `0x0000000000000000` | `false` | `true` | `true` |
| `sp_slot0` | `0x0000000000000000` | `false` | `true` | `true` |
| `sp_slot8` | `0xffffffc08182c1c0` | `false` | `true` | `true` |

## Classification

- Canonical aligned LR-like fields: `thread_pc`
- Canonical misaligned LR-like fields: `none`
- Nonzero raw frame slots: `fp_slot_raw_lr, sp_slot8`

## Result Interpretation

- The raw-slot capture path works: `fp+8` and `sp+8` were read directly from saved-context memory.
- In this helper-pid sample, the raw slot value is a kernel VA outside the kernel text range, while `thread_pc` is canonical kernel text.
- `fp_slot_next=0` means this helper's saved-context frame does not provide a walkable parent chain in this sample.
- This does not prove that V2195's stackmap frames were encoded-but-canonical; it proves that direct slot capture is viable and that helper-pid `sched_switch` is too shallow for full ROPP recovery.

## Next

- If ROPP stack recovery remains required, extend the helper from a single last sample to a small sample ring or use a tracepoint path that exposes a sleeping/non-current task pointer.
- Keep the same read-only boundary: `bpf_probe_read` only, no `probe_write_user`, no cgroup attach, no Wi-Fi or flash side effects.

## Safety

- cgroup_attach: `false`
- flash_reboot: `false`
- partition_or_firmware_write: `false`
- probe_write_user_executed: `false`
- read_only_bpf: `true`
- wifi_action: `false`

## Evidence

- Private run: `workspace/private/runs/kernel/v2212-raw-frame-slots-20260612-035341`
- Helper SHA-256: `f737a273be8857803dabdc732ac4abdc041414828d76ea42086c23f2f907d347`
