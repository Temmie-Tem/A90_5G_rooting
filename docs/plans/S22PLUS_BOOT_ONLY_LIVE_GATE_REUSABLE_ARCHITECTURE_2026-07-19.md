# S22+ Boot-Only Live-Gate Reusable Architecture

Date: 2026-07-19 KST

Status: source implementation present; host qualification and policy activation
remain separate gates.

Scope: new S22+ boot-only experiments after R4W1-B. This design performs no
device contact and grants no flash authorization.

## Decision

New boot-only experiments use a two-layer architecture:

1. `s22plus_boot_only_live_core.py` owns mechanical safety primitives only;
2. one target-specific helper owns every evidence claim, artifact pin, observer
   meaning, transition, verdict, and policy acknowledgement.

The core is reusable because its behavior does not decide whether a candidate
is correct. The target helper remains independently reviewable because no
declarative manifest or common framework can synthesize a PASS.

This is the live equivalent of the existing builder/checker separation. It
removes repeated implementation while preserving independent evidence.

## Reusable Core Boundary

The core may provide only:

- durable replace-write JSON;
- race-free `O_EXCL` durable state creation;
- the canonical ordered `events:[{name,timestamp_utc}]` timeline;
- private run-directory allocation;
- direct regular-file stable reads and hashes;
- bounded `adb exec-out` streaming through real process EOF with separate empty
  stderr, return-code, timeout, and live size checks; and
- delimiter-anchored marker-family parsing with exact, repeated exact, foreign,
  malformed, unterminated, and observer-boundary-partial outcomes.

The core contains no model, firmware, candidate, partition, path, expected
hash, policy marker, acknowledgement, PASS verdict, USB transition, or flash
command.

## Target Helper Boundary

Each target-specific helper must carry inline:

- exact target and firmware identity;
- candidate raw/LZ4/AP/manifest/static-result pins;
- builder/checker/source pins required by that evidence chain;
- exact Magisk rollback, stock cleanup, Odin, and full-stock evidence;
- baseline and final partition identities;
- marker bytes, family namespace, observer paths, and verdict table;
- candidate observation meaning and numeric bounds;
- Download/RDX operator protocol;
- connected and live policy sentinels and fresh acknowledgement tokens; and
- one-shot consumed-state schema.

Generated manifests and stored PASS records are receipts. They never replace
inline pins or a fresh checker run.

## Standard Four-Mode Lifecycle

Every new helper exposes exactly four modes:

1. `--offline-check`: no device contact; reopen all pins and rerun the
   independent checker.
2. `--connected-read-only-dry-run`: separately policy-bound; exact Android,
   partition, observer, marker-cleanliness, and no-Odin preflight only. It must
   rehearse every read-only load-bearing observer operation, including repeated
   reads and byte-identity checks.
3. `--live`: separately policy-bound and one-shot; consume immediately before
   candidate transfer, perform the bounded experiment, and mandatorily roll
   back.
4. `--rollback-from-download`: valid only after consumption; verify only the
   minimal rollback artifacts and endpoint, never rerun expensive candidate or
   full-firmware gates before emergency recovery. This recovery mode does not
   depend on the live ACTIVE sentinel or current-helper hash after consumption;
   those gates authorize the candidate, not restoration of the pinned baseline.

The connected PASS is bound to the exact helper, focused test, core, core test,
result path, and result hash. Any source change invalidates it.

## R4W1-B Specialization

R4W1-B is the first consumer. It adds:

- exact three-reproduction candidate and fresh static checker replay;
- exact rooted FYG8 Android with Magisk boot, stock `vendor_boot`, DTBO, and
  recovery;
- live `sec_log_buf`, exact platform bind, both proc observers read to EOF, and
  R4W1-B family absence before consumption; connected rehearsal reads
  `/proc/last_kmsg` twice and requires byte identity;
- one candidate boot-only transfer and at most 90 seconds of raw-park
  observation;
- no host RDX command;
- a temporal operator confirmation after physically reaching normal Samsung
  Download mode and before rollback transfer;
- exact Magisk-first rollback, with stock boot only after a failed Magisk
  transfer on the same unambiguous endpoint; and
- two byte-identical EOF-complete reads of the first rollback boot's
  `/proc/last_kmsg` as the sole load-bearing live observer.

## Ring-Identity Finding

The qualified R4W1-B Image intentionally reproduces the FYG8 Linux banner:

`5.10.226-android12-9-30958166-abS906NKSS7FYG8`

That banner is also present in the stock/Magisk kernel and is therefore not a
candidate-specific ring identity. Requiring it would create false confidence.

The safe interpretation is:

- before the first candidate run, both baseline observers must contain no
  R4W1-B family prefix or boundary partial;
- the one-shot state prevents a second candidate attempt;
- an exact R4W1-B marker after a successful candidate transfer is a positive
  ring identity and proves the narrow exec-acceptance claim;
- marker absence cannot distinguish exec rejection, retained-ring loss, or an
  intervening kernel boot and remains only `NO_PROOF`.

This closes stale-positive risk without pretending to close the already
documented retention-leg ambiguity.

## Standard Safety Rules

- Candidate and rollback APs contain exactly one `boot.img.lz4` member.
- Only boot is in the transfer envelope.
- One unambiguous endpoint is required before every transfer.
- RDX is never a transfer target; normal Download requires a temporal operator
  confirmation.
- Consumed state is created with a durable exclusive link before candidate
  transfer and is never removed to retry.
- All outcomes have the same eight-event timeline; no-action phases are
  explained in the result, not removed from the schema.
- Stock cleanup is recovery-only and never PASS.
- Exact Magisk rollback health is required for every experimental PASS.
- Emergency rollback never waits for full-firmware hashing or candidate static
  qualification, never requires the retired live sentinel, and accepts the
  recorded consumed helper SHA as provenance rather than requiring it to equal
  later source.

## When A New Design Is Required

A new architecture review is required only when one of these changes:

- target device or firmware lineage;
- writable partition envelope;
- boot-image/container format;
- candidate construction trust boundary;
- observer source or retention semantics;
- RDX/Download/rollback transition;
- live evidence claim or verdict meaning; or
- need for a device write other than the exact boot-only transfer.

A new marker ID, kernel patch, `/init` binary, or candidate hash within the same
boundaries requires new target pins, tests, and policy review, but not a fresh
live-harness architecture.

## Current Verdict

`PASS_REUSABLE_LIVE_GATE_ARCHITECTURE_SOURCE_PRESENT; HOST_QUALIFICATION_NEXT; NO_DEVICE_AUTHORIZATION`
