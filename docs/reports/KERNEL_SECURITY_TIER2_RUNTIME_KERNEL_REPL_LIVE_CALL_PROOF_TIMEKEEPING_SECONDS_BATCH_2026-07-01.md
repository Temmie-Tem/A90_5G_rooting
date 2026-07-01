# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: timekeeping seconds batch

Date: 2026-07-01

## Scope

- Targets proved in one v1-repl boot session: `ktime_get_seconds`, `ktime_get_real_seconds`.
- Result: live batch proof passed; both targets promoted under no-argument read-only
  time64 seconds contracts.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-timekeeping-seconds-batch-20260701T014723Z/`.

This batch follows the 2026-07-01 GOAL steer to prove adjacent same-shape targets in one boot
session instead of spending one flash/rollback cycle per scalar helper.

## Candidate Selection

Host triage compared adjacent timekeeping seconds getters after the prior `ktime_get_ts64`
result-slot proof and `get_seconds` scalar proof:

- `ktime_get_seconds` was selected as a no-argument monotonic timekeeping seconds getter.
- `ktime_get_real_seconds` was selected as the adjacent no-argument realtime wall-clock seconds getter.
- `ktime_get_resolution_ns` stayed parked because the current resolver did not verify it through
  the export/direct-xref gate (`direct_bl_xref_count=0`), despite a scalar-looking body.
- `ktime_get_raw` stayed rejected because the static gate saw a precall x0 dereference.

## Static Candidates

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `ktime_get_seconds` | `0xffffff800815f66c` | `SAFE-SCALAR`; no pointer args; leaf | `extern time64_t ktime_get_seconds(void)` |
| `ktime_get_real_seconds` | `0xffffff800815f694` | `SAFE-SCALAR`; no pointer args; leaf | `extern time64_t ktime_get_real_seconds(void)` |

Static gates:

- `ktime_get_seconds`: `export-recovery`, direct BL xrefs `2`, source
  `include/linux/timekeeping.h:44`, next-symbol boundary `ktime_get_real_seconds` at `+0x28`,
  all 10 identity words pinned through the next-entry sentinel.
- `ktime_get_real_seconds`: `export-recovery`, direct BL xrefs `10`, source
  `include/linux/timekeeping.h:45`, next-symbol boundary `__ktime_get_real_seconds` at `+0x18`,
  all 6 identity words pinned through the next-entry sentinel.
- C1 allowlist requires no valid pointer arguments for either target.

Input contract:

- Call each target with no arguments.
- Treat each return as a scalar `time64_t` seconds value.
- Do not dereference or free any returned value.

Return contract:

- Returned value is a nonnegative `time64_t` scalar.
- Two immediate reads are nondecreasing.
- The short-run forward delta is at most 2 seconds.

## Live Result

The live batch proof passed in one `ReplSession`:

| Target | Case 1 | Case 2 | Max delta | Result |
| --- | ---: | ---: | ---: | --- |
| `ktime_get_seconds` | `0x59` | `0x5a` | `0x1` | pass |
| `ktime_get_real_seconds` | `0x5a521ebc` | `0x5a521ebc` | `0x0` | pass |

All live checks passed:

- `decision=a90-repl-live-call-proof-batch-pass`
- `host_batch_single_repl_session=true`
- `all_returns_nonnegative_time64=true`
- `all_returns_nondecreasing=true`
- `bounded_forward_deltas=true`
- `raw_runtime_values_redacted=true`

## Code Outcome

Both targets are now represented in the call-proof machinery as:

- `SAFE-SCALAR`
- no required pointer arguments
- return kind: `time64-seconds`
- live-proven function-map entries after the bounded same-session batch proof

The fake REPL transport now models both timekeeping seconds getters by returning bounded
nondecreasing synthetic values, so host tests exercise the same no-argument batch contract as the
live proof.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-timekeeping-seconds-batch-20260701T014723Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `63.0s` |
| candidate flash helper total | `63.708s` |
| candidate explicit health initial attempt | `30.0s` |
| candidate bridge restart | `2.0s` |
| candidate explicit health retry | `2.0s` |
| live call-proof batch | `9.0s` |
| post-proof candidate health | `1.0s` |
| rollback flash start to helper done | `65.0s` |
| rollback flash helper total | `64.628s` |
| final explicit health initial attempt | `31.0s` |
| final bridge restart | `2.0s` |
| final explicit health retry | `1.0s` |
| candidate start to final health retry done | `296.0s` |

Candidate explicit health initially hit serial AT noise and failed before a health judgment; bridge
restart plus retry passed cleanly. Final explicit health after rollback exited 0 and showed
`selftest fail=0`, but the version capture contained AT noise, so a bridge restart plus clean retry
was recorded.

## Validation

Device validation:

- Preflight confirmed candidate, v2321, v2237, and v48 image SHA values.
- Bridge status passed before flash.
- Baseline v2321 `version`, `status`, and `selftest` passed.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- Candidate helper health passed.
- Explicit candidate health passed after bridge restart and retry for serial AT noise.
- Live batch proof passed and wrote evidence JSON.
- Post-proof candidate health passed with `selftest fail=0`.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final explicit `version`, `status`, and `selftest` passed cleanly after bridge restart and retry
  with `selftest pass=11 warn=1 fail=0`.

Host validation:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Focused tests for classifier/source/fake batch-proof path: `Ran 4 tests`, `OK`.
- Classifier CLI for both targets: `SAFE-SCALAR=2`, `ok=true`.
- Full `tests.test_a90_repl`: `Ran 179 tests`, `OK`.
- `git diff --check`.

## End State

Final resident is v2321 (`v2321-usb-clean-identity-rodata`) with `selftest fail=0`.

`ktime_get_seconds` and `ktime_get_real_seconds` are promoted as live-proven no-argument
read-only timekeeping seconds getters.
