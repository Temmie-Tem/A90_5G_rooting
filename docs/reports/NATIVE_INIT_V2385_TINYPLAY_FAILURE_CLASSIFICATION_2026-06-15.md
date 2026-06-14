# NATIVE_INIT_V2385_TINYPLAY_FAILURE_CLASSIFICATION_2026-06-15

## Scope

Host-only follow-up to V2384. No device flash, no mixer write, no playback retry.

Questions:

1. What exactly does the V2384 `Error playing sample` marker prove?
2. Why did `tinyplay` exit with rc 0 despite that failure?
3. What runner evidence was missing from V2384 `result.json`, and how is it fixed before another live run?

## Inputs

- V2384 private run evidence: `workspace/private/runs/audio/v2379-native-speaker-pilot-20260615-051444/`
- Pinned tinyalsa source: `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/`
- Current runner source: `workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py`

## V2384 live symptom

The bounded AUD-4 run reached playback only after all route writes and resets were syntactically successful:

- 13 route apply commands: `rc=0`
- 12 reverse reset commands: `rc=0`
- `tinyplay` host step: `rc=0`, remote `[exit 0]`, but stdout/stderr contained `Error playing sample`
- Rollback: V2321, `rollback_selftest_fail0=True`

The tinyplay step output tail was:

```text
a90_tcpctl v1 ready
OK authenticated
[pid 691]
Error playing sample
Playing sample: 2 ch, 48000 hz, 16 bit 192000 bytes
Draining... Wait 85333 us
[exit 0]
OK
```

The apparent ordering is stdout/stderr interleaving. The source prints `Playing sample...` before entering the write loop, while `Error playing sample` is stderr.

## Source classification

`tinyplay.c` does not propagate playback failure to the process exit code. `main()` calls `play_sample()` and then returns `0` unconditionally after closing the file. Inside `play_sample()`, the write loop prints `Error playing sample` and breaks when `pcm_write()` returns nonzero, but the function still drains/sleeps, closes the PCM, and returns `void`.

Relevant source locations:

- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/tinyplay.c:243` opens PCM device 0.
- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/tinyplay.c:259` prints `Playing sample`.
- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/tinyplay.c:268` calls `pcm_write()`.
- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/tinyplay.c:269` prints `Error playing sample`.
- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/pcm.c:551` maps the first write to `SNDRV_PCM_IOCTL_WRITEI_FRAMES` and records `cannot write initial data` through `oops()` on ioctl failure.
- `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/pcm.c:556` maps later writes to the same ioctl and records `cannot write stream data` on non-`EPIPE` failure.

Therefore V2384 proves:

- PCM open, hw params, sw params, and status mmap got far enough for `tinyplay` to enter the write loop.
- The first or a later `SNDRV_PCM_IOCTL_WRITEI_FRAMES` failed.
- The process rc cannot be used as success/failure for this tinyplay build.

V2384 does **not** yet prove:

- Whether the failing errno was `EINVAL`, `EPIPE`, `ENODEV`, `EIO`, or another driver error.
- Whether the blocker is route incompleteness, PCM device selection, period geometry, ADSP stream state, or smart-amp path readiness.

## Runner fix

`native_audio_speaker_pilot_live_handoff_v2379.py` now preserves partial speaker-pilot evidence when a bounded live step blocks:

- Adds `SpeakerPilotBlocked`, carrying a deep-copied partial result.
- Records `baseline_snapshot`, per-command `remote_tool_result`, `playback.remote_tool_result`, `post_reset_snapshot`, and `blocked_error`.
- Runs reverse reset in `finally` as before.
- In `live_run()`, catches `SpeakerPilotBlocked`, stores `result["speaker_pilot"] = exc.partial_result`, then re-raises so rollback and the top-level blocked decision remain unchanged.

This fixes the V2384 reporting gap: a future blocked live run will keep route-apply, playback, reset, and reset-verification details in `result.json`, not only in per-step JSON files.

## Decision

V2385 is a host-only classification and observability fix. It intentionally does not retry playback and does not change route controls or PCM parameters.

Next safe unit:

- V2386: build/stage a diagnostic tinyplay or minimal PCM write probe that reports `pcm_get_error()` and errno when `pcm_write()` fails, then rerun the same V2377 route once under the existing AUD-4 safety envelope.
- Do not tune route controls, periods, sample rate, or device/card selection until the write errno is known.

## Validation

Host-only validation passed:

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py tests/test_native_audio_speaker_pilot_live_handoff_v2379.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_native_audio_speaker_pilot_live_handoff_v2379` — 8 tests OK
- `python3 workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py --dry-run` — `decision=v2379-native-speaker-pilot-runner-dry-run`, `ok=True`, `route_transport=serial`
- `PYTHONPATH=tests python3 -m unittest discover -s tests` — 1064 tests OK
- `git diff --check`
