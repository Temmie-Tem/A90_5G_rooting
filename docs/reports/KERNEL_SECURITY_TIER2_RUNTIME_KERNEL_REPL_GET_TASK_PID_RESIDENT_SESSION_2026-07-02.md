# Kernel Security Tier-2 Runtime Kernel REPL - get_task_pid resident-session proof

- Date: 2026-07-02 KST / 2026-07-01 UTC
- Scope: add and live-prove `get_task_pid(init_task, PIDTYPE_PID)` as a target-specific balanced refcount primitive.
- Device action: v1-repl candidate flash once, mandatory resident warm reboot, one bounded batch, v2321 rollback once.
- Public result: PASS on retry, rolled back to `v2321-usb-clean-identity-rodata`, final `selftest fail=0`.

## Target

`get_task_pid()` was selected because it is not a `/proc` or `/sys` state getter. It proves a new ABI shape: borrowed `struct task_struct *` input, scalar enum input, returned owned `struct pid *` ref, and mandatory `put_pid()` cleanup.

The proof contract is intentionally narrow:

- Input: verified global `init_task` pointer and scalar `PIDTYPE_PID` only.
- Direct observation before call: `init_task->thread_pid` is a sane kernel pointer, its `numbers[level].nr` is PID `0`, and its refcount is nonzero.
- Return: `get_task_pid(init_task, PIDTYPE_PID)` returns exactly the directly observed `init_task->thread_pid`.
- Cleanup: `put_pid(returned)` is always attempted for a sane returned pointer.
- Success condition: refcount rises after `get_task_pid` and returns to the initial value after `put_pid`.

## Static Gate

The generic call-safety gate remains closed:

- Symbol: `get_task_pid`
- Link address: `0xffffff80080d8204`
- Resolution method: `export-recovery`
- Export candidates: `1`
- Map agrees with export: yes
- Direct BL xrefs: `5`
- JOPP entry: yes
- In-body BL count: `2`
- In-body callees: `__rcu_read_lock`, `__rcu_read_unlock`
- Pre-call pointer deref: none
- Arg-derived memory base: `x0` only
- Source declaration: `extern struct pid * get_task_pid(struct task_struct *task, enum pid_type type)` at `include/linux/pid.h:94`
- Generic gate tier: `DENY`
- Target-specific advisory tier: `CONTEXT-SENSITIVE`, blocked by `context-sensitive-disasm-call`

Cleanup identity was separately pinned:

- Symbol: `put_pid`
- Link address: `0xffffff80080d753c`
- Resolution method for cleanup: `export-recovery` with `allow_pre_arg_deref=True`
- Direct BL xrefs: `101`
- Next symbol: `free_pid` at `+0x70`
- Source declaration: `extern void put_pid(struct pid *pid)` at `include/linux/pid.h:90`
- Generic classification remains `DENY` because it dereferences and may free the supplied pointer.

Pinned `get_task_pid` body words:

```text
ca1103d0 a9be43fd a9014ff4 910003fd
2a0103f3 aa0003f4 9401ccda 34000053
f9437694 52800308 9ba85268 f9439113
b40000d3 f9800271 885f7e68 11000508
88097e68 35ffffa9 9401ccd4 aa1303e0
a9414ff4 a8c243fd ca11021e d65f03c0
d503201f 00be7bad
```

## Live Run

Passing run directory:

```text
workspace/private/runs/kernel/repl-resident-session-get-task-pid-retry-20260701T163708Z/
```

Harness summary:

- Decision: `a90-repl-resident-session-pass`
- Candidate flashed once: yes
- Warm reboot between batches: yes
- Completed targets: `1/1`
- Flash count: `2`
- Rollback flashed once: yes
- Timeline errors: none

Target result:

- Decision: `a90-repl-live-call-proof-get_task_pid-pass`
- Proof status: `trusted-under-init-task-pid-refcount-balanced-contract`
- Direct PID number observation: `0x0`
- Return matched direct `init_task->thread_pid`: yes
- Refcount initial: `1`
- Refcount after get: `2`
- Refcount after put: `1`
- Cleanup attempted: yes
- Cleanup OK: yes

Raw runtime pointers and KASLR slide remain private-only in the run directory.

## Failed First Attempt

First run directory:

```text
workspace/private/runs/kernel/repl-resident-session-get-task-pid-20260701T163156Z/
```

The first attempt failed before calling `get_task_pid`: the host-side proof contract incorrectly required `init_task->thread_pid` to be a lowmem heap pointer. Live observation showed it is a sane kernel image/data pointer, which is valid for the statically owned init PID object. No target call was made. The harness rolled back through `rollback-flash-finally`, and rollback-finally health confirmed `v2321-usb-clean-identity-rodata` with `selftest pass=11 warn=1 fail=0`.

The contract was corrected to require a nonzero sane kernel pointer while keeping return equality and refcount restoration mandatory. The retry above then passed.

## Health And Rollback

Preflight confirmed the rollback/fallback boot images:

- v1-repl candidate SHA: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- v2321 rollback SHA: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- v2237 fallback SHA: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- v48 fallback present: yes

Baseline v2321 health passed before the live run. The candidate booted and health checks passed. The REPL selftest was clean before the batch. Post-batch candidate health passed with `selftest fail=0`.

Rollback to v2321 completed through `native_init_flash.py` with matching v2321 readback SHA. Final rollback `version/status/selftest` passed:

- Resident build: `v2321-usb-clean-identity-rodata`
- Final selftest: `pass=11 warn=1 fail=0`

## Timing

Canonical `timeline.json` uses the single top-level `events` schema and includes the required phase events.

| Phase | Seconds |
| --- | ---: |
| candidate flash | 64.133 |
| candidate boot/health | 54.279 |
| resident warm reboot | 32.664 |
| post-reboot REPL ready | 32.251 |
| live target batch | 7.361 |
| post-batch health | 1.277 |
| rollback flash | 64.782 |
| rollback boot/health | 0.817 |
| candidate start to rollback ready | 257.608 |

The timing aggregator now parses `26/74` canonical timelines. With `batch_size=10`, `resident_batches=10`, and `warm_reboot=15s`, it projects:

- Flash count: `20 -> 2`
- Old in-boot batch: `29.920s/target`
- Resident session: `14.203s/target`
- Speedup: `21.07x` versus per-unit flash, `2.11x` versus per-unit in-boot batch

## Validation

Host validation:

- `py_compile` for `a90_repl.py` and `tests/test_a90_repl.py`
- `CallSafetyClassificationTests`
- `SelftestIntegrationTests.test_call_proof_get_task_pid_passes_with_balanced_refcount_contract`
- `tests.test_a90_repl_resident_session`
- `tests.test_analyze_repl_run_timing`
- resident-session dry-run with `--batch get_task_pid`
- `git diff --check`

## Outcome

`get_task_pid()` is promoted as live-proven only under the `init_task + PIDTYPE_PID + balanced put_pid` contract. This does not make `put_pid()` or arbitrary `get_task_pid(task,type)` globally callable; both remain outside mass auto-call.
