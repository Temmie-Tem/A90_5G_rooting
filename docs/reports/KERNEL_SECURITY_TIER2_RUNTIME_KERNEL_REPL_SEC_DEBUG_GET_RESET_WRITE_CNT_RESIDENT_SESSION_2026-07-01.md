# Kernel Security Tier-2 Runtime Kernel REPL — sec_debug_get_reset_write_cnt resident-session proof

Date: 2026-07-01

## Decision

PASS. `sec_debug_get_reset_write_cnt()` is live-proven as a no-argument,
read-only Samsung reset-header write-count getter under the existing
sec_debug scalar proof contract.

Private run evidence:
`workspace/private/runs/kernel/repl-resident-session-sec-debug-get-reset-write-cnt-20260701T123235Z/`

## Static Gate

- Target: `sec_debug_get_reset_write_cnt`
- Link address: `0xffffff80086ed494`
- Resolution: `exact-leaf-map+xref+word-boundary`
- Export candidates: `0`; identity rests on the C2B-fixed System.map label,
  JOPP entry, exact words, direct callsite xrefs, and next-symbol boundary.
- Direct BL xref count: `7`.
- Pinned words: `f0012ec8 b944cd00 d65f03c0 00be7bad`
- Next symbol boundary: `sec_debug_get_reset_reason_str`, delta `0x10`.
- Source declaration: `extern int sec_debug_get_reset_write_cnt(void)` at
  `include/linux/samsung/debug/sec_debug_user_reset.h:25`.
- Call safety: `SAFE-SCALAR`, no required pointer args, no BL in the pinned
  body, no argument memory flow.

The source-side reset header defines `write_times` as `uint32_t`. The exported
getter is declared as `int`, so this proof records the raw lower-32 return value
and only requires it to remain stable in the bounded proof.

## Live Result

Resident-session mode was used:

- Candidate flash: v1-repl `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback flash: v2321 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Flash count: `2`
- Warm reboot before batch: yes
- Completed batches: `1`
- Completed targets: `1`
- Target result: `a90-repl-live-call-proof-sec_debug_get_reset_write_cnt-pass`
- Observed raw return: `0xffffffff`, repeated `2` times, stable and in the
  raw `0..0xffffffff` contract range. Interpreted as a signed 32-bit `int`,
  this is `-1`; the report does not assign stronger semantic meaning.
- Cleanup: none required; scalar read-only no-argument leaf.
- Final resident: v2321 `v2321-usb-clean-identity-rodata`
- Final health: `selftest fail=0`

Candidate REPL selftest hit transient serial marker loss and recovered through
the harness retry/bridge restart path. The batch completed, rollback completed,
and standalone post-rollback `a90ctl version` plus `a90ctl selftest` passed
after a bridge resync.

The canonical timeline uses the required single top-level `events` schema and
contains all eight required session phase events. Timings from this run:

- Candidate flash: `64.126462s`
- Candidate boot/selftest to ready: `35.837245s`
- Live session total: `65.777249s`
- Warm reboot: `33.232281s`
- Actual one-target live batch: `3.097960s`
- Rollback flash: `64.073198s`
- Rollback boot/health: `1.066533s`
- Total session: `230.899706s`

The run-timing aggregator now sees `13` canonical timelines. With
`batch_size=10`, `resident_batches=10`, and `warm_reboot=15s`, it projects
flash count `20->2`, resident per-target time `14.031s`, `19.98x` speedup
versus unbatched per-unit flash, and `2.00x` speedup versus per-unit in-boot
batching on the current evidence set.

## Final State

After rollback and bridge resync, standalone `a90ctl version` and
`a90ctl selftest` confirmed v2321 resident state:

- `version: 0.9.285 build=v2321-usb-clean-identity-rodata`
- `selftest: pass=11 warn=1 fail=0`

No boot artifacts, raw logs, runtime pointers, or private JSON evidence are
committed by this report.
