# V2551 — ACDB topology replay live handoff

Date: 2026-06-16

## Scope

Implement and run the exact-gated native ACDB topology replay handoff that V2550 only planned.

The runner:

- boots the V2334 audio materialization image through the checked flash helper;
- verifies serial `version`/`status`/`selftest fail=0`;
- brings up ADSP and materializes `/dev/snd` nodes;
- stages the private V2549 ACDB replay helper and the private V2547 topology payload;
- applies the V2407 App Type gate and the V2377 speaker route;
- starts topology replay and waits for `AUDIO_SET_CALIBRATION ok`;
- runs the bounded PCM probe only if replay SET succeeds;
- resets the route and rolls back to V2321.

No raw ACDB payloads or generated binaries are committed.

## Implementation

Public changes:

- `workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2550.py`
  - rewrites inherited V2379 runtime paths to the V2550 runtime directory;
  - removes shell `$SECONDS` dependency from the replay wait loop.
- `workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2551.py`
  - adds the exact-gated live runner for the V2550 plan;
  - adds content-retry selftest verification to avoid treating serial truncation as a health failure;
  - always rolls back to V2321 after the candidate run.
- `tests/test_native_audio_acdb_topology_replay_live_handoff_v2550.py`
  - locks the V2550 runtime-path rewrite and no-`SECONDS` contract.
- `tests/test_native_audio_acdb_topology_replay_live_handoff_v2551.py`
  - covers dry-run readiness, exact gate, cleanup contract, and the selftest retry helper.

## Live attempts

All attempts used the exact approval phrase:

```text
AUD-5N-native-acdb-topology-replay go: one-shot V2550 topology replay wrapper with pinned V2547 payload, V2407 app-type, V2377 route, bounded PCM probe, explicit deallocate, rollback to V2321
```

### Attempt 1

- Run directory: `workspace/private/runs/audio/v2551-acdb-topology-replay-20260616-084058`
- Decision: `v2551-acdb-topology-replay-live-blocked`
- Blocker: replay shell used `$SECONDS`, which the device shell did not define.
- Rollback: V2321 restored; final selftest `fail=0`.

### Attempt 2

- Run directory: `workspace/private/runs/audio/v2551-acdb-topology-replay-20260616-084939`
- Decision: `v2551-acdb-topology-replay-live-blocked`
- Blocker: candidate selftest command returned a valid transport end marker, but the captured stdout was truncated before `fail=0`.
- Rollback: V2321 restored; final selftest `fail=0`.

### Attempt 3

- Run directory: `workspace/private/runs/audio/v2551-acdb-topology-replay-20260616-085346`
- Decision: `v2551-acdb-topology-replay-live-blocked`
- Candidate boot and audio setup:
  - V2334 booted and passed selftest;
  - ADSP/card materialized;
  - 61 `/dev/snd` nodes were created;
  - V2549 helper, V2547 payload, `tinymix`, PCM probe, and the low-amplitude WAV staged successfully;
  - V2407 App Type gate and all 13 V2377 route controls applied successfully;
  - route reset completed with no mismatches.
- Functional blocker:

```text
A90_ACDB_REPLAY_HELPER_EXITED_BEFORE_SET
open /dev/ion: No such file or directory
[exit 31]
```

PCM probe was not attempted because ACDB replay did not reach `AUDIO_SET_CALIBRATION ok`.

Rollback:

- V2321 restored through the checked helper;
- rollback version check passed;
- rollback selftest reported `fail=0`.

## Validation

Host validation:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2550.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2551.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_native_audio_acdb_topology_replay_live_handoff_v2550 \
  tests.test_native_audio_acdb_topology_replay_live_handoff_v2551
```

Result:

```text
Ran 11 tests in 0.436s
OK
```

Current post-run health:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

## Decision

V2551 is a valid live handoff and rollback test, but not a speaker or ACDB replay success.

The route/app-type path is now validated in the native replay wrapper. The concrete new blocker is
lower than ACDB payload content: the V2549 replay helper cannot open `/dev/ion` under the V2334
native audio candidate. The next replay-side unit should materialize or otherwise provide the ION
device node before starting the helper, then rerun the same replay wait gate.

The operator handover to arm `acdb_ioctl` only after init is already implemented and validated by
V2540/V2547; V2547 captured the canonical topology payload with SHA-256
`7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89`.
