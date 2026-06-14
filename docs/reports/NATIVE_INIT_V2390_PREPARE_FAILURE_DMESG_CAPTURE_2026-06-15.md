# NATIVE_INIT_V2390_PREPARE_FAILURE_DMESG_CAPTURE_2026-06-15

## Scope

V2390 is a host-only observability patch for the AUD-4 native speaker pilot runner. It does not change route controls, PCM geometry, sample rate, amplitude, ADSP behavior, Magisk use, Android handoff behavior, or flash policy.

The V2389 live run reached the intended diagnostic point and showed:

- ADSP boot accepted and `/dev/snd` materialized.
- All 13 V2377-observed route apply commands returned OK.
- The V2386 PCM probe opened card0/device0 successfully.
- The first write failed at tinyalsa `pcm_prepare()` with `errno=22` and `pcm_error="cannot prepare channel: Invalid argument"`.
- Reset verification and rollback to V2321 completed with `selftest fail=0`.

## Change

`native_audio_speaker_pilot_live_handoff_v2379.py` now captures a read-only kernel log snapshot immediately after a playback-attempt failure and before route reset:

- Step name: `dmesg-after-playback-failure-before-reset`
- Command: `/bin/toybox dmesg`
- Capture condition: only when `result.playback_attempted` is true and a failure is caught.
- Stored under `speaker_pilot.playback_failure_dmesg` with `stdout_path`, `remote_tool_result`, and capture point metadata.

Dry-run now advertises the capture under `runtime_plan.playback_failure_dmesg_capture` so the live artifact contract is visible before execution.

## Safety

- Read-only only: `dmesg` snapshot.
- No route/control expansion.
- No smart-amp gain/boost changes.
- No Wi-Fi, modem, eSoC, PCIe, PMIC/GPIO/GDSC, partition, or credential action.
- No Magisk/native dependency; Magisk remains Android-side measurement fallback only.
- Existing route reset and V2321 rollback behavior remains unchanged.

## Validation

Commands run:

```bash
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py tests/test_native_audio_speaker_pilot_live_handoff_v2379.py
PYTHONPATH=tests python3 -m unittest tests/test_native_audio_speaker_pilot_live_handoff_v2379.py
python3 -m unittest discover tests -p 'test_native_audio_speaker_pilot_live_handoff_v2379.py'
python3 -m unittest discover tests
python3 workspace/public/src/scripts/revalidation/native_audio_speaker_pilot_live_handoff_v2379.py --dry-run > /tmp/v2390-dry-run.json
git diff --check
```

Results:

- Focused V2379 tests: 10/10 pass.
- Focused discovery: 10/10 pass.
- Full unittest discover: 1069/1069 pass.
- Dry-run: `decision=v2379-native-speaker-pilot-runner-dry-run`, `ok=True`.
- Dry-run advertises `playback_failure_dmesg_capture.step=dmesg-after-playback-failure-before-reset` and `read_only=True`.
- `git diff --check`: pass.

## Next

Run the pre-authorized AUD-4 native speaker pilot again as V2391. If the PCM probe reproduces the `SNDRV_PCM_IOCTL_PREPARE` `EINVAL`, inspect the captured kernel log before changing route controls, period geometry, card/device, sample rate, or amplitude.
