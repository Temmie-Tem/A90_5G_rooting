# Kernel REPL resident-session proof: PID borrowed batch

Date: 2026-07-02 KST

## Scope

Promote a packed resident-session PID borrowed-pointer batch with two target-specific
proofs in one `v1-repl` flash session:

- `pid_task`: owned `find_get_pid(1)` `struct pid *` anchor plus scalar `PIDTYPE_PID`,
  returning a borrowed `task_struct *`
- `find_pid_ns`: scalar PID `1` plus the PID namespace pointer observed from the owned
  `find_get_pid(1)` anchor, returning the same borrowed `struct pid *`

Both targets remain outside the global auto-call gate. They are explicit `DENY` seeds and
are callable only through their bounded proof contracts.

## Static Gate

`pid_task`:

- Link address: `0xffffff80080d807c`
- Resolution: verified by relocated export recovery; one export candidate; map agrees with export
- Source declaration: `extern struct task_struct * pid_task(struct pid *pid, enum pid_type)`
  at `include/linux/pid.h:91`
- Body pin: exact body words, leaf/no in-body BL, next symbol `find_task_by_pid_ns` at `+0x30`
- Generic call-safety: `DENY`, `auto_call_allowed=false`, seeded
- Target-specific advisory: `DENY`; x1 is a bounded enum in the proof but participates in
  memory-base flow, so the generic classifier stays fail-closed

`find_pid_ns`:

- Link address: `0xffffff80080d7d4c`
- Resolution: verified by relocated export recovery; one export candidate; map agrees with export
- Source declaration: `extern struct pid * find_pid_ns(int nr, struct pid_namespace *ns)`
  at `include/linux/pid.h:118`
- Body pin: exact body words, leaf/no in-body BL, next symbol `find_vpid` at `+0x90`
- Generic call-safety: `DENY`, `auto_call_allowed=false`, seeded
- Target-specific advisory: `SAFE-WITH-VALID-PTR`; memory flow is attributed to the x1
  namespace pointer supplied from the owned anchor

Shared anchor/cleanup:

- Anchor: `find_get_pid`, link `0xffffff80080d82ec`, declaration
  `extern struct pid * find_get_pid(int nr)`, generic `DENY`, target-specific
  `CONTEXT-SENSITIVE` due the RCU call pair
- Cleanup: `put_pid`, link `0xffffff80080d753c`, next symbol `free_pid` at `+0x70`,
  source declaration `extern void put_pid(struct pid *pid)`

## Live Result

Successful resident-session run:

`workspace/private/runs/kernel/repl-resident-session-pid-borrowed-batch-20260701T174344Z/`

Batch result:

- Session decision: `a90-repl-resident-session-pass`
- Completed targets: `2/2`
- Completed batches: `1/1`
- Flash count: `2`
- Timeline schema: canonical top-level `events` only; `timeline_errors=[]`

`pid_task` result:

- `decision`: `a90-repl-live-call-proof-pid_task-pass`
- Contract: `find_get_pid(1)` owned anchor, then `pid_task(anchor, PIDTYPE_PID)` borrowed lookup
- Embedded pid number: `0x1`
- Return check: returned task had `task->thread_pid` equal to the owned PID 1 anchor
- Refcount path: `6 -> 6 -> 5` after anchor, after `pid_task`, after `put_pid`
- Cleanup: `put_pid` called once for the anchor ref, OK

`find_pid_ns` result:

- `decision`: `a90-repl-live-call-proof-find_pid_ns-pass`
- Contract: `find_get_pid(1)` owned anchor, observe anchor namespace, then
  `find_pid_ns(1, ns)` borrowed lookup
- Embedded pid number: `0x1`
- Return check: returned the same pid pointer as the owned `find_get_pid(1)` anchor
- Refcount path: `6 -> 6 -> 5` after anchor, after `find_pid_ns`, after `put_pid`
- Cleanup: `put_pid` called once for the anchor ref, OK

Raw runtime pointers and KASLR slide stayed private-only.

## Resident-Session Compliance

This is the first PID borrowed-pointer proof run promoted under the operator correction that
forbids one-target resident sessions. The harness now rejects single-target resident plans
before any device action. A previous `pid_task` single-target resident run was already in
flight before the correction and rolled back cleanly; it is not used as the promoted evidence.

Successful run behavior:

- Candidate `v1-repl` flashed once
- Mandatory warm reboot before the batch: yes
- Per-target result flush: yes
- Rollback `v2321` flashed once at session end
- Actual session size: `2` targets
- Actual flash amortization: `2 flashes / 2 targets = 1.0 flash per target`

Final device health after rollback:

- Resident build: `v2321-usb-clean-identity-rodata`
- `version`: `0.9.285 build=v2321-usb-clean-identity-rodata`
- `status`: `BOOT OK`, `selftest fail=0`
- `selftest`: `pass=11 warn=1 fail=0`

Phase timings from the successful run:

- Candidate flash: `64.262s`
- Candidate boot/health: `53.803s`
- Warm reboot: `32.666s`
- Batch REPL selftest readiness after warm reboot: `38.025s`
- Live target batch: `15.537s`
- Rollback flash: `64.892s`
- Rollback boot/health: `0.847s`
- Candidate-start to rollback-ready total: `271.358s`

Timing aggregator after this run:

- Timelines found: `79`
- Canonical runs used: `31`
- Resident projection: `13.749s/target`
- Speedup vs unbatched per-unit flash: `21.50x`
- Speedup vs per-unit in-boot batching: `2.15x`
- Modeled flash count: `20 -> 2`

The projection remains a model for a packed `batch_size=10`, `resident_batches=10` session.
The measured result for this specific promoted session is the actual `2` targets, `2` flashes,
and `271.358s` total wall time above.

## Validation

Host validation:

- `python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py workspace/public/src/scripts/revalidation/a90_repl_resident_session.py tests/test_a90_repl.py tests/test_a90_repl_resident_session.py`
- Focused unittest set:
  - `CallSafetyClassificationTests.test_proven_live_call_targets_stay_safe`
  - `CallSafetyClassificationTests.test_seed_inventory_summary_counts_tiers`
  - `CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args`
  - `SelftestIntegrationTests.test_call_proof_pid_task_passes_with_borrowed_task_contract`
  - `SelftestIntegrationTests.test_call_proof_find_pid_ns_passes_with_namespace_borrowed_pid_contract`
  - `SelftestIntegrationTests.test_call_proof_pid_borrowed_batch_candidates_pass_in_one_fake_session`
  - resident-session parse tests for accepting multi-target batches and rejecting single-target plans
- `a90_repl.py call-safety-classify ... pid_task find_pid_ns find_get_pid put_pid`
- Resident-session dry-run with `--batch pid_task,find_pid_ns`
- Single-target resident dry-run with `--batch pid_task` failed host-side as expected
- Run-timing aggregator
- `git diff --check`

Live validation:

- `a90_repl_resident_session.py --batch pid_task,find_pid_ns`
- Final standalone `a90ctl version/status/selftest` independently confirmed rollback health.

## Function-Map Entries

`pid_task` is live-proven only under this target-specific contract:

`owned find_get_pid(1) struct pid anchor plus scalar PIDTYPE_PID only; pid pointer remains
owned by the proof until put_pid cleanup and pid_task return is treated as borrowed`.

`find_pid_ns` is live-proven only under this target-specific contract:

`scalar PID number 1 plus the pid namespace pointer directly observed from an owned
find_get_pid(1) anchor; proof treats find_pid_ns return as borrowed and keeps the anchor
owned until put_pid cleanup`.

Both remain unsuitable for global auto-call.
