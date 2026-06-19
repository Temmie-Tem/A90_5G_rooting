# Native Init V2799 Audio Native Ioctl Width Live Handoff

## Summary

- Cycle: `V2799`
- Track: audio core closure gate.
- Decision: `v2799-audio-native-ioctl-width-live-worker-failed-before-rollback`
- Result directory: `workspace/private/runs/audio/v2799-audio-native-ioctl-width-20260619-090337`
- Candidate tag: `v2799-audio-native-ioctl-width`
- Candidate image SHA256: `f07afce570a52b5c9fa59e16932d16b4f83d258b58a2a738e96ce42003ee4e6b`
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`
- Operator audible confirmation: `not-applicable-no-listen-window`
- Frontier: `audio.play.integrated.wait.sound_control.ready=0 elapsed_ms=70250`; SET-cal/ioctl stage was not reached in this run.

## Playback Evidence

- Native command: `audio play internal-speaker-safe --mode listen --duration-ms 8000 --amplitude-milli 150 --manifest /cache/a90-acdb-setcal-replay-v2725/audio-setcal-internal-speaker-safe.manifest --execute`
- Play start rc: `0`
- Worker status done/attempts: `1` / `30`
- Worker status stdout: `workspace/private/runs/audio/v2799-audio-native-ioctl-width-20260619-090337/58_candidate-audio-play-status-30.txt`
- Worker log stdout: `workspace/private/runs/audio/v2799-audio-native-ioctl-width-20260619-090337/59_candidate-audio-native-ioctl-width-log.txt`
- Worker started/done: `1` / `0`
- Listen window begin/end: `0 / 0`
- Integrated done: `0`
- Sound-control ready/timeout: `0 / 1`
- ION materialize seen/ok/alloc: `0 / 0 / 0`
- MSM audio cal materialize seen/ok/open/missing: `0 / 0 / 0 / 0`
- DMABUF msync nonfatal / SET entries prepared: `0 / 0`
- SET-cal native allocate/set request seen: `0 / 0`
- SET-cal first ioctl EFAULT / allocate EFAULT: `0 / 0`
- SET-cal hold/all-set/dealloc: `0 / 0 / 0`
- Route apply/reset OK: `0 / 0`
- PCM write/done: `0 / 0`
- Safety amplitude/duration cap: `1 / 1`

## Live Classification

- V2799 built and booted the native 64-bit ioctl-width candidate (`0.9.312`) and the rollback completed cleanly to `v2321`.
- The worker stopped before `/dev/ion`, `/dev/msm_audio_cal`, or any SET-cal ioctl. The native ioctl request-width fix was therefore compiled but not exercised live.
- The immediate blocker for the integrated playback command is the upstream ADSP/sound-control readiness wait returning ready=`0` after the 70 s settle budget.

## Runtime Artifacts

- Deploy plan: `workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json`
- Native manifest remote path: `/cache/a90-acdb-setcal-replay-v2725/audio-setcal-internal-speaker-safe.manifest`
- Native manifest SHA256: `9be68f78bf8f4d8798e45b7b73e4a3328e6ce31ef476272700dfe3bfe7c1d518`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/00-set-arg-cal39-core-custom-topologies.bin`
- `payload` `/cache/a90-acdb-setcal-replay-v2725/00-payload-cal39-core-custom-topologies.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/01-set-arg-cal20-realhal-01.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/02-set-arg-cal20-realhal-02.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/03-set-arg-cal13.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/04-set-arg-cal09.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/05-set-arg-cal11.bin`
- `payload` `/cache/a90-acdb-setcal-replay-v2725/05-payload-cal11.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/06-set-arg-cal12.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/07-set-arg-cal15.bin`
- `payload` `/cache/a90-acdb-setcal-replay-v2725/07-payload-cal15.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/08-set-arg-cal23.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/09-set-arg-cal16.bin`
- `payload` `/cache/a90-acdb-setcal-replay-v2725/09-payload-cal16.bin`
- `set_arg` `/cache/a90-acdb-setcal-replay-v2725/10-set-arg-cal21.bin`
- `native_manifest` `/cache/a90-acdb-setcal-replay-v2725/audio-setcal-internal-speaker-safe.manifest`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is flashed; runtime ACDB files are staged under `/cache`.
- No forbidden partitions are touched.
- `audio play` uses the source-enforced `internal-speaker-safe` profile caps (`listen` amplitude 0.15, cap 0.2).
- Public report is metadata-only; private ACDB payloads and raw command transcripts stay under `workspace/private/`.
