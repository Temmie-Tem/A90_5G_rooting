# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: total_swapcache_pages

Date: 2026-07-01

## Scope

- Target proved: `total_swapcache_pages`.
- Result: live proof passed; target promoted under a no-argument swapcache page-count
  read-only contract.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-total-swapcache-pages-20260701T020827Z/`.

This target extends the REPL read-only memory-state map with swapcache accounting. It is not
promoted as a general call primitive; it is trusted only under the exact no-argument scalar proof
contract below.

## Candidate Selection

`total_swapcache_pages` was selected as a memory-state observation target rather than another
time/lib helper. `show`-style sysfs targets stayed parked because the current C1 identity oracle
does not yet prove table-bound show callbacks with direct-call confidence. The selected target has
source-backed no-argument ABI, nine direct BL xrefs, no pre-call argument pointer dereferences, and
only the function's internal RCU read-side lock/unlock calls in the scanned body.

## Static Candidate

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `total_swapcache_pages` | `0xffffff8008260bd4` | `SAFE-SCALAR`; no pointer args; RCU read section | `extern unsigned long total_swapcache_pages(void)` |

Static gates:

- Resolution method: `disasm-signature+xref+map`, verified.
- Direct BL xrefs: `9`.
- Source declaration: `include/linux/swap.h:413`.
- Next-symbol boundary: `show_swap_cache_info` at `+0x88`.
- The proof pins all 35 identity words, including the JOPP entry, `__rcu_read_lock`,
  `__rcu_read_unlock`, final `ret`, next-entry sentinel, and next-entry first word.
- C1 allowlist requires no valid pointer arguments.

Input contract:

- Call `total_swapcache_pages()` with no arguments.
- Treat the returned value as a scalar page count only.
- Do not dereference or free any returned value.

Return contract:

- Returned value is in `0..(1 << 40) - 1` pages. Zero is valid when no swapcache pages are present.
- Two short-repeat calls may drift, but the delta must stay under `1 << 30` pages.

## Live Result

The live proof passed:

| Case | Return value | Delta from first | Result |
| --- | ---: | ---: | --- |
| `total_swapcache_pages-read-1` | `0x0` | n/a | pass |
| `total_swapcache_pages-read-2` | `0x0` | `0x0` | pass |

All live checks passed:

- `all_returns_in_sane_range=true`
- `repeat_count=2`
- `bounded_short_repeat_drift=true`
- `raw_runtime_values_redacted=true`

Post-proof candidate health stayed clean with `selftest pass=11 warn=1 fail=0`. Rollback to v2321
completed with matching readback SHA, and final explicit health passed after a bridge restart/retry
for serial framing noise.

## Code Outcome

`total_swapcache_pages` is now represented in the call-proof machinery as:

- `SAFE-SCALAR`
- no required pointer arguments
- return kind: `unsigned-long-pages`
- live-proven function-map entry after the bounded no-argument swapcache page-count proof

The fake REPL transport now models `total_swapcache_pages()` by returning bounded synthetic page
counts, so host tests exercise the same no-argument contract as the live proof.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-total-swapcache-pages-20260701T020827Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `56.0s` |
| candidate flash helper total | `55.520s` |
| candidate explicit health initial attempt | `11.0s` |
| candidate bridge restart | `4.0s` |
| candidate explicit health retry | `1.0s` |
| live call-proof | `6.0s` |
| post-proof candidate health | `0.0s` |
| rollback flash start to helper done | `65.0s` |
| rollback flash helper total | `64.706s` |
| final explicit health initial attempt | `11.0s` |
| final bridge restart | `4.0s` |
| final explicit health retry | `2.0s` |
| candidate start to final health retry done | `261.0s` |

The candidate and final initial `version` observations both hit serial framing noise while
`status/selftest` passed. In both cases, bridge restart plus retry passed cleanly.

## Validation

Device validation:

- Preflight confirmed candidate, v2321, v2237, v48, and TWRP recovery artifact SHA values.
- Bridge status passed before flash.
- Baseline v2321 `version`, `status`, and `selftest` passed.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- Candidate helper health passed.
- Explicit candidate health passed after bridge restart/retry for a truncated `version` response.
- Live proof passed and wrote evidence JSON.
- Post-proof candidate `selftest` and `status` passed with `selftest fail=0`.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final explicit `version`, `status`, and `selftest` passed after bridge restart/retry with
  `selftest pass=11 warn=1 fail=0`.

Host validation:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Focused tests for the `total_swapcache_pages` classifier/source/fake-proof path: `Ran 4 tests`,
  `OK`.
- Classifier CLI for `total_swapcache_pages`: `SAFE-SCALAR=1`, `ok=true`.
- Full `tests.test_a90_repl`: `Ran 180 tests`, `OK`.

