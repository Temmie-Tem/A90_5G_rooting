# Device Action Process v2 F1 Adapter Host PASS

Date: 2026-07-21 KST

## Verdict

`PASS_DEVICE_ACTION_F1_ADAPTER_V2_HOST_SOURCE`

The reusable Process v2 F1 adapter and its execution-critical closure are
source-ready. The production manifest remains `draft-host-only`; no connected
preparation, Download transition, Odin invocation, partition transfer, or
device write occurred. This verdict is not F1 authority.

## Implementation

- adapter: `workspace/public/src/scripts/revalidation/device_action_f1_live_v2.py`
- adapter SHA256: `a90a01624f6b0a29b6ca8e9f07fd6504e22e4edf7537a92597ccd52f50b0af87`
- H0 core SHA256: `6b6ccaab0e67706a4b624b677e82c0d326945a586585576cebdf5a4c19d917f5`
- D0 adapter SHA256: `1d34718b194d2ff11f8b57e9042944295a1fa88abd59db601fd504868d1a6fa1`
- focused tests: `tests/test_device_action_f1_live_v2.py`
- focused test SHA256: `576584c8b79ccb1bb89341fd4df8b789f2dae08364c1a068c22fa460cd7eb276`
- design SHA256: `2f4b5718ac1a747fc6bcf9ded59b46856afca91483911269b591c0d0d8ff5773`

The adapter has separate H0, D0, F1, and recovery surfaces:

- `--validate` and `--render-plan` perform H0 only;
- `--prepare` requires `ready-for-f1-approval`, performs D0 only, and emits the
  exact approval binding without authorizing itself;
- `--execute` requires that exact binding plus a fresh exact token; and
- `--recover` accepts no approval and can resume only exact rollback after a
  durable candidate attempt is bound into the journal.

The binding covers the validated bundle, live target evidence, private target
continuity, candidate and rollback identities, observation rule, and complete
execution-critical source closure. Execution repeats D0 before creating its
journal. Android-to-Download continuity uses the prepared physical USB
topology plus measured usbfs endpoint generation and repeated sysfs identity.

## Failure And Recovery Semantics

- Only a recognized local Odin parse failure can abort without rollback.
- Every exception or ambiguous outcome that may have opened a device session
  enters mandatory rollback or leaves a recoverable rollback state.
- Recovery never calls the candidate transfer.
- Exclusive attempt starts are bound into state-specific hash-chained
  checkpoints, enforce attempts 1 then 2, and stop on missing or changed
  evidence.
- A durable completed rollback receipt advances the journal without another
  endpoint wait or transfer; missing rollback timeline events are resumed in
  canonical order.
- Candidate, rollback, preflight, raw Odin, and observer evidence is retained
  append-only or atomically replaced only for current derived state.
- Preflight and transfer attempts stop after the same material failure twice.
- Final PASS requires candidate completion, exact delimiter-anchored marker
  cardinality with no foreign or partial family record, exact rollback,
  final Android/Magisk health, raw observer reopening, and all eight canonical
  timeline events.

## Validation

The final focused Process v2 run passed `67/67`. The related transport,
marker, USBFS identity, endpoint-generation, connected-gate, and regular-path
regression run passed `127/127`. `py_compile`, `git diff --check`, real H0
`--validate`, and real H0 `--render-plan` passed. Against the production
manifest, real `--prepare` returned rc=2 with
`manifest is not ready for F1 preparation` before run allocation or device
contact.

Focused simulation covers exact approval, draft/reverted-draft refusal,
changed preparation evidence, wrong target path, endpoint identity, local
parse failure, ambiguous device session, candidate interruption, rollback-only
recovery, rollback retry, final-health retry, marker absence, foreign and
partial markers, raw evidence tamper, durable-attempt tamper, pre-attempt and
post-result interruption, canonical timeline recovery, and both fails-twice
bounds.

## Independent Review

The initial Claude Opus 4.8 high-effort read-only review found no HIGH issue and
returned `GO_HOST_SOURCE_TO_SEPARATE_MANIFEST_READINESS_AND_D0_PREPARE`. It
identified one MEDIUM missing arming-gate test and two LOW robustness issues:
a pre-journal preflight interruption could strand a run, and the retry bound
was wider than `fails-twice-stop`.

The implementation added explicit draft/reverted-draft and recovery-argument
tests, append-only two-attempt preflight resume, and a common two-attempt
transfer bound. A second Opus delta review confirmed M1, L1, and L2 closed and
returned the same GO verdict. A third Opus call hit its rolling limit before a
verdict and is not authority. Combined three-call Opus metrics were
`$5.857253`, `979.484 s` API time, `982.338 s` wall time, `69,907` output
tokens, `2,199,846` cache-read tokens, and `300,935` cache-creation tokens.
Fast mode was off.

A later self-audit added pre-Odin attempt checkpoints. An independent
`gpt-5.6-sol` xhigh review found that deleted starts could reset the attempt
count and that event-before-start interruption lacked valid result evidence.
After remediation, a second xhigh delta review confirmed those findings closed
but found completed-rollback replay and rollback timeline interruption gaps.
The final high-effort narrow delta review found no remaining issue and returned
`GO_HOST_SOURCE_TO_SEPARATE_MANIFEST_READINESS_AND_D0_PREPARE`. These reviews
were read-only and performed no device action.

## Remaining Gate

This closes only the adapter source unit. The next selected unit may review the
data-only manifest readiness change and perform one new connected D0
preparation. Only the exact token emitted by that new preparation can be
presented for a fresh operator approval. Until then there is no F1 run to
approve or execute.
