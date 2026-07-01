# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: can_do_mlock

Date: 2026-07-01

## Scope

- Target proved: `can_do_mlock`.
- Result: live proof passed; target promoted under a no-argument current-task mlock
  allowance bool contract.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-can-do-mlock-20260701T010937Z/`.

This target extends the REPL's read-only current-process state observation surface. It is not
promoted as a general call primitive; it is trusted only under the exact no-argument bool proof
contract below.

## Candidate Selection

Host sweep compared current-state candidates outside the already covered `CALL_PROOF_TARGETS`
inventory. `get_debug_reset_header` was rejected for this unit because the current-image body
allocates, reads a debug partition, prints, and frees. `is_current_pgrp_orphaned` was parked as a
heavier tasklist read-lock traversal. `can_do_mlock` was selected because the static body is only
0x40 bytes, takes no arguments, observes current task mm/credential state, and returns a bool.

## Static Candidate

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `can_do_mlock` | `0xffffff800824bb0c` | `SAFE-SCALAR`; no pointer args | `extern bool can_do_mlock(void)` |

Static gates:

- Resolution method: `export-recovery`, verified.
- Direct BL xrefs: `1`.
- Source declaration: `include/linux/mm.h:1303`.
- Next-symbol boundary: `clear_page_mlock` at `+0x40`.
- The proof pins all 16 identity words, including the `capable(CAP_IPC_LOCK)` call path,
  final `ret`, and next-entry sentinel.
- C1 allowlist requires no valid pointer arguments.

Input contract:

- Call `can_do_mlock()` with no arguments.
- Treat the returned value as a bool scalar only.
- Do not dereference or free any returned value.

Return contract:

- Returned value is exactly `0` or `1`.
- Two short-repeat calls return the same value.

## Live Result

The live proof passed:

| Case | Return value | Result |
| --- | ---: | --- |
| `can_do_mlock-read-1` | `0x1` | pass |
| `can_do_mlock-read-2` | `0x1` | pass |

All live checks passed:

- `all_returns_bool=true`
- `repeat_count=2`
- second read `stable_from_first=true`
- `raw_runtime_values_redacted=true`

## Code Outcome

`can_do_mlock` is now represented in the call-proof machinery as:

- `SAFE-SCALAR`
- no required pointer arguments
- return kind: `bool`
- live-proven function-map entry after the bounded no-argument bool proof

The fake REPL transport now models `can_do_mlock()` by returning a stable synthetic bool, so
host tests exercise the same no-argument current-task state contract as the live proof.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-can-do-mlock-20260701T010937Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `65.0s` |
| candidate flash helper total | `64.629s` |
| candidate explicit health initial attempt | `1.0s` |
| candidate explicit health retry | `1.0s` |
| live call-proof | `6.0s` |
| post-proof candidate health | `0.0s` |
| rollback flash start to helper done | `64.0s` |
| rollback flash helper total | `63.562s` |
| final explicit health initial attempt | `30.0s` |
| final bridge restart | `3.0s` |
| final explicit health retry | `1.0s` |
| candidate start to final health retry done | `268.0s` |

The first preflight attempt used `a90ctl` from `PATH`, which was not present; no flash had occurred.
The retry used the repo-local `a90ctl.py` and passed. Candidate explicit health initially hit a
serial END-marker truncation; a safe observation retry passed. Final explicit health after rollback
also hit serial truncation; bridge restart plus settle and retry passed cleanly.

## Validation

Device validation:

- Preflight retry confirmed candidate, v2321, v2237, and v48 image SHA values.
- Bridge status passed before flash.
- Baseline v2321 `version`, `selftest`, and `status` passed.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- Candidate helper health passed.
- Explicit candidate health passed after one safe observation retry for a truncated `version`
  response.
- Live proof passed and wrote evidence JSON.
- Post-proof candidate `selftest` and `status` passed with `selftest fail=0`.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final explicit `version`, `selftest`, and `status` passed after bridge restart and retry with
  `selftest pass=11 warn=1 fail=0`.

Host validation:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Focused tests for the `can_do_mlock` classifier/source/fake-proof path: `Ran 4 tests`, `OK`.
- Classifier CLI for `can_do_mlock`: `SAFE-SCALAR=1`, `ok=true`.
- Full `tests.test_a90_repl`: `Ran 177 tests`, `OK`.
- `git diff --check`.

## End State

Final resident is v2321 (`v2321-usb-clean-identity-rodata`) with `selftest fail=0`.

`can_do_mlock` is promoted as a live-proven current-task mlock allowance bool getter.
