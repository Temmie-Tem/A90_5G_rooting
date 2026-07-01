# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: pid_vnr

Date: 2026-07-01

## Scope

- Target proved: `pid_vnr`.
- Result: live proof passed; target promoted only under the borrowed
  `init_task->thread_pid` input contract.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-pid-vnr-20260701T032646Z/`.

This target extends the pid/namespace proof chain from explicit namespace input
(`pid_nr_ns(pid, ns)`) to the current-namespace helper
`pid_vnr(pid)`. It is not promoted for arbitrary `struct pid *` values.

## Candidate Selection

`pid_vnr` was selected from the same pid namespace neighborhood as
`task_active_pid_ns(init_task)` and `pid_nr_ns(init_task->thread_pid, active_ns)`.
The previous proof established the direct `init_task->thread_pid` and active namespace
observation path. This proof passes only:

- x0 = direct read-only `init_task->thread_pid`

`pid_vnr` obtains the current task namespace internally through `sp_el0`. The proof cannot
directly peek that internal current pointer, so the current namespace match is recorded as
inferred by return equality against the directly observed init namespace pid number.

## Static Candidate

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `pid_vnr` | `0xffffff80080d8414` | `SAFE-WITH-VALID-PTR`; x0 read-only deref; leaf | `pid_t pid_vnr(struct pid *pid)` |

Static gates:

- Resolution method: `export-recovery`, verified, with map agreement.
- Direct BL xrefs: `27`.
- Source declaration: `include/linux/pid.h:181`.
- Next-symbol boundary: `__task_pid_nr_ns` at `+0x58`.
- Pinned identity words cover the current body through the next sentinel:
  `mrs x8,sp_el0`, `ldr x8,[x8,#1824]`, current namespace lookup through
  `pid->numbers[level].ns`, x0 null check, `ldr w10,[x0,#4]`, level compare,
  namespace pointer compare, `ldr w0,[x9,#72]`, `ret`, next-entry sentinel.
- C1 allowlist requires x0 as `init-task-thread_pid-struct-pid`.

Input contract:

- Call `pid_vnr(init_task->thread_pid)`.
- `thread_pid` is read from `init_task + 0x720`.
- The observed pid level and namespace level must be equal and inside the proof bound.
- The borrowed `struct pid *` is not freed, retained, or generalized to other task/pid objects.

Return contract:

- Before calling, read the expected pid number directly from
  `thread_pid + 0x48 + (active_ns->level << 5)`.
- The observed `pid_t` must be in the sane proof range `0..0x400000`.
- Two short-repeat calls must exactly match the direct read-only observation.

## Live Result

The live proof passed:

- `thread_pid_nonzero=true`
- `active_namespace_nonzero=true`
- `pid_level=0`
- `namespace_level=0`
- direct expected pid nr: `0x0`
- current namespace observation: `inferred-by-return-equality-not-directly-peeked`

| Case | Expected | Return value | Result |
| --- | ---: | ---: | --- |
| `init-task-thread-pid-current-ns-1` | `0x0` | `0x0` | pass |
| `init-task-thread-pid-current-ns-2` | `0x0` | `0x0` | pass |

All live checks passed:

- `all_returns_match_direct_observation=true`
- `current_namespace_match_inferred_by_return=true`
- `repeat_count=2`
- `raw_runtime_values_redacted=true`
- `borrowed_pointer_redacted=true`

Post-proof candidate selftest stayed clean with `selftest fail=0`. Rollback to v2321
completed with matching readback SHA, and final `status` confirmed
`selftest pass=11 warn=1 fail=0`.

## Code Outcome

`pid_vnr` is now represented in the call-proof machinery as:

- `SAFE-WITH-VALID-PTR`
- required pointer args:
  - x0 = `init-task-thread_pid-struct-pid`
- return kind: `pid_t`
- live-proven function-map entry only under the `init_task->thread_pid`
  direct-observation contract

The fake REPL transport now models `pid_vnr(thread_pid)` and asserts that the proof
passes only `init_task->thread_pid`, so host tests exercise the same contract.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-pid-vnr-20260701T032646Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `65.0s` |
| candidate flash helper total | `65.747s` |
| candidate boot-ready after helper done | `16.0s` |
| candidate explicit health retry | `0.0s` |
| live call-proof | `8.0s` |
| post-proof candidate health | `1.0s` |
| rollback flash start to helper done | `64.0s` |
| rollback flash helper total | `63.694s` |
| rollback boot-ready after helper done | `9.0s` |
| final status health | `1.0s` |
| candidate start to final status done | `216.0s` |

The candidate explicit selftest initial attempt hit serial END-marker/framing loss; an
immediate retry passed. The final explicit selftest commands returned rc=0 but lost the
body line in serial output, so the closing health gate used `status`, which showed
`selftest pass=11 warn=1 fail=0`.

## Validation

Device validation:

- Preflight confirmed candidate, v2321, v2237, and v48 SHA values.
- TWRP recovery image was present.
- Bridge status passed before flash.
- Baseline v2321 `version`, `status`, and `selftest` passed.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- TWRP recovery path was exercised by the flash helper.
- Candidate helper `version/status` health passed.
- Explicit candidate health retry passed after serial framing noise.
- Live proof passed and wrote evidence JSON.
- Post-proof candidate `selftest` passed with `selftest fail=0`.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final v2321 `status` passed with `selftest pass=11 warn=1 fail=0`.

Host validation:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Classifier CLI for `pid_vnr`, `pid_nr_ns`, and `task_active_pid_ns`:
  `SAFE-WITH-VALID-PTR=3`, `ok=true`.
- Focused tests for the classifier/source/fake-proof path: `Ran 3 tests`, `OK`.
- Full `tests.test_a90_repl`: `Ran 184 tests`, `OK`.
- `git diff --check`: clean.
