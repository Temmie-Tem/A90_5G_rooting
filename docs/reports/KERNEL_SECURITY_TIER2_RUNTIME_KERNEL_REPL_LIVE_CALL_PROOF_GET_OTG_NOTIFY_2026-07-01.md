# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: get_otg_notify

Date: 2026-07-01

- Decision: `a90-repl-live-call-proof-get_otg_notify-pass`
- Scope: one-target live-call proof; boot partition only; rollback to `v2321`
- Target: `get_otg_notify(void)`
- Public artifact: this report and `GOAL.md`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-get-otg-notify-20260701T062153Z/proof/a90_repl_evidence.json`
- Private timeline: `workspace/private/runs/kernel/live-call-proof-get-otg-notify-20260701T062153Z/timeline.json`

## Target Selection

`get_otg_notify` was selected as a new read-only USB/OTG state-observation
target outside the already-covered `CALL_PROOF_TARGETS` inventory. It extends
the function map with a no-argument borrowed-pointer getter for the native
kernel's USB notify core state.

The proof was one-target only.

## Static Gate

- Address: `get_otg_notify=0xffffff800901d8d4`.
- Resolution: `export-recovery`, map agreement, one export candidate.
- Direct BL xrefs: `41`.
- JOPP entry: yes.
- Leaf body: yes.
- Source declaration: `extern struct otg_notify * get_otg_notify(void)` at
  `include/linux/usb_notify.h:175`.
- Implementation source: `drivers/usb/notify/usb_notify.c`.
- ABI/source contract: no arguments; no pointer arguments.
- C1 tier: `SAFE-SCALAR`.
- Required valid pointer args: none.
- Next-symbol boundary: `inc_hw_param` at `+0x20`.
- Static words: global core load, NULL branch, `o_notify` load, return, NULL
  return, return, and final `0x00be7bad` boundary guard were pinned.

The implementation check matched the expected read-only pattern:
NULL if `u_notify_core` is absent, NULL if `u_notify_core->o_notify` is absent,
otherwise return the borrowed `o_notify` pointer.

## Live Run

Flash gate:

- Rollback image `v2321`, deeper fallback `v2237`, final fallback `v48`, and
  TWRP recovery artifacts were present with expected SHA256 values.
- Baseline v2321 `version/status/selftest` passed before candidate flash.
- Candidate image
  `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
  matched SHA256
  `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Candidate flash used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the candidate SHA.
- Candidate helper verification passed, and explicit candidate `selftest`
  returned `pass=11 warn=1 fail=0`.

Live proof:

- Initial proof attempt called the target but stopped because the host-side
  proof predicate was too narrow: it accepted only lowmem borrowed pointers,
  while the function returned a stable canonical kernel data pointer. Candidate
  health remained clean after this host-contract failure.
- The predicate was corrected to accept a stable canonical kernel pointer or
  NULL for this borrowed-pointer contract.
- The retry called `get_otg_notify()` twice with no arguments.
- Both calls returned a stable non-NULL borrowed kernel pointer.
- The returned pointer was not dereferenced and was not freed.
- Raw runtime pointer values and the KASLR slide are private-only and not
  committed.

Health and rollback:

- Post-proof candidate `selftest` passed with `pass=11 warn=1 fail=0`.
- Rollback to `v2321` used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Rollback helper verification passed.
- Final standalone selftest initially had partial serial capture, then `hide`
  hit known marker-loss noise and `double` input mode proved unsuitable for the
  current bridge state. A host-side bridge restart restored clean framing.
- Final standalone `selftest` retry passed with `pass=11 warn=1 fail=0`.

## Timing

Timing was recorded in:

- `workspace/private/runs/kernel/live-call-proof-get-otg-notify-20260701T062153Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper total | `63.720s` |
| candidate explicit selftest | `0.299s` |
| initial live proof host-contract failure | `4.820s` |
| post-failure candidate selftest | `0.297s` |
| live proof retry pass | `5.216s` |
| post-proof candidate selftest | `0.299s` |
| rollback flash helper total | `63.816s` |
| final selftest partial capture | `0.309s` |
| final hide marker-loss attempt | `20.108s` |
| double input mode failed command encoding | `29.921s` |
| bridge restart | `1.996s` |
| final selftest retry | `0.309s` |

The helper total rows are retained for compatibility with prior reports and
are not additive. All serial bridge commands in this unit were run
sequentially.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --no-objdump get_otg_notify`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_a90_repl.ConstantTests.test_kernel_canonical_pointer_gate tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_get_otg_notify_passes_with_borrowed_pointer_contract`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_a90_repl.CallSafetyClassificationTests tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_get_otg_notify_passes_with_borrowed_pointer_contract`

Live validation:

- Candidate flash passed with matching candidate readback SHA.
- `get_otg_notify` live proof passed under the no-argument USB OTG notify
  borrowed-pointer contract.
- Post-proof health passed.
- Rollback to v2321 passed with matching rollback readback SHA.
- Final v2321 selftest retry passed with `selftest fail=0`.

## Function Map Entry

`get_otg_notify` is live-proven only under this contract:

- input: no arguments; USB notify core/global state is read-only.
- return: `struct otg_notify *` is borrowed; it may be NULL or a stable
  canonical kernel pointer.
- observed: two calls returned a stable non-NULL borrowed pointer.
- cleanup: none; the pointer is not owned by the proof and must not be freed.
- policy: one-target proof only; not a mass auto-call target.
