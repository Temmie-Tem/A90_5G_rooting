# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof Attempt: of_flat_dt_is_compatible

Date: 2026-07-01

## Scope

- Target attempted: `of_flat_dt_is_compatible`.
- Result: live proof failed; target not promoted.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-of-flat-dt-is-compatible-20260630T233514Z/`.

This was a deliberate pivot from saturated scalar/string helpers toward read-only kernel state
observation. The candidate looked statically plausible, but the live call faulted in the REPL run
context before producing an `A90R` return value. The correct outcome is therefore a parked target and
a call-firewall entry, not a function-map promotion.

## Static Candidate

Pre-live selection pinned:

| Target | Link VA | Static shape | Source contract |
| --- | ---: | --- | --- |
| `of_flat_dt_is_compatible` | `0xffffff800a66cc34` | flat-DT node offset plus compatible-string pointer | `extern int of_flat_dt_is_compatible(unsigned long node, const char *name)` |

The attempted input contract was root node offset `0`, an owned NUL-terminated positive compatible
string `qcom,sm8150`, and an owned impossible compatible string. The intended return contract was a
positive score for the root-compatible case and `0` for the impossible string, with canaries preserved
and owned buffers freed.

## Live Result

The live proof did not reach a usable return:

```text
[signal 11]
[err] run rc=139 (101ms)
A90P1 END seq=25 cmd=run rc=139 errno=0 duration_ms=101 flags=0x2 status=error
```

The host wrapper raised `ReplTransientNoiseError` because no `A90R` output was captured, but the
stdout tail shows the load-bearing fact: the target faulted in the native run context. No retry was
performed. Under the flash-gate rules, the unit stopped and rolled back instead of retry-looping a
faulting live target.

## Code Outcome

No `of_flat_dt_is_compatible` function-map entry was promoted. The final public code change fences the
target as known-unsafe for live calls:

- `resolve_verified(..., "of_flat_dt_is_compatible", purpose="call")` now returns
  `blocked-known-unsafe`.
- `call-safety-classify of_flat_dt_is_compatible` reports `DENY`, `auto_call_allowed=false`, and
  `known-unsafe-live-call`.

This keeps the static observation useful for future analysis without allowing the REPL call gate to
hit the same faulting path again.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-of-flat-dt-is-compatible-20260630T233514Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `65.0s` |
| candidate helper done to explicit REPL-ready marker | `13.0s` |
| live session total | `95.0s` |
| live call-proof attempt | `11.0s` |
| rollback flash start to helper done | `65.0s` |
| rollback helper done to final explicit health done | `33.0s` |
| candidate start to final health done | `310.0s` |

## Validation

Device validation:

- Baseline v2321 health passed before the candidate flash.
- Candidate flash used `native_init_flash.py`; candidate SHA/readback matched.
- Candidate helper health passed, and explicit candidate `version`, `selftest`, and `status` passed
  after a standalone retry for serial framing.
- REPL selftest passed before the target call.
- Target proof failed with native run `SIGSEGV`/`rc=139`; no return value was captured.
- Rollback to v2321 used `native_init_flash.py`; rollback SHA/readback matched.
- Final explicit `a90ctl.py version/selftest/status` passed with
  `selftest pass=11 warn=1 fail=0`.

Host validation after fencing:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and
  `tests/test_a90_repl.py`.
- Focused tests: `Ran 3 tests`, `OK`.
- Full `tests.test_a90_repl`: `Ran 172 tests`, `OK`.
- Classifier CLI over `of_flat_dt_is_compatible`: `DENY=1`, `blocked-known-unsafe`.
- `git diff --check`.

## End State

Final resident is v2321 (`v2321-usb-clean-identity-rodata`) with `selftest fail=0`.

No function-map entry is promoted from this attempt.
