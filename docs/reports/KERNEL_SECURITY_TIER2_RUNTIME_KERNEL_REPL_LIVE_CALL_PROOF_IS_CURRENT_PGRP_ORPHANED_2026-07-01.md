# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: is_current_pgrp_orphaned

Date: 2026-07-01

## Scope

- Target proved: `is_current_pgrp_orphaned`.
- Result: live proof passed; target promoted under a no-argument current process-group
  orphan-status bool contract.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-is-current-pgrp-orphaned-20260701T012647Z/`.

This target extends the REPL's read-only current-task and process-group state observation surface.
It is not promoted as a general call primitive; it is trusted only under the exact no-argument
bool proof contract below.

## Candidate Selection

Host triage used a small adjacent-candidate batch rather than a single isolated guess. The batch
included current-task and time/state observation candidates around the already proven
`can_do_mlock` surface:

- `current_kernel_time64` was parked because the current v1-repl op3 return capture records x0
  only, while this struct-return shape needs the x0/x1 return lanes to make a complete proof.
- `get_debug_reset_header` stayed excluded for this unit because its body allocates, reads, prints,
  and frees rather than behaving as a narrow read-only scalar observation.
- `is_current_pgrp_orphaned` was selected because it takes no arguments, returns a bool-like int,
  and observes current process-group state through its internal tasklist read-lock traversal.

## Static Candidate

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `is_current_pgrp_orphaned` | `0xffffff80080b72bc` | `SAFE-SCALAR`; no pointer args; non-leaf read-lock traversal | `extern int is_current_pgrp_orphaned(void)` |

Static gates:

- Resolution method: `disasm-signature+xref+map`, verified.
- Direct BL xrefs: `2`.
- Source declaration: `include/linux/tty.h:506`.
- Next-symbol boundary: `mm_update_next_owner` at `+0xd8`.
- The proof pins all 54 identity words, including the JOPP entry, `_raw_read_lock`,
  `_raw_read_unlock`, final `ret`, and next-entry sentinel.
- C1 allowlist requires no valid pointer arguments.

Input contract:

- Call `is_current_pgrp_orphaned()` with no arguments.
- Treat the returned value as a bool-like scalar only.
- Do not dereference or free any returned value.

Return contract:

- Returned value is exactly `0` or `1`.
- Two short-repeat calls return the same value.

## Live Result

The live proof passed:

| Case | Return value | Result |
| --- | ---: | --- |
| `is_current_pgrp_orphaned-read-1` | `0x1` | pass |
| `is_current_pgrp_orphaned-read-2` | `0x1` | pass |

All live checks passed:

- `all_returns_bool=true`
- `repeat_count=2`
- second read `stable_from_first=true`
- `raw_runtime_values_redacted=true`

## Code Outcome

`is_current_pgrp_orphaned` is now represented in the call-proof machinery as:

- `SAFE-SCALAR`
- no required pointer arguments
- return kind: `int-bool`
- live-proven function-map entry after the bounded no-argument bool proof

The fake REPL transport now models `is_current_pgrp_orphaned()` by returning a stable synthetic
bool, so host tests exercise the same no-argument process-group state contract as the live proof.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-is-current-pgrp-orphaned-20260701T012647Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `64.0s` |
| candidate flash helper total | `64.628s` |
| candidate explicit health initial attempt | `34.0s` |
| candidate explicit health retry | `1.0s` |
| live call-proof | `5.0s` |
| post-proof candidate health | `0.0s` |
| rollback flash start to helper done | `63.0s` |
| rollback flash helper total | `63.568s` |
| final explicit health | `1.0s` |
| candidate start to final health done | `302.0s` |

Candidate explicit health initially exited cleanly but the capture contained serial noise/truncation,
so a safe observation retry was recorded and passed. Final explicit health after rollback passed
without a bridge restart or retry.

## Validation

Device validation:

- Preflight confirmed candidate, v2321, v2237, and v48 image SHA values.
- Bridge status passed before flash.
- Baseline v2321 `version`, `status`, and `selftest` passed.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- Candidate helper health passed.
- Explicit candidate health passed after one safe observation retry for serial capture noise.
- Live proof passed and wrote evidence JSON.
- Post-proof candidate health passed with `selftest fail=0`.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final explicit `version`, `status`, and `selftest` passed with `selftest pass=11 warn=1 fail=0`.

Host validation:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Focused tests for the classifier/source/fake-proof path: `Ran 4 tests`, `OK`.
- Classifier CLI for `is_current_pgrp_orphaned`: `SAFE-SCALAR=1`, `ok=true`.
- Full `tests.test_a90_repl`: `Ran 178 tests`, `OK`.
- `git diff --check`.

## End State

Final resident is v2321 (`v2321-usb-clean-identity-rodata`) with `selftest fail=0`.

`is_current_pgrp_orphaned` is promoted as a live-proven current process-group orphan-status
bool getter.
