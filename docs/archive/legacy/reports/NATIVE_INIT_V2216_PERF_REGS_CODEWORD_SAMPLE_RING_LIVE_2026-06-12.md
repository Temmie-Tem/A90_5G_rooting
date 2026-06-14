# Native Init V2216 Perf Regs Codeword Sample Ring

## Decision

- Decision: `v2216-codeword-slide-exact`
- Pass: `true`
- Total samples observed: `62`
- Printed samples parsed: `62`
- Occupied ring slots: `62` / `1024`
- Selftest fail=0: `true`

## Method

- Uses bounded BPF array maps: one stats row plus a 1024-slot sample ring.
- Supports per-CPU software CPU-clock perf events; no unbounded kernel storage is used.
- Samples live perf-event `pt_regs` x29/LR/SP/PC plus raw FP slots with `bpf_probe_read` only.
- Does not use `probe_write_user`, cgroup attach, Wi-Fi, flash, reboot, or partition/firmware writes.

## Metrics

- Unique comms: `11`
- Unique pids: `11`
- Walkable `fp_slot_next`: `60`
- Walkable `fp2_slot_next`: `58`
- Raw LR nonzero: `60`
- Raw LR in kernel text: `1`
- Raw LR kernel VA outside text: `0`
- Live ctx PC in kernel text: `62`
- Live ctx LR nonzero: `62`
- Live ctx LR in kernel text: `60`
- Live ctx LR kernel VA outside text: `0`
- Direct stock-map ctx PC hits: `62` / `62`
- Direct stock-map ctx LR hits: `60` / `62`
- Codeword exact slide accepted: `true`
- Codeword best slide: `0x84ef4`

| Field | Unique Count | Preview |
| --- | ---: | --- |
| `ctx_pc` | 45 | 0xffffff8008103bd4, 0xffffff8008107a1c, 0xffffff800815d6ac, 0xffffff80081d5b18, 0xffffff800824d0ec, 0xffffff8008296140, 0xffffff80082ad610, 0xffffff80082e8ba4, 0xffffff80082e9020, 0xffffff8008310118, 0xffffff800831b398, 0xffffff800831d0e8 |
| `fp_slot_raw_lr` | 59 | 0x00ae7d5e0046241c, 0x015eb88ff810452d, 0x01a2339d2a275b97, 0x03968c46c7bc0258, 0x059ca032b3d6f3f5, 0x06b303e188fbbe55, 0x099f2e93123007e0, 0x0db715cf890e400e, 0x0fc26946e9d9906a, 0x15ae3691107c2c94, 0x19ca6cac587e1cf9, 0x1db45271f2de3aca |
| `fp_slot_next` | 45 | 0xffffff800bcbbda0, 0xffffff800bcbbe00, 0xffffff800bcbbe60, 0xffffff801251bd90, 0xffffff8013c5b7d0, 0xffffff8013d4bd60, 0xffffff8013d4bd90, 0xffffff8013d53930, 0xffffff8013d53940, 0xffffff8013db3cf0, 0xffffff8013dbbc60, 0xffffff8013dbbd00 |
| `fp2_slot_raw_lr` | 58 | 0x00ae7d5e00463808, 0x015eb88ff81046a5, 0x01a2339d2a24c633, 0x03968c46c7dce0f0, 0x059ca032b3d6f2c9, 0x06b303e188fb9351, 0x099f2e9312300f80, 0x0db715cf890ea046, 0x0fc26946e9da387a, 0x15ae3691107d5268, 0x19ca6cac587de359, 0x1db45271f2df4312 |
| `ctx_lr` | 47 | 0x000000000044dfb0, 0xffffff8008107a5c, 0xffffff80081560bc, 0xffffff8008156158, 0xffffff800816ddcc, 0xffffff80081d5b80, 0xffffff80081dd424, 0xffffff800824d128, 0xffffff80082ad5a0, 0xffffff80082e8b04, 0xffffff80082e8f2c, 0xffffff80082e8f54 |

## Codeword Slide Check

- Stock raw: `workspace/private/runs/kernel/v2197-stock-kallsyms/kernel.raw`
- Candidate source: `workspace/private/runs/kernel/v2215-perf-regs-ropp-jopp-classifier/result.json`
- Candidate count: `281`

| Rank | Slide | Score | PC Match | LR-4 Match | LR Match |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `0x84ef4` | 428 | 62/62 | 60/60 | 60/60 |
| 2 | `0x84848` | 68 | 17/62 | 0/60 | 0/60 |
| 3 | `0x84e1c` | 68 | 17/62 | 0/60 | 0/60 |
| 4 | `0x85154` | 64 | 16/62 | 0/60 | 0/60 |
| 5 | `0x21cc84` | 64 | 16/62 | 0/60 | 0/60 |
| 6 | `0x21ccdc` | 64 | 16/62 | 0/60 | 0/60 |
| 7 | `0x21d658` | 64 | 16/62 | 0/60 | 0/60 |
| 8 | `0x2258a8` | 64 | 16/62 | 0/60 | 0/60 |
| 9 | `0x2d3ed8` | 64 | 16/62 | 0/60 | 0/60 |
| 10 | `0x2d4168` | 64 | 16/62 | 0/60 | 0/60 |
| 11 | `0x62c5a0` | 64 | 16/62 | 0/60 | 0/60 |
| 12 | `0x21e13c` | 52 | 12/62 | 0/60 | 4/60 |

## Direct Symbol Preview

- Stock map: `workspace/private/runs/kernel/v2197-stock-kallsyms/System.map`
- Text symbols loaded: `77770`

| Source | Count | Address | Symbol | Offset |
| --- | ---: | --- | --- | ---: |
| `ctx_pc` | 11 | `0xffffff8009a4825c` | `_end_hyperdrive` | `283136` |
| `ctx_pc` | 5 | `0xffffff8009a482b4` | `_end_hyperdrive` | `283224` |
| `ctx_pc` | 3 | `0xffffff800832f2d0` | `proc_pid_status` | `872` |
| `ctx_pc` | 2 | `0xffffff8008103bd4` | `irqtime_account_irq` | `356` |
| `ctx_pc` | 1 | `0xffffff8009a28c0c` | `_end_hyperdrive` | `154544` |
| `ctx_pc` | 1 | `0xffffff8008310118` | `locks_free_lock_context` | `0` |
| `ctx_pc` | 1 | `0xffffff8009a480c4` | `_end_hyperdrive` | `282728` |
| `ctx_pc` | 1 | `0xffffff800832f304` | `proc_pid_status` | `924` |
| `ctx_pc` | 1 | `0xffffff80085201c8` | `elv_completed_request` | `224` |
| `ctx_pc` | 1 | `0xffffff800824d0ec` | `__follow_pte_pmd` | `244` |
| `ctx_pc` | 1 | `0xffffff8009a43de8` | `_end_hyperdrive` | `265612` |
| `ctx_pc` | 1 | `0xffffff8009a28a80` | `_end_hyperdrive` | `154148` |
| `ctx_lr` | 4 | `0xffffff8008a34a18` | `scsi_seq_show` | `144` |
| `ctx_lr` | 4 | `0xffffff800832f2cc` | `proc_pid_status` | `868` |
| `ctx_lr` | 4 | `0xffffff800816ddcc` | `tick_setup_periodic` | `6644` |
| `ctx_lr` | 3 | `0xffffff80081dd424` | `bpf_get_file_flag` | `300` |
| `ctx_lr` | 2 | `0xffffff80082e8b04` | `fsnotify_peek_first_event` | `1476` |
| `ctx_lr` | 2 | `0xffffff80085151f0` | `ecc_point_mult` | `112` |
| `ctx_lr` | 2 | `0x000000000044dfb0` | `None` | `None` |
| `ctx_lr` | 2 | `0xffffff800851b814` | `bvec_free` | `148` |
| `ctx_lr` | 1 | `0xffffff800831d118` | `dqget` | `176` |
| `ctx_lr` | 1 | `0xffffff800832f31c` | `proc_pid_status` | `948` |
| `ctx_lr` | 1 | `0xffffff800824d128` | `__follow_pte_pmd` | `304` |
| `ctx_lr` | 1 | `0xffffff80083b919c` | `trace_raw_output_jbd2_handle_start` | `2636` |

## Interpretation

- V2216 promotes the codeword-matched text slide to exact for this boot.
- The exact slide supersedes the V2215 rank-only slide candidate because live instruction words match stock raw bytes.
- Direct stock-map `_end_hyperdrive` labels are no-slide artifacts in this capture, not final function names.
- The useful ROPP-bypass anchor is live perf-event `ctx_pc` plus live `ctx_lr` with codeword reads.
- The saved FP-chain LR slots remain mostly ROPP-encoded and are not a completed unwind path.
- Direct stock-map symbol previews are retained only to show why no-slide range lookup is misleading.

## Source Basis

- `bpf_perf_event_data` exposes `struct pt_regs regs` in the UAPI header.
- `pe_prog_convert_ctx_access` rewrites default perf-event ctx reads through `bpf_perf_event_data_kern->regs`.
- arm64 `pt_regs` layout is `regs[31], sp, pc, pstate`; generated offsets confirm LR=240, SP=248, PC=256.

## Convergence

- Ring saturated: `false`
- Hint: ring not saturated; longer duration can still add information

## Safety

- cgroup_attach: `false`
- flash_reboot: `false`
- partition_or_firmware_write: `false`
- probe_write_user_executed: `false`
- read_only_bpf: `true`
- wifi_action: `false`

## Evidence

- Private run: `workspace/private/runs/kernel/v2216-perf-regs-codeword-sample-ring-5s-20260612-053331`
- Helper SHA-256: `3a16efc217eafeacbcc95a5e6005d0abce02e89ab52ed537df1fc2b193ca3dd7`
