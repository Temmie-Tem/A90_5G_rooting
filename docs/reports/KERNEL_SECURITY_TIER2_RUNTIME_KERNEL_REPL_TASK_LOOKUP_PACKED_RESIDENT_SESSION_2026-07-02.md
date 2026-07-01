# Kernel REPL packed resident-session task lookup proofs

Date: 2026-07-02 KST

## Scope

Add and live-prove two task lookup helpers under target-specific contracts:

- `find_task_by_pid_ns`: scalar PID `1` plus a `struct pid_namespace *` observed from an
  owned `find_get_pid(1)` anchor, returning a borrowed `struct task_struct *`
- `find_task_by_vpid`: scalar PID `1` in the current namespace, returning a borrowed
  `struct task_struct *`

Both functions remain `DENY` at the global call-safety gate. They are not promoted as
general auto-call targets; the only trusted path is the bounded proof that creates an
owned PID anchor, cross-checks the returned task's `task->thread_pid`, and balances the
anchor with `put_pid`.

## Static Gate

`find_task_by_pid_ns`:

- Link address: `0xffffff80080d80ac`
- Resolution: generic C1 export verification unavailable, so the proof uses the
  System.map function entry plus exact body words, next-symbol boundary, source
  signature, direct BL xrefs, and live cross-check
- Source declaration: `extern struct task_struct * find_task_by_pid_ns(pid_t nr, struct pid_namespace *ns)`
  at `include/linux/sched.h:1785`
- Body pin: exact body words, leaf/no in-body BL, next symbol `find_task_by_vpid` at
  `+0xa0`
- Generic call-safety: `DENY`, `auto_call_allowed=false`, seeded
- Proof-specific contract: `SAFE-WITH-VALID-PTR` only when x1 is the namespace pointer
  read from the owned PID anchor

`find_task_by_vpid`:

- Link address: `0xffffff80080d814c`
- Resolution: generic C1 export verification unavailable, so the proof uses the
  System.map function entry plus exact body words, next-symbol boundary, source
  signature, direct BL xrefs, scalar-flow classifier evidence, and live cross-check
- Source declaration: `extern struct task_struct * find_task_by_vpid(pid_t nr)` at
  `include/linux/sched.h:1784`
- Body pin: exact body words, leaf/no in-body BL, next symbol `get_task_pid` at `+0xb8`
- Generic call-safety: `DENY`, `auto_call_allowed=false`, seeded
- Proof-specific contract: `SAFE-SCALAR` for scalar PID `1` only, with the returned
  borrowed task verified against an independently owned PID anchor

Shared anchor/cleanup:

- Anchor: `find_get_pid`, link `0xffffff80080d82ec`, declaration
  `extern struct pid * find_get_pid(int nr)`, generic `DENY`, target-specific
  `CONTEXT-SENSITIVE` due the RCU call pair
- Cleanup: `put_pid`, link `0xffffff80080d753c`, declaration
  `extern void put_pid(struct pid *pid)`

## Code Changes

- Added `CALL_SAFETY_DENY` seeds for `find_task_by_pid_ns` and `find_task_by_vpid`.
- Added exact body-word and next-symbol-boundary pins for both helpers.
- Added source-signature hints for `include/linux/sched.h`.
- Added `_run_call_proof_find_task_lookup()`, shared by both targets.
- Added a pre-write `dmesg` drain in `op_sh()` so stale `A90R` records are less likely
  to contaminate later result parsing.
- Extended fake transport and focused tests for individual proofs plus the packed fake
  batch.

## Live Evidence

Two packed resident sessions were run. Both obeyed the operator correction: no
one-target resident session, `max_batch_size=30`, per-target result flush, candidate
`v1-repl` flash once, warm reboot before the batch, and rollback to `v2321` at the end.

### Attempt 1: 13-target packed session

Private run directory:

`workspace/private/runs/kernel/repl-resident-session-task-lookup-packed-batch-20260701T180337Z/`

Plan:

- `target_count=13`
- `max_batch_size=30`
- Batch:
  `find_task_by_pid_ns, find_task_by_vpid, pid_task, find_pid_ns, find_vpid, find_get_pid, get_task_pid, task_active_pid_ns, pid_nr_ns, pid_vnr, __task_pid_nr_ns, task_prio, task_curr`

Flushed target results before the batch exception:

- `find_task_by_pid_ns`: PASS
- `find_task_by_vpid`: PASS
- `pid_task`: PASS
- `find_pid_ns`: PASS

Exception:

- `find_vpid changed pid refcount: anchor=6 after=9`

Decision for this run: do not promote the packed session as a batch pass. The four
completed target result files were flushed before the exception and are valid per-target
evidence.

Timing:

- Candidate flash: `64.205s`
- Candidate boot/health: `42.674s`
- Warm reboot: `33.580s`
- Batch live window: `35.770s`
- Rollback flash: `64.332s`
- Rollback boot/health: `0.819s`
- Candidate-start to rollback-ready total: `274.283s`

### Attempt 2: max30 packed session after result-channel pre-drain

Private run directory:

`workspace/private/runs/kernel/repl-resident-session-task-lookup-preflush-max30-batch-20260701T181136Z/`

Plan:

- `target_count=30`
- `max_batch_size=30`
- Batch:
  `find_task_by_pid_ns, find_task_by_vpid, pid_task, find_pid_ns, find_vpid, find_get_pid, get_task_pid, task_active_pid_ns, pid_nr_ns, pid_vnr, __task_pid_nr_ns, task_prio, task_curr, current_umask, in_group_p, in_egroup_p, get_taint, test_taint, sec_debug_is_enabled, sec_debug_level, sec_debug_get_reset_reason, sec_debug_get_reset_write_cnt, sec_debug_get_reset_reason_str, slab_is_available, debugfs_initialized, tracefs_initialized, cpu_mitigations_off, get_state_synchronize_rcu, get_state_synchronize_sched, is_boot_recovery`

Flushed target results before the batch exception:

- `find_task_by_pid_ns`: PASS
- `find_task_by_vpid`: PASS
- `pid_task`: PASS

Exception:

- `put_pid did not restore anchor pid refcount: anchor=6 after_find_pid_ns=6 after_put=8`

Decision for this run: do not promote the packed session as a batch pass. The second
failure hit an older PID borrowed-pointer canary after the two new target results had
already flushed. Per the fails-twice rule, no further live retries were made.

Timing:

- Candidate flash: `64.220s`
- Candidate boot/health: `32.590s`
- Warm reboot: `33.212s`
- Batch live window: `31.491s`
- Rollback flash: `64.283s`
- Rollback boot/health: `0.771s`
- Candidate-start to rollback-ready total: `262.826s`

## New Target Results

`find_task_by_pid_ns` passed in both packed sessions:

- Decision: `a90-repl-live-call-proof-find_task_by_pid_ns-pass`
- Proof status: `trusted-under-scalar-namespace-task-borrowed-pointer-contract`
- Embedded pid number: `0x1`
- Return check: returned a sane task pointer whose `task->thread_pid` matched the owned
  PID 1 anchor
- Refcount path in both sessions: `6 -> 6 -> 5` after anchor, after target call, after
  `put_pid`
- Cleanup: `put_pid` called once for the anchor ref, OK

`find_task_by_vpid` passed in both packed sessions:

- Decision: `a90-repl-live-call-proof-find_task_by_vpid-pass`
- Proof status: `trusted-under-current-namespace-task-borrowed-pointer-contract`
- Embedded pid number: `0x1`
- Return check: returned a sane task pointer whose `task->thread_pid` matched the owned
  PID 1 anchor
- Refcount path in both sessions: `6 -> 6 -> 5` after anchor, after target call, after
  `put_pid`
- Cleanup: `put_pid` called once for the anchor ref, OK

Raw runtime pointers and KASLR slide stayed private-only.

## Final Device State

Both live attempts used the rollback-finally path and ended on clean `v2321`:

- Resident build: `v2321-usb-clean-identity-rodata`
- `version`: `0.9.285 build=v2321-usb-clean-identity-rodata`
- `status`: `BOOT OK`, `selftest fail=0`
- `selftest`: `pass=11 warn=1 fail=0`

Post-report standalone recheck with repo-local `a90ctl.py` also confirmed the same
resident state: `version` returned `0.9.285 build=v2321-usb-clean-identity-rodata`,
`status` reported `BOOT OK` and `selftest fail=0`, and `selftest` reported
`pass=11 warn=1 fail=0`.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- Focused unittest set covering command buffers, live math fake transport, call-safety
  classification, source signatures, both new task lookup proofs, and the packed fake
  PID borrowed batch
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --no-objdump find_task_by_pid_ns find_task_by_vpid find_get_pid put_pid`
- `git diff --check`

Live validation:

- Packed 13-target resident session: new targets passed, older canary failed later,
  rollback clean
- Packed max30 resident session: new targets passed again, older canary failed later,
  rollback clean

## Decision

Promote the two target-specific function-map entries:

- `find_task_by_pid_ns`: live-proven only for scalar PID `1` plus the namespace pointer
  observed from an owned PID anchor; return is borrowed and must be verified against the
  anchor task contract.
- `find_task_by_vpid`: live-proven only for scalar PID `1` with an independently owned
  PID anchor used as a cross-check; return is borrowed and must be verified against the
  anchor task contract.

Do not promote the 13-target or max30 packed sessions as batch-pass evidence. The packed
resident machinery preserved per-target evidence correctly, but the older PID borrowed
canary refcount/readback path is unstable under the packed session. The next live unit
should harden the result channel and canary accounting, for example with a unique per-op
marker or stronger `dmesg -c`/result-channel isolation, before another max30 batch run.
