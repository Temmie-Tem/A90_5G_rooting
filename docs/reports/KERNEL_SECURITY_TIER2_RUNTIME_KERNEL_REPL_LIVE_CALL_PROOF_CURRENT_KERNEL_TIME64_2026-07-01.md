# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: current_kernel_time64

Date: 2026-07-01

## Summary

- Target proved: `current_kernel_time64`.
- Contract: no arguments; REPL captures only the x0 return register, which is
  the `tv_sec` field of returned `struct timespec64` on arm64.
- Anchor: same-session `ktime_get_real_seconds()` calls before and after the
  target calls.
- Result: live PASS. Two target calls returned x0 values inside the anchor
  range, nonnegative and nondecreasing.
- Device state: v1-repl candidate flashed, proof ran, post-proof selftest
  stayed `fail=0`, rollback to v2321 completed, final v2321 health passed.

## Candidate Selection

The operator steer now prefers pivoting away from saturated one-shape scalar
helpers toward state/identity functions that extend the REPL as a measurement
instrument. `current_kernel_time64` was selected from the timekeeping
neighborhood because it adds a new return shape: an aggregate `timespec64`
returned in registers. The current v1-repl call path records x0 only, so this
unit proves only the x0 `tv_sec` part, not x1 `tv_nsec`.

Nearby rejected/parked candidates:

- `task_nice`, `task_cpu`, `pid_alive`, and related task helpers were not
  callable map symbols in the current verified map.
- `sysfs-show` sweep produced no auto-callable candidate; show handlers mostly
  require unowned object pointers or lacked source identity.
- Already promoted timekeeping scalar anchors (`ktime_get_seconds`,
  `ktime_get_real_seconds`) were kept as anchors, not new target outcomes.

## Static Gate

| Symbol | Link address | Gate | Source |
| --- | ---: | --- | --- |
| `current_kernel_time64` | `0xffffff8008161894` | `SAFE-SCALAR`; export-recovery; JOPP entry; leaf; direct BL xrefs `26`; no arg deref | `struct timespec64 current_kernel_time64(void)` at `include/linux/timekeeping.h:27` |
| `ktime_get_real_seconds` | `0xffffff800815f694` | existing `SAFE-SCALAR` anchor; export-recovery; JOPP entry; leaf | `extern time64_t ktime_get_real_seconds(void)` at `include/linux/timekeeping.h:45` |

Pinned body checks for `current_kernel_time64`:

- Next symbol: `get_monotonic_coarse64` at `+0x50`.
- Full 20-word body matched the expected static disassembly.
- The body loads x0 from the same timekeeping seconds slot used by
  `ktime_get_real_seconds`, then computes x1 nanoseconds via shift.
- No pointer arguments are accepted or dereferenced.

## Input And Return Contract

Input contract:

- No arguments.
- Kernel timekeeping xtime state is read-only.
- Returned x0 is interpreted only as `struct timespec64.tv_sec`.
- x1 is not captured by the current REPL ABI and is not promoted by this unit.

Return contract:

- x0 `tv_sec` is nonnegative.
- Repeated target calls are nondecreasing.
- Repeated target calls advance by at most 2 seconds in the short proof window.
- Every target x0 value lies between same-session
  `ktime_get_real_seconds()` anchor calls.

## Live Result

Live run:

- Candidate image: `boot_linux_tier2_repl_v1_repl.img`
  (`b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`).
- Rollback image: `boot_linux_v2321_usb_clean_identity_rodata.img`
  (`ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`).
- Fallback images and TWRP recovery were present before flash.
- Baseline v2321 `version/status/selftest` passed before flash.
- Candidate helper health passed; explicit candidate health passed after one
  serial END-marker retry.

Observed public values:

- `ktime_get_real_seconds()` before: `0x5a523ab0`.
- `current_kernel_time64()` x0 call 1: `0x5a523ab1`.
- `current_kernel_time64()` x0 call 2: `0x5a523ab2`.
- `ktime_get_real_seconds()` after: `0x5a523ab2`.
- Target delta: `0x1`.
- Anchor delta: `0x2`.

Decision:

- `a90-repl-live-call-proof-current_kernel_time64-pass`.
- Function-map status: live-proven only under the no-argument
  `timespec64.tv_sec` x0 contract.
- Raw runtime pointers and KASLR slide stayed private.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-current-kernel-time64-20260701T034714Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper total | `63.640s` |
| candidate flash start to helper done | `64s` |
| candidate explicit health retry total | `30s` |
| live call-proof | `7s` |
| post-proof candidate health | `1s` |
| rollback flash helper total | `63.555s` |
| rollback flash start to helper done | `63s` |
| final health retry total | `51s` |
| candidate start to final health done | `244s` |

Notes:

- Candidate explicit `version` first attempt lost the A90P1 END marker; slow
  retry `version/status/selftest` passed.
- Final explicit `version` first attempts lost the A90P1 END marker; `hide`
  resync plus slow `version/status/selftest` passed.
- The serial issue did not coincide with target-call failure, oops, or health
  regression.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- Focused tests:
  - `CallSafetyClassificationTests.test_safe_with_valid_pointer_seed_records_required_args`
  - `CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args`
  - `SelftestIntegrationTests.test_call_proof_current_kernel_time64_passes_with_tv_sec_anchor_contract`
- Full suite: `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests.test_a90_repl`
  - `Ran 185 tests ... OK`.
- `git diff --check` passed before live; rerun before commit.

Device validation:

- Candidate flash used only `native_init_flash.py`, with matching readback SHA.
- Live proof returned `ok=true`.
- Post-proof candidate selftest: `pass=11 warn=1 fail=0`.
- Rollback to v2321 used only `native_init_flash.py`, with matching readback SHA.
- Final v2321 `version/status/selftest` passed after serial resync:
  `selftest pass=11 warn=1 fail=0`.
