# NATIVE_INIT V2644 — ACDB SET-cal replay helper payload-policy blocked

Date: 2026-06-18

## Scope

Final bounded V2639 live rerun after the V2641/V2642/V2643 transport fixes:

- long replay scripts staged as files, not inlined through serial
- scripts installed under allowed roots
- V2636 ACDB replay artifacts allowed under the dedicated `/cache/a90-acdb-setcal-replay-*` prefix
- checked rollback to V2321 after the attempt

## Result

- decision: `v2639-acdb-setcal-replay-live-blocked`
- classification: `helper-payload-policy-blocked-before-final-set`
- private_run_dir: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-102657`
- rollback: `rolled_back=True`
- rollback_version_ok: `True`
- rollback_selftest_fail0: `True`
- post-run host health check: V2321 `0.9.285`, `selftest fail=0`

## What Actually Ran

This run passed the previous setup/transport blockers:

- all staged ACDB replay files passed SHA-256 checks on device
- the start script executed from `/cache/a90-runtime/bin/v2639-setcal-replay-scripts/`
- the V2635 helper started and printed `A90_ACDB_SETCAL_REPLAY_START entries=9`
- runtime cleanup completed
- route reset verification reported no mismatches

## Blocking Evidence

The helper exited before the final SET marker:

```text
A90_SETCAL_REPLAY_HELPER_EXITED_BEFORE_ALL_SET
A90_ACDB_SETCAL_REPLAY_START entries=9
msync dmabuf: Invalid argument
msync dmabuf: Invalid argument
msync dmabuf: Invalid argument
msync dmabuf: Invalid argument
exact arg requires payload but none supplied cal_type=21 cal_size=28
A90_ACDB_SETCAL_REPLAY_DONE rc=1
[exit 32]
```

No PCM probe was attempted after a successful SET replay, so this run does not
answer the speaker/prepare question. It localizes the next blocker to the replay
helper's payload policy: the captured cal_type 21 SET arg is intentionally
header/no-payload in the V2632/V2633 manifest, but the helper treats `cal_size=28`
as requiring a dma-buf payload.

## Safety / Cleanup

- No forbidden partition writes occurred.
- Runtime cleanup printed `A90_SETCAL_REPLAY_RUNTIME_CLEANUP_DONE`.
- Checked rollback to V2321 completed.
- Post-run bridge health check confirmed V2321 `version/status/selftest`, with
  `selftest fail=0`.

## Next Unit

Host-only first: inspect `a90_acdb_setcal_replay_scaffold_v2635.c` payload
requirements for exact SET args. The likely fix is to preserve the captured
header-only SET records exactly for cal_types 9/12/13/21/23 instead of requiring a
separate dma-buf payload whenever the captured arg header advertises a non-zero
`cal_size`. Do not rerun live until focused tests prove cal_type 21 is accepted as
header-only and deallocation expectations remain correct.

## Validation

- V2639 live rerun completed inside the recoverable envelope.
- `version/status/selftest` was rechecked over the bridge after rollback.
- This report contains no raw ACDB payloads or private binary dumps.
