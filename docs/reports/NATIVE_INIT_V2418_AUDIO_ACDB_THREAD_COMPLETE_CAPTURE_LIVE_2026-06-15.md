# NATIVE_INIT V2418 — ACDB payload capture thread-complete live rerun

## Scope

- Unit: AUD-5D / N3-CAP follow-up after V2417.
- Goal: rerun the Android-good `msm_audio_cal` ioctl payload capture with the V2417
  thread-complete M0 observer.
- Device action: rollbackable Android handoff through the checked helper, transient
  Magisk-root observer only, then rollback to V2321.
- Safety boundary: no native calibration ioctl, no native speaker write, no persistent
  Magisk module, no committed raw payload bytes.

## Live result

- Private evidence:
  `workspace/private/runs/audio/v2418-acdb-thread-complete-capture-20260615-100716/`
- Decision:
  `v2418-acdb-thread-complete-capture-no-msm-audio-cal-ioctl-observed-before-rollback-rollback-pass`
- Result: `ok=true`, `rolled_back=true`.
- Final resident checkpoint verified after the run:
  `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- Post-rollback `selftest verbose`: `fail=0`.

Payload-capture summary:

| Field | Value |
| --- | --- |
| Target processes | audio HAL PID `798`, audioserver PID `922` |
| Target task snapshot | 29 TIDs |
| Helper starts | 29 |
| Helper errors | 0 |
| JSONL files | 29 |
| `ioctl_entry` events | 0 |
| `ioctl_exit` events | 0 |
| Raw payload committed | no |

## Critical observation

The Android-good ACDB edge did occur during the capture window, but not on any
TID present in the pre-playback task snapshot.

Logcat shows the speaker route and ACDB calibration sequence under the audio HAL:

- `audio_hw_primary: select_devices ... output device ... speaker, acdb 15`
- `send_app_type_cfg_for_device PLAYBACK app_type 69941, acdb_dev_id 15, sample_rate 48000`
- `ACDB -> send_audio_cal, acdb_id = 15, path = 0, app id = 0x11135`
- `AUDIO_SET_AUDPROC_CAL cal_type[11] acdb_id[15] app_type[69941]`
- `AUDIO_SET_AFE_CAL cal_type[16] acdb_id[15]`

Those lines were emitted by audio HAL TID `4278`. The V2418 task snapshot for
PID `798` contained only:

- `798`, `812`, `816`, `828`, `829`, `1451`, `1461`, `1464`, `1474`, `1484`,
  `1555`, `1556`

Therefore V2418 did not prove an early payload miss and does not justify an M1
temporary Magisk boot module yet. It proved a narrower M0 coverage gap:

> the ACDB worker thread can be created after the one-time `/proc/<pid>/task/*`
> snapshot.

## Helper behavior note

Most per-TID JSONL files contain only `start` events; only one helper emitted
`stop`. That is compatible with idle traced threads blocking in syscall wait
paths during the fixed capture window, and it is not sufficient to infer that
the real ACDB ioctl path was traced. The decisive evidence is stronger: the
actual ACDB TID `4278` was absent from the enumerated task set.

## Magisk direction

Use the same principle that worked during Wi-Fi investigation:

1. Prefer a transient Android/Magisk-root measurement capsule for observation.
2. Keep native-init runtime independent of Magisk.
3. Escalate to a temporary Magisk boot module only when transient M0 cannot
   observe a confirmed early edge.

For the current audio frontier, M1 remains premature. The next unit should keep
the M0 model but make it dynamic:

- poll `/proc/<pid>/task/*` during the capture window;
- attach to newly-created TIDs such as the observed audio HAL worker `4278`;
- enforce per-helper timeout/stop reporting so idle threads do not leave
  ambiguous `start`-only JSONL files;
- retain private payload-only storage under `workspace/private/`;
- preserve the same no-native-calibration/no-native-speaker-write boundary.

Only if a dynamic-thread M0 run still misses a logcat-proven ACDB edge should an
M1 temporary Magisk boot-module observer be designed. That M1 design would be a
measurement-delivery fallback only, not a final native-init dependency.

## Next unit

V2419 should be host-only support for a dynamic M0 task watcher:

- add bounded task polling to the generated Android capture controller;
- start a helper for each newly observed TID;
- make helper lifetime bounded and auditable;
- test that a post-snapshot synthetic TID is included in the plan;
- then rerun the exact-gated Android handoff in a later V-iteration.

Expected discriminator for the later live run:

- `captured-msm-audio-cal-payload-events` → decode request headers, command
  order, private payload hashes, mem-handle policy, and cleanup behavior.
- `dynamic-m0-missed-logcat-proven-acdb-edge` → design M1 temporary Magisk boot
  module as a separate exact-gated measurement unit.
