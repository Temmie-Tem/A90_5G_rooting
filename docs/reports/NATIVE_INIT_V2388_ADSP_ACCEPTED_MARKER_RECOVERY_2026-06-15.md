# NATIVE_INIT_V2388_ADSP_ACCEPTED_MARKER_RECOVERY_2026-06-15

## Scope

Host-only runner fix after V2387. No bridge command, no flash, no ADSP write, no `/dev/snd` command, no mixer write, and no playback retry.

V2387 did not reach the V2386 PCM probe because `candidate-adsp-boot-once` lost the `A90P1 END` marker after printing `audio.adsp_boot_once.retry=forbidden`. Source inspection shows that marker is printed only after the ADSP boot write is accepted, so retrying the one-shot command is the wrong recovery behavior.

## Change

Updated `workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py`:

- Added `classify_adsp_boot_once_step()`.
- Runs `candidate-adsp-boot-once` with `allow_error=True`.
- Classifies output as accepted when all are true:
  - contains `audio.adsp_boot_once.retry=forbidden`;
  - contains no `audio.adsp_boot_once.refused=` marker;
  - contains no `audio.adsp_boot_once.write=open_failed`, `write=failed`, or `write=close_failed` marker.
- Uses `A90P1 END seq=` as the real protocol-end marker so the diagnostic string `A90P1 END marker not found` is not misclassified as a valid END marker.
- Stores the classification in `result["adsp_boot_once"]` before moving to `wait_for_audio_card()`.
- If accepted marker is absent or a failure/refusal marker appears, the runner still blocks.

## Why this is safe

`audio.adsp_boot_once.retry=forbidden` is emitted only after `write_all_checked(fd, "1\n", 2)` and `close(fd)` succeed in `a90_audio.c`. Treating that as accepted does not retry the one-shot write; it simply preserves the successful activation evidence and continues to passive post-ADSP polling.

This fix does not change:

- exact AUD-4 live approval phrase;
- V2334 candidate boot image;
- V2321 rollback behavior;
- route apply commands;
- reset commands;
- PCM file, sample rate, channels, period size, or playback amplitude;
- V2386 probe default playback tool.

## Test coverage

Added tests for:

- the exact V2387 corrupted output tail: accepted marker present, real `A90P1 END seq=` absent, no failure markers → `accepted-protocol-marker-lost`;
- explicit refused marker → rejected.

## Decision

V2388 prepares the next live attempt. It does not itself prove ADSP/card recovery after marker loss because V2387 had already rolled back before this patch existed.

Next frontier:

- V2389 exact-gated live retry with V2388 ADSP accepted-output recovery and V2386 PCM probe.
- Do not change route controls or PCM parameters until the V2386 probe reports either `A90_PCM_PROBE_WRITE_ERROR` with errno/`pcm_get_error()` or `A90_PCM_PROBE_DONE`.

## Validation

Focused validation passed:

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py tests/test_native_audio_speaker_pilot_live_handoff_v2379.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_native_audio_speaker_pilot_live_handoff_v2379 -v` — 10 tests OK
- `python3 workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py --dry-run` — `ok=True`, `playback_tool=pcm-probe`

Additional validation passed:

- `PYTHONPATH=tests python3 -m unittest discover -s tests` — 1069 tests OK
- `git diff --check`
