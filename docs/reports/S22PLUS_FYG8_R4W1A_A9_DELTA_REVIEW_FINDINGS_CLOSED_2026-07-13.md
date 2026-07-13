# S22+ FYG8 R4W1-A A9 Delta-Review Findings Closed

Date: 2026-07-13 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Scope: host-only source, test, and inactive policy-draft hardening. No device
contact, USB enumeration, ADB, Odin invocation, reboot, Download transition,
repository consumed-state creation, or flash occurred.

## Delta Review

Both independent reviewers reexamined A8 commit `58976f59` and returned
`GO_WITH_MUST_FIX`. They confirmed that all original A7 findings were closed,
then identified three additional boundary defects:

1. a consumed-state creation exception treated any remaining regular state file
   as consumed without validating its v2 contract;
2. the inherited transport raises `SystemExit` for multiple Odin endpoints, so
   both pre-candidate and post-consumption waits could bypass normal fail-closed
   handling and timeline completion; and
3. an absolute requested run directory outside the repository run root could be
   created before later failing `relative_to(root)` after Download entry.

The policy reviewer also corrected the A8 test-total description: the prior
`111/111` total was 103 R4W1-pattern tests plus eight builder tests.

## Closure

The successor helper now:

- reopens and fully validates a v2 consumed state after any exclusive-create
  exception; malformed or unbound state ends with no candidate or rollback
  flash, while only a valid state may proceed to recovery;
- wraps the inherited Odin wait and converts ambiguous-endpoint `SystemExit`
  into `GateError` at both call sites;
- finishes all eight canonical events when the post-consumption manual wait is
  ambiguous; and
- rejects requested run directories outside `workspace/private/runs` before
  allocation and before any connected preflight or Download request.

New tests inject a malformed state after a synthetic fsync failure and prove
that neither candidate nor rollback flash is called, inject the inherited
ambiguous-endpoint `SystemExit`, exercise the post-consumption manual-wait
failure through the full live state machine, verify canonical timeline
completion, and prove an outside run directory is rejected without creation.

## Exact Pins

- successor helper SHA256:
  `9f3055e3c782d058f11bc2482c6cc4270a400e1654fdfdc50be6e681b4e3d7d7`;
- focused test SHA256:
  `402382d88ef853cda70e98614aa6a73ab9ff424cff8d25daf00b4a72962d72b3`;
- inactive policy draft SHA256:
  `a4d72aaa29807e9f056ef64ce04398246801f115a4667b4837acb9cd4335960c`.

All A4, candidate, oracle, rollback, stock, builder, checker, transport, Odin,
and full-stock firmware evidence pins remain unchanged.

## Validation

- focused successor tests: `26/26 PASS`;
- R4W1-pattern tests: `107/107 PASS`;
- candidate-builder tests: `8/8 PASS`;
- combined bounded suite: `115/115 PASS`;
- Python compile and `git diff --check`: PASS;
- offline gate: `PASS_R4W1A_STREAM_CANDIDATE_OFFLINE_CHECK`;
- offline policy state: `DRAFT_INACTIVE`, `active=false`;
- candidate consumed: `false`;
- offline device contact, device write, and flash: all `false`.

Policy remains `DRAFT_INACTIVE`; `AGENTS.md` contains no stream-candidate ACTIVE
sentinel and no live action is authorized.

## Decision

The two delta-review MUST-FIX sets are closed in source and tests. This is still
not an activation verdict. The exact A9 checkpoint must receive one final
read-only delta review before any separate binding-policy commit. Any eventual
device run remains a distinct attended action requiring fresh operator approval.
