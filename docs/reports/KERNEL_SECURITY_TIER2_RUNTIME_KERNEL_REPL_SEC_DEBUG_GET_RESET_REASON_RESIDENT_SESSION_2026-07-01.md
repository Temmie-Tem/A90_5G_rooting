# Kernel Security Tier-2 Runtime Kernel REPL — sec_debug_get_reset_reason resident-session proof

Date: 2026-07-01

## Decision

PASS. `sec_debug_get_reset_reason()` is live-proven as a no-argument,
read-only Samsung reset-reason getter under the existing sec_debug scalar proof
contract.

Private run evidence:
`workspace/private/runs/kernel/repl-resident-session-sec-debug-get-reset-reason-20260701T122038Z/`

## Static Gate

- Target: `sec_debug_get_reset_reason`
- Link address: `0xffffff80086ed484`
- Resolution: `exact-leaf-map+xref+word-boundary`
- Export candidates: `0`; identity rests on the C2B-fixed System.map label,
  JOPP entry, exact words, direct callsite xrefs, and next-symbol boundary.
- Direct BL xref count: `7`.
- Pinned words: `f0012ec8 b944c900 d65f03c0 00be7bad`
- Next symbol boundary: `sec_debug_get_reset_write_cnt`, delta `0x10`.
- Source declaration: `extern unsigned int sec_debug_get_reset_reason(void)` at
  `include/linux/samsung/debug/sec_debug_user_reset.h:22`.
- Call safety: `SAFE-SCALAR`, no required pointer args, no BL in the pinned
  body, no argument memory flow.

`sec_debug_get_upload_cause()` was excluded because it calls logging helpers.
`sec_debug_get_reset_write_cnt()` remains an adjacent same-shape candidate for a
future batch, but this unit promoted only the single reset-reason target.

## Live Result

Resident-session mode was used:

- Candidate flash: v1-repl `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback flash: v2321 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Flash count: `2`
- Warm reboot before batch: yes
- Completed batches: `1`
- Completed targets: `1`
- Target result: `a90-repl-live-call-proof-sec_debug_get_reset_reason-pass`
- Observed return: `0xffeeffee`, repeated `2` times, stable and in the
  `0..0xffffffff` contract range.
- Cleanup: none required; scalar read-only no-argument leaf.
- Final resident: v2321 `v2321-usb-clean-identity-rodata`
- Final health: `selftest fail=0`

The first post-warm REPL selftest hit transient serial marker loss and recovered
through the harness retry/bridge restart path. The second attempt passed, the
batch completed, and rollback completed cleanly.

The canonical timeline uses the required single top-level `events` schema and
contains all eight required session phase events. Timings from this run:

- Candidate flash: `65.215950s`
- Candidate boot/selftest to ready: `54.655904s`
- Live session total: `58.190330s`
- Warm reboot: `20.879940s`
- Actual one-target live batch: `3.274416s`
- Rollback flash: `64.848177s`
- Rollback boot/health: `48.126153s`
- Total session: `291.053173s`

The run-timing aggregator now sees `12` canonical timelines. With
`batch_size=10`, `resident_batches=10`, and `warm_reboot=15s`, it projects
flash count `20->2`, resident per-target time `14.390s`, `19.77x` speedup
versus unbatched per-unit flash, and `1.98x` speedup versus per-unit in-boot
batching on the current evidence set.

## Final State

After rollback, standalone `a90ctl version` and `a90ctl selftest` confirmed
v2321 resident state:

- `version: 0.9.285 build=v2321-usb-clean-identity-rodata`
- `selftest: pass=11 warn=1 fail=0`

No boot artifacts, raw logs, runtime pointers, or private JSON evidence are
committed by this report.
