# S22+ FYG8 R4W1-B Connected-To-Live Runbook

Date: 2026-07-19 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

State: connected policy bound; connected PASS absent; live policy inactive.

This runbook fixes the remaining promotion sequence so the experiment is not
redesigned between the connected qualification and the attended live run. It
does not grant device contact or live authorization. `AGENTS.md` remains the
binding policy.

## Frozen Implementation

- source checkpoint: `c744abb3`;
- connected policy binding: `49f76041`;
- helper SHA256:
  `734693c456d482e6a09360129ba74e9123017b5c42829518a23870d07465a95d`;
- focused test SHA256:
  `87de80150d1962c5804471a8037657144a4c394cd8cba5c596947c0723be42c1`;
- reusable core SHA256:
  `9bcade2532e77d538112836ebe9903bab832c1f2250151d3635260b6fd013725`;
- core test SHA256:
  `b55db8579115ec437e7fe63b6a3b6ecef0d8cbcac54110599e85f310f3b2fd9d`.

Any change to these four source identities invalidates a connected PASS and
requires a new host qualification. Do not edit the helper between connected
PASS and live.

## Stage 1: Connected Read-Only Qualification

Required fresh operator acknowledgement:

`S22PLUS-FYG8-R4W1B-CONNECTED-READ-ONLY-DRY-RUN`

Only after that exact acknowledgement, run from the repository root:

```bash
PYTHONPYCACHEPREFIX=/tmp/android_native_init_lab_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1b_live_gate.py \
  --connected-read-only-dry-run \
  --ack S22PLUS-FYG8-R4W1B-CONNECTED-READ-ONLY-DRY-RUN
```

Expected sole PASS verdict:

`PASS_R4W1B_CONNECTED_BASELINE_READ_ONLY`

Load-bearing state:

`workspace/private/state/s22plus_fyg8_r4w1b_connected_read_only_pass.json`

The run must create no consumed state and report `device_writes=false`,
`reboot=false`, `download_transition=false`, `odin_transfer=false`, and
`flash=false`. A failure does not authorize live promotion or a same-policy
retry.

## Stage 2: Deterministic Live Binding

After connected PASS, do not modify the helper, tests, core, connected result,
or PASS record. Reopen the PASS through `validate_connected_pass()` and record:

- PASS record path and SHA256;
- connected result path and SHA256;
- helper/test/core/core-test identities;
- observer read receipts and the byte-identical double `last_kmsg` proof;
- pstore absence, no-Odin state, and every false write/transition field.

Construct the exact live clause from
`docs/operations/S22PLUS_FYG8_R4W1B_AGENTS_EXCEPTION_DRAFT_2026-07-19.md`.
Bind the exact connected PASS identities into that clause. The clause must add
exactly one standalone live sentinel:

`S22PLUS_FYG8_R4W1B_POLICY_STATE=ACTIVE`

Before committing it, obtain an independent host-only binding review. The
review must prove the connected PASS contract, source and artifact pins,
one-shot consumption point, boot-only transfer envelope, mandatory rollback,
observer semantics, canonical timeline, and absolute prohibitions. A clean
review authorizes only the separate policy commit, not execution.

After the policy commit, rerun:

1. focused core/helper tests;
2. all R4W1-B regression tests;
3. `py_compile`;
4. `git diff --check`;
5. the complete `--offline-check` gate.

Required ready state is connected PASS present, candidate consumed absent,
connected policy active, live policy active, and no device action since the
connected qualification.

## Stage 3: Attended One-Shot Live

Only after Stage 2 is committed and requalified, request the fresh live
acknowledgement:

`S22PLUS-FYG8-R4W1B-DIRECT-PID1-LIVE`

Then run:

```bash
PYTHONPYCACHEPREFIX=/tmp/android_native_init_lab_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1b_live_gate.py \
  --live \
  --ack S22PLUS-FYG8-R4W1B-DIRECT-PID1-LIVE
```

The helper repeats the exact connected baseline before requesting Download.
It creates the consumed state immediately before the single candidate
transfer. Consumption is permanent regardless of transfer outcome.

The operator must attend the raw-park close, physically leave any RDX screen,
and enter normal Samsung Download. Before rollback transfer, enter exactly:

`S22PLUS-FYG8-R4W1B-NORMAL-DOWNLOAD-CONFIRMED`

The helper then performs Magisk-first boot-only rollback. Stock boot is
cleanup-only after a failed Magisk transfer on the same single endpoint and
can never produce PASS.

## Stage 4: Interrupted Recovery

Use this only if a valid consumed state already exists and the device is in
confirmed normal Samsung Download mode. It cannot authorize or repeat the
candidate.

Fresh recovery acknowledgement:

`S22PLUS-FYG8-R4W1B-MAGISK-ROLLBACK-FROM-DOWNLOAD`

Command:

```bash
PYTHONPYCACHEPREFIX=/tmp/android_native_init_lab_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1b_live_gate.py \
  --rollback-from-download \
  --ack S22PLUS-FYG8-R4W1B-MAGISK-ROLLBACK-FROM-DOWNLOAD
```

The same temporal confirmation
`S22PLUS-FYG8-R4W1B-NORMAL-DOWNLOAD-CONFIRMED` is still required before the
rollback transfer.

## Stop Conditions

Stop without improvisation on any source/hash mismatch, missing or existing
unexpected state, observer mismatch, marker contamination, ambiguous or
changed endpoint, non-normal Download screen, transfer failure outside the
pinned stock-cleanup rule, rollback health failure, or noncanonical timeline.
Never broaden the partition envelope or replace an exact acknowledgement with
a generic approval.
