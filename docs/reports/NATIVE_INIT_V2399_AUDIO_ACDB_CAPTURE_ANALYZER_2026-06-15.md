# NATIVE_INIT V2399 — Audio ACDB capture analyzer

## Scope

Host-only implementation unit after V2398. No Android boot, ADB command, Magisk install, native
speaker write, `/dev/snd` open, mixer write, playback, or ACDB ioctl ran in this unit.

Touched public paths:

- `workspace/public/src/scripts/revalidation/analyze_audio_acdb_android_measurement_v2399.py`
- `tests/test_analyze_audio_acdb_android_measurement_v2399.py`

## Decision

V2399 adds the missing post-live parser for the future AUD-5A/V2397 Android/Magisk ACDB capture. The
analyzer consumes a private V2397 run directory and emits a conservative JSON classification:

- `bounded-native-acdb-candidate` — the capture has rollback proof, AudioTrack stimulus markers,
  App Type evidence, ACDB or `/dev/msm_audio_cal` evidence, and AFE/Q6ASM/ADM calibration edges;
- `hal-dependent-or-opaque` — the capture is complete and points at Android HAL/vendor libs but does
  not expose a bounded native sequence;
- `negative-no-calibration` — the capture is complete but lacks App Type/calibration sequence
  markers;
- `capture-incomplete` — required `result.json`, logcat, or baseline/active/post artifacts are
  missing.

The analyzer is intentionally host-only and tolerant of ADB pull layout differences: it searches the
run directory recursively, so both direct `device-artifacts/*` and nested
`device-artifacts/a90-audio-acdb-v2396/*` layouts are accepted.

## Usage

Analyze a specific private run:

```text
python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_android_measurement_v2399.py \
  --run-dir workspace/private/runs/audio/v2397-android-acdb-measurement-<timestamp> \
  --pretty
```

Or analyze the newest V2397 run under `workspace/private/runs/audio`:

```text
python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_android_measurement_v2399.py --pretty
```

If no private V2397 run exists yet, the CLI returns `capture-incomplete` and exits non-zero. That is
expected until the exact-gated AUD-5A live measurement is run.

## Safety boundary

- host-only; no device command;
- no raw logs committed;
- output contains marker counts, selected evidence lines, and artifact paths only;
- no credentials, DHCP, Wi-Fi, or partition writes;
- Magisk remains measurement-only, not a native-init runtime dependency.

## Validation

Commands run:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/analyze_audio_acdb_android_measurement_v2399.py \
  tests/test_analyze_audio_acdb_android_measurement_v2399.py
PYTHONPATH=tests python3 -m unittest tests/test_analyze_audio_acdb_android_measurement_v2399.py
```

Focused unit tests: `5` tests passed. Full test suite: `1084` tests passed.

## Next frontier

The next live-capable unit remains the exact-gated AUD-5A/V2397 Android/Magisk measurement. After it
produces private artifacts and rolls back to V2321, run this V2399 analyzer to decide whether to design
a bounded native ACDB/App Type bootstrap or close/narrow the audio epic as HAL-dependent.
