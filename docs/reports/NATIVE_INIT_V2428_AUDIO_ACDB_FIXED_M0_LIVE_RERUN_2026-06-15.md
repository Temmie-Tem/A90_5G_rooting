# NATIVE_INIT V2428 — fixed-M0 ACDB capture live rerun

## Scope

- Unit: exact-gated Android/Magisk M0 ACDB payload-capture rerun after V2427 clone-child resume hardening.
- Device action: rollbackable Android handoff, then checked rollback to V2321.
- Native action: none.
- Native speaker write: none.
- Calibration ioctl issued by helper: none.
- Persistent Magisk module: none.

## Live result

Private evidence directory:

- `workspace/private/runs/audio/v2428-acdb-threadset-clone-follow-capture-20260615-121212/`

Safety envelope:

- Pre-live native baseline: V2321 `A90 Linux init 0.9.285`.
- Pre-live rollback/fallback images: V2321, V2237, and V48 present.
- Android flash/handoff: pass.
- Post-handoff ADB/boot/root settle: pass.
- Stage waits before observer/controller/APK push/install: pass.
- Playback Activity launch: pass.
- Artifact pull and cleanup: pass.
- Rollback to V2321: pass.
- Final native `selftest verbose`: `fail=0`.

Observer summary:

- helper starts: `2`
- tracee-add events: `30`
- clone events: `1`
- cloned child resumed: yes (`clone-child-resumed tid=4619`)
- captured `/dev/msm_audio_cal` ioctl entries: `0`
- captured ioctl exits: `0`
- helper errors: `0`
- raw payload bytes in public report: `0`

Private JSONL summaries:

- `msm-audio-cal-threadset-p795.jsonl`: `tracee_adds=14`, `clone_events=1`, `clone-child-resumed=1`, `captured_entries=0`, `timed_out=false`
- `msm-audio-cal-threadset-p913.jsonl`: `tracee_adds=16`, `clone_events=0`, `captured_entries=0`, `timed_out=true`

Android logcat proved the Android-good audio edge in the same worker that the helper traced:

- `A90_AUDIO_STIMULUS_BEGIN` appeared.
- `AudioTrack` became active for `USAGE_MEDIA`.
- `audio_hw_primary` switched `deep-buffer-playback` to speaker, `acdb 15`.
- Worker TID `4619` emitted `select_devices`.
- The same TID emitted ACDB loader activity, including `send_audio_cal`, topology/table calls, `AUDIO_SET_AUDPROC_CAL`, and `AUDIO_SET_AFE_CAL`.
- `/proc/795/fd` showed fd `13 -> /dev/msm_audio_cal`.

The public report deliberately does not include raw private payload bytes, request hex, device serials, or unredacted identifiers.

## Code delta

V2428 adds a thin live-runner wrapper around the shared V2424 runner so the fixed-M0 live rerun has a distinct run/build identity:

- `run_id=V2428`
- `build_tag=v2428-audio-acdb-threadset-clone-child-resume-live-rerun`
- V2425 ADB stage waits inherited.
- V2427 clone-child resume handling inherited.

Validation also exposed an import-time identity leak in the thin wrapper pattern: importing the V2428 wrapper mutated the shared V2424 module `RUN_ID`, which could make V2426 tests see V2428 paths. V2426 and V2428 wrappers now set the shared base identity only inside `dry_run()`, `run_live()`, and wrapper-local `default_live_out_dir()`, then restore it afterward.

## Interpretation

V2428 closes the V2427 verification loop.

The fixed helper did what V2427 required: it observed the clone event and explicitly resumed child TID `4619` for syscall tracing. The same TID later produced the Android-good speaker/ACDB logcat edge, and the target process had `/dev/msm_audio_cal` open. Despite that, the M0 staged/running observer still captured zero `/dev/msm_audio_cal` ioctl entries.

This is no longer explained by:

- ADB staging failure.
- Missing Magisk root.
- Process-main-thread-only capture.
- Clone child never being resumed.

The remaining likely explanation is timing/placement: the transient M0 helper is not early or integrated enough relative to the vendor audio service's ACDB ioctl path.

## Magisk direction

M1 is now justified as the next design unit, but only in the Wi-Fi-style measurement sense.

Allowed M1 direction:

- Temporary Android-side Magisk module or boot-time service packaging.
- Same observer semantics as M0: attach/trace only, filter `/dev/msm_audio_cal`, copy private request buffers, no helper-open of `/dev/msm_audio_cal`, and no calibration ioctl issued by the helper.
- Earlier delivery/placement only: start before the audio service ACDB edge instead of after normal staging.
- Run-local/private artifacts only under `workspace/private/`.
- Explicit cleanup and checked rollback to V2321.
- No native-init runtime dependency and no persistent module left behind.

Still forbidden / out of scope:

- Native ACDB replay before raw ioctl command order, decoded headers, private payload hashes, mem-handle policy, and cleanup behavior are pinned.
- Native speaker write from the Magisk module.
- Persistent `magisk --install-module` as a baseline dependency.
- Shipping a boot image that depends on Magisk to make native audio work.

## Next unit

V2429 should be host-only M1 design/planner work:

1. Define a temporary Magisk module/service layout that starts the same observer before the vendor audio ACDB edge.
2. Preserve the V2321 rollback and Android handoff model.
3. Add static gates proving the module contains no native replay, no `/dev/msm_audio_cal` open/issue path, no persistent install command, and no raw payload in public outputs.
4. Add an exact future gate for a single live M1 measurement attempt.

Native replay remains blocked until raw ioctl command order, decoded headers, private payload hashes, mem-handle policy, and cleanup behavior are pinned.

## Validation

- Android handoff/staging/playback/artifact pull/cleanup/rollback: pass.
- Final V2321 `selftest verbose`: `fail=0`.
- `python3 -m py_compile` on touched V2428 runner/test: pass.
- Focused V2428 wrapper tests: pass.
- Focused V2426 wrapper tests: pass.
- Focused V2424 live-runner regression tests: pass.
- Focused V2423 planner/helper tests: pass.
- Full unittest suite: pass.
- `git diff --check`: pass.
