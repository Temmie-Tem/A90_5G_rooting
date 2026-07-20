# Device Action Process v2 F1 Adapter Design

Date: 2026-07-21 KST
Status: host-only implementation and review complete; no F1 run authorized

## Objective

Connect the validated Process v2 core, reusable D0 preflight, measured Samsung
Download endpoint tracking, and regular-path Odin transport without creating a
candidate-specific helper or policy block.

## Commands

- `--validate` and `--render-plan`: H0 only.
- `--prepare`: D0 only. Allocate one private run, collect exact connected
  preflight evidence, bind the execution-critical closure, and print one exact
  approval token. It cannot reboot, enumerate a Download endpoint through Odin,
  invoke Odin transfer, or authorize itself.
- `--execute`: F1. Requires the exact prepared run and exact fresh approval
  token. Reopens all prepared evidence and repeats the connected read-only
  health/identity check before any control action.
- `--recover`: recovery only. Requires an existing approved journal with a
  durable candidate-attempt event. It can continue only the exact prepared
  Magisk rollback and final verification. It cannot request or transfer the
  candidate and requires no second approval.

## Approval Binding

The token binds the target evidence, candidate and rollback AP hashes, manifest
and profile, observation rule and timeout, runner version, D0 result, and exact
execution-critical source closure. Any change requires a new preparation and
fresh approval.

## Live Flow

1. Reopen preparation, source closure, artifacts, D0 raw evidence, and private
   target continuity material.
2. Repeat read-only Android health and target continuity checks.
3. Create the append-only journal and bind the exact approval.
4. Request Download once and require one measured endpoint on the same USB
   topology.
5. Durably bind an exclusive attempt start into the state-bound journal, record
   `candidate_flash_start`, and invoke regular-path Odin with the exact
   candidate boot-only AP.
6. Classify local parse failure separately from any possible device session.
   Any possible session enters the mandatory rollback path.
7. Close bounded candidate observation. Successful transfer must leave the
   original Download endpoint before candidate execution can be considered.
8. Require attended physical Download when no rollback endpoint is already
   present, then transfer the exact Magisk boot-only AP.
9. Require final Android/Magisk health, same target/topology, no Odin endpoint,
   two identical EOF-bounded retained-log reads, one marker-family occurrence,
   and one exact marker.
10. Close only after the canonical eight timeline events and verified rollback.

## Failure And Recovery

- Failure before `candidate_flash_start` may abort without rollback.
- Local Odin parse failure with no device-session marker aborts without claiming
  a transfer.
- Timeout, interruption, unknown Odin output, or any possible device session
  requires rollback even when candidate success is unproved.
- A failed or interrupted rollback leaves the journal recoverable. It does not
  authorize another candidate or a different cleanup image.
- Attempt starts are limited to two and cross-checked against the journal. A
  durable completed rollback result advances recovery without another flash.
- `recover` reconstructs missing no-proof candidate/observation transitions
  and canonical rollback events, then resumes only rollback.
- Candidate success without exact retained-marker proof is `NO_PROOF`, not PASS.
- Stock boot cleanup, second candidate, non-boot payload, and every permanent
  forbidden primitive remain outside this adapter.

## Evidence

One private run contains prepared evidence, private target continuity material,
the append-only journal, measured endpoint receipts, raw Odin stdout/stderr,
two retained-log captures, one structured result, and the canonical eight-event
timeline. Tracked output contains no raw serial, USB topology, or device log.

## Host Gate

Before any F1 use, focused simulations must cover approval mismatch, changed
closure/artifact, wrong target, local parse failure, unknown session, candidate
timeout, interruption and recovery, rollback failure and retry, exact marker
PASS, marker absence, final-health failure, timeline uniqueness, and the rule
that recovery can never invoke candidate transfer. The final execution-critical
closure then requires one independent safety review. A fresh operator approval
is still required afterward.

## Host Result

The implementation passed its focused and related regression suites. An
independent Opus review found no HIGH issue and returned
`GO_HOST_SOURCE_TO_SEPARATE_MANIFEST_READINESS_AND_D0_PREPARE`; a delta review
confirmed its M1/L1/L2 findings closed. The production manifest remains
`draft-host-only`, so `--prepare` stops before device contact or run allocation.
