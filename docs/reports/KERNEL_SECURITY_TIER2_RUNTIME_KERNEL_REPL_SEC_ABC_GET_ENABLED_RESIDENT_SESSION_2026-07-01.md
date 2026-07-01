# Kernel Security Tier-2 Runtime Kernel REPL — sec_abc_get_enabled resident-session proof

Date: 2026-07-01

## Decision

PASS. `sec_abc_get_enabled()` is live-proven under a target-specific read-only
contract, without adding it to the global `CALL_SAFETY_SEEDS` auto-call gate.

Private run evidence:
`workspace/private/runs/kernel/repl-resident-session-sec-abc-get-enabled-20260701T120126Z/`

## Static Gate

- Target: `sec_abc_get_enabled`
- Link address: `0xffffff800935c62c`
- Resolution: `exact-leaf-export+word-boundary`
- Export candidates: `1`; selected candidate map-agrees with export.
- Direct BL xref count: `1`, sample site `0xffffff8009241848`.
- Pinned words: `d0011708 b9478900 d65f03c0 00be7bad`
- Next symbol boundary: `sec_abc_send_event`, delta `0x10`.
- Source declaration: `extern int sec_abc_get_enabled(void)` at
  `include/linux/sti/abc_common.h:118`.
- Return contract source enum: `ABC_DISABLED`, `ABC_TYPE1_ENABLED`,
  `ABC_TYPE2_ENABLED`, so the proof accepts only stable values in `0..2`.

The global call-safety classifier still returns `DENY` and
`auto_call_allowed=false` because the target is not in the vetted seed
whitelist. The target-specific advisory gate returns `SAFE-SCALAR` with
`candidate_safe=true`; this proof path is therefore target-specific only, not a
new global auto-call permission.

## Live Result

Resident-session mode was used:

- Candidate flash: v1-repl `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback flash: v2321 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Flash count: `2`
- Warm reboot between batches: yes
- Completed batches: `1`
- Completed targets: `1`
- Target result: `a90-repl-live-call-proof-sec_abc_get_enabled-pass`
- Observed return: `0x0`, repeated `2` times, stable and in contract range.
- Cleanup: none required; scalar read-only no-argument leaf.
- Final resident: v2321 `v2321-usb-clean-identity-rodata`
- Final health: `selftest fail=0`

The canonical timeline uses the required single top-level `events` schema and
contains all eight required session phase events. Timings from this run:

- Candidate flash: `64.100786s`
- Candidate boot/selftest to ready: `54.195668s`
- Live session total: `65.943745s`
- Warm reboot: `32.662513s`
- Actual one-target live batch: `3.050100s`
- Rollback flash: `63.650129s`
- Rollback boot/health: `0.844144s`
- Total session: `248.751145s`

The run-timing aggregator now sees `11` canonical timelines. With
`batch_size=10`, `resident_batches=10`, and `warm_reboot=15s`, it projects
flash count `20->2`, resident per-target time `14.821s`, `19.15x` speedup
versus unbatched per-unit flash, and `1.91x` speedup versus per-unit in-boot
batching on the current evidence set.

## Final State

After rollback, `a90ctl version/status/selftest` confirmed v2321 resident state:

- `version: 0.9.285 build=v2321-usb-clean-identity-rodata`
- `selftest: pass=11 warn=1 fail=0`
- Storage remains SD-backed and writable.

No boot artifacts, raw logs, runtime pointers, or private JSON evidence are
committed by this report.
