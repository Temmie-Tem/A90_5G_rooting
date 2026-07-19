# S22+ FYG8 R4W1-C Connected-To-Live Final Design

Date: 2026-07-20 KST

Status: `PRECONNECTED_SOURCE_GO_AWAITING_EXACT_CONNECTED_ACK`

This design grants no device contact, candidate execution, transfer, rollback,
or flash. `AGENTS.md` remains the only authorization source.

## Objective

After one R4W1-C connected read-only PASS, reach a state where the only missing
input before live execution is a fresh exact operator acknowledgement. Eliminate
the R4W1-B failure mode where the connected helper changed after connected PASS
and forced requalification.

## Frozen Boundaries

The connected source checkpoint is immutable after connected qualification:

```text
64d317ab s22plus: prepare R4W1C connected qualification
```

The following connected files must not change between connected PASS and live:

```text
workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py
tests/test_s22plus_fyg8_r4w1c_connected_gate.py
workspace/public/src/scripts/revalidation/s22plus_boot_only_live_core.py
workspace/public/src/scripts/revalidation/s22plus_odin_transition_core.py
```

The live path is a separate helper. It imports the connected validator and
reopens its canonical PASS, connected result, raw observers, stderr files,
preflight, timeline, Odin receipts, and transaction-index segments. It cannot
create or replace the connected PASS.

## Promotion Split

### Preconnected source packet

Build and independently review these inert files before connected device
contact:

- R4W1-C live helper and focused tests;
- inactive full live-exception draft;
- live-clause template;
- deterministic live-binding packet generator and tests;
- connected-to-live runbook.

The generator's `--preconnected-check` is host-only. It requires connected
policy ACTIVE, live policy absent, connected PASS absent, candidate state
unconsumed, exact source/template pins, and zero device action.

### Post-connected evidence packet

After connected PASS, source files remain unchanged. The generator reopens the
canonical PASS through the connected helper and fills exactly these six values:

```text
CONNECTED_PASS_CREATED_AT_UTC
CONNECTED_PASS_RECORD_SIZE
CONNECTED_PASS_RECORD_SHA256
CONNECTED_RESULT_PATH
CONNECTED_RESULT_SIZE
CONNECTED_RESULT_SHA256
```

It emits a private packet, rendered policy document, and exact `AGENTS.md`
clause. It cannot edit policy or contact a device. Independent review and a
separate policy commit remain mandatory.

## Live Transaction

One process and thread hold the hardened Odin transaction lease for the entire
live invocation. The live helper uses one private run directory and the exact
forward-only internal phases:

```text
prepared
candidate_transfer_started
candidate_transfer_finished
candidate_observation_closed
rollback_endpoint_observed
rollback_confirmed
rollback_transfer_finished
rollback_android_ready
first_rollback_observer_captured
classified
```

The public timeline remains exactly:

```text
live_session_start
candidate_flash_start
candidate_flash_done
candidate_boot_ready
rollback_flash_start
rollback_flash_done
rollback_boot_ready
live_session_end
```

Every Odin enumeration becomes a sealed snapshot receipt and append-only index
record. Endpoint tickets bind USB node path, character-device identity,
generation, snapshot sequence, and receipt identity. A ticket is revalidated
immediately before each transfer.

Endpoint uniqueness is not device attribution. Before Android leaves ADB, the
helper captures exact `adb get-devpath` physical USB topology and requires the
selected ADB serial, `adb get-serialno`, and Android USB sysfs serial to agree.
Every candidate, rollback, and cleanup endpoint must resolve through sysfs to a
Samsung USB character device with both that topology and serial digest. A
unique endpoint on another port or a same-port substitute is rejected.

Pathnames are not transfer identities. Odin and each AP are copied into
write-sealed memfds, hashed from the copied bytes, and AP membership is parsed
again from the sealed descriptor. Only after both inputs are sealed does the
helper revalidate endpoint generation and topology, followed immediately by
the sealed Odin invocation with no intervening durable write.

## Candidate Path

1. Reopen exact connected evidence and all offline artifact pins before device
   contact.
2. Repeat exact rooted FYG8 Android, partition, retained-observer, pstore, and
   clean-empty Odin baseline under the transaction lease.
3. Request normal Download from Android.
4. Wait for exactly one generation-bound Odin endpoint.
5. At `candidate_flash_start`, exclusively create the consumed state before any
   transfer. It binds the transaction run, helper/test, connected evidence,
   candidate AP, rollback APs, and artifact contract.
6. Seal `candidate_transfer_started`, seal Odin and AP bytes, revalidate the
   same endpoint generation and physical topology, and transfer the exact
   one-member candidate AP once.
7. Require Odin disappearance before passive observation. Observe for a bounded
   120 seconds, long enough to cross the prior approximately 30-second reset
   confounder. Absence of an endpoint is not by itself liveness proof.
8. Seal observation closure and proceed to mandatory rollback regardless of
   candidate proof or transfer outcome after consumption.

## Attended Rollback

Endpoint discovery and human confirmation have independent budgets. After one
rollback endpoint is observed, the operator receives a fresh full confirmation
window and must enter the exact temporal token. TTY buffered input is cleared
before prompting; prebuffered non-TTY input is rejected.

After confirmation, `rollback_confirmed` is also the durable Magisk transfer
intent. The helper seals inputs, revalidates the same endpoint generation and
topology, and transfers exact Magisk boot. A stock boot-only cleanup transfer
is permitted only after the sealed Odin process definitely returns nonzero for
Magisk while the same endpoint generation and topology still revalidate;
pre-launch validation failure, timeout, or unknown outcome cannot trigger stock
cleanup. Stock cleanup can never produce PASS.

Exact Magisk Android must return with root, known boot, stock `vendor_boot`,
DTBO and recovery, orange state, and no Odin endpoint. Before classification,
the helper reads `/proc/last_kmsg` twice through EOF under 64 MiB, requires
empty stderr and byte identity, and recomputes the exact R4W1-B marker-family
contract from raw bytes.

## Recovery Resume

`--rollback-from-download` is valid only while the exact live clause remains
ACTIVE and the exact consumed state reopens the policy template/clause,
connected PASS/result, prepared receipt, baseline Android identity and topology,
artifact contract, and original run directory. It never retransfers candidate.

If `rollback_confirmed` exists without `rollback_transfer_finished`, recovery
first waits for exact known Magisk Android. A matching postcondition completes
the phase without retransmission. Otherwise one separately acknowledged
ambiguous Magisk retry is allowed and durably consumed before transfer; no
second ambiguous retry exists.

Recovery attempts are append-only and numbered, with two attempts maximum.
Each gets a distinct timeline and result and never overwrites the live result.
Partial observer files are bypassed with a new attempt name. A complete summary
left before phase publication is reopened and promoted; once the observer phase
exists, its exact raw bytes are always reopened and never recaptured. Existing
phase receipts are semantically reopened before classification.

## Verdict Boundary

- clean exact marker plus exact Magisk rollback:
  `PASS_R4W1C_DIRECT_PID1_EXEC_ACCEPTED_AND_ROLLED_BACK`;
- clean family absence after complete observer:
  `NO_PROOF_R4W1C_EXEC_OR_RETENTION_UNRESOLVED`;
- the 120-second passive window is recorded as behavioral evidence only. Odin
  absence cannot distinguish a live park from power-off or RDX, so it never
  independently proves watchdog ownership or survival;
- missing observer, marker-integrity failure, candidate-transfer failure, or
  rollback failure has a distinct fail-closed verdict;
- no candidate outcome is PASS without exact Magisk rollback and the first
  rollback observer.

Timeline entries are action evidence, not mandatory fillers. Failure records
may contain a strict canonical-order subset and never synthesize skipped action
names or current-time replacements. A completed PASS contains all canonical
eight events exactly once. Live and recovery result files are exclusive and
append-only by attempt.

## Absolute Envelope

Only the boot partition may be transferred through exact one-member Odin APs.
No recovery, vendor_boot, DTBO, vbmeta, BL, CP, CSC, super, userdata, persist,
EFS, sec_efs, RPMB, keymaster, modem, bootloader, or other partition write is
allowed. No raw `dd`, fastboot, Magisk module, panic, SysRq, RDX/S-Boot command,
RAM dump, qdl/Sahara/Firehose, EUD/UART write, format, wildcard cleanup, or A90
action is allowed.

## Ready Definition

The goal is live-ready only when all of the following are current and proven:

1. connected read-only PASS exists and validates against frozen source;
2. post-connected packet exactly binds PASS and result identities;
3. live helper, tests, artifacts, packet, and rendered clause pass independent
   review;
4. complete live clause is committed ACTIVE in `AGENTS.md` separately;
5. focused and regression tests, syntax checks, and full offline artifact gate
   pass after binding;
6. consumed state is absent; and
7. the sole next input is the fresh exact live acknowledgement.
