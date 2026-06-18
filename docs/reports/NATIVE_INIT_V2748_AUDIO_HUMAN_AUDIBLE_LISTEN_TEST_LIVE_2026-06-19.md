# NATIVE_INIT V2748 — Human-Audible Speaker Listen Test Live

Date: 2026-06-19 KST

## Scope

Run the V2639/V2735 native audio path with the V2743/V2745 human-listen variant:

- flash the V2334 audio candidate through the checked helper;
- boot ADSP and materialize `/dev/snd`;
- write global `App Type Config` as `1 69941 48000 16`;
- replay the corrected ACDB SET sequence `[39,20,20,13,9,11,12,15,23,16,21]`;
- play one bounded, moderate-amplitude listen window;
- reverse-deallocate/reset and roll back to V2321.

This unit is still measurement/playback only. It does not change smart-amp gain/boost
settings, does not write forbidden partitions, and commits no raw/private audio artifacts.

## Result

**PASS — first human-confirmed audible native-init speaker output.**

The operator confirmed hearing the marked playback window: `삐 소리 들렸어`.

Evidence:

- run directory: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260619-002937/`
- runner decision: `v2639-acdb-setcal-replay-live-pass-before-rollback`
- listen WAV: 48 kHz S16LE stereo, 8 s, amplitude `0.15`, frames `384000`
- listen WAV SHA-256: `0920dbbdfa022e8e6fcf78f5d5e590d21c7c50e94b33edbc538b4ec94e737726`
- playback markers: `A90_LISTEN_WINDOW_READY`, `A90_LISTEN_WINDOW_BEGIN`, `A90_LISTEN_WINDOW_END rc=0`
- PCM write result: `A90_PCM_PROBE_DONE chunks=94 bytes=1536000 drain_us=85333`
- global app-type write: `App Type Config` values `1 69941 48000 16`, `ok=true`
- SET replay marker: `A90_SETCAL_REPLAY_ALL_SET_OK pid=873 final_index=10`
- cleanup: reverse deallocation and runtime-dir cleanup completed
- rollback: V2321 boot image readback SHA matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- final rollback health: `selftest fail=0`

## Interpretation

This closes the basic-audibility question for the current native-init speaker path:

1. The ADSP/Q6 path can be initialized far enough under native init for real speaker output.
2. The corrected ACDB replay plus `App Type Config` write is sufficient for audible playback.
3. The remaining `q6asm_send_cal`/speaker-protection telemetry issues are not blockers for
   basic audibility, but remain follow-up items for safety/quality characterization.

## Residual Notes

- The playback was intentionally bounded: amplitude `0.15`, duration `8 s`.
- WSA speaker-protection/VI-sense telemetry is still not confirmed active; do not raise
  amplitude beyond the established cap without a separate telemetry/safety unit.
- Some serial observation paths have shown transient parser noise in earlier V274x attempts;
  this V2748 run completed, rolled back, and a direct post-run `selftest verbose` on V2321
  again reported `fail=0`.

## Validation

Commands/evidence used after the live run:

```bash
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90ctl.py version

PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose

rg -n 'A90_LISTEN|A90_PCM|failed|error' \
  workspace/private/runs/audio/v2639-acdb-setcal-replay-20260619-002937/70_listen-window-audible-playback.txt
```

Direct post-run device state:

- `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- `selftest: pass=11 warn=1 fail=0`

## Next

Do not repeat basic-audibility probing. The next audio units should be selected from:

1. lightweight WSA/VI-sense telemetry during the same bounded playback path;
2. route/output-quality characterization at the same conservative amplitude cap;
3. documentation/baseline promotion once safety telemetry expectations are explicit.
