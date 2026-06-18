# Native Init V2772 Audio PCM Writer Device Validation

## Summary

- Cycle: `V2772`
- Track: audio command PCM writer device validation.
- Decision: `v2772-audio-pcm-writer-reached-alsa-open`
- Result directory: `workspace/private/runs/audio/v2772-audio-pcm-writer-device-validation-20260619-031719`
- Candidate image SHA256: `c0645f12f385491f189bc7a2238f4a186fb509bfa96e10ce5de651eb5551ade8`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2771 moved `audio play --execute` from a source refusal into a bounded native ALSA PCM writer.
- This run records whether the on-device command reaches `open` / `HW_PARAMS` / `PREPARE` / `WRITEI` / `DRAIN`, or fails at a concrete device errno.
- The next modular API cleanup should be based on this device result, not more host-only assumptions.
- Device result: the old `execute-not-implemented-native-pcm` refusal did not appear, and `audio play --execute` reached the native PCM open path.
- Concrete frontier: `audio.play.execute.open.rc=-1 errno=2` for `/dev/snd/pcmC0D0p`, meaning the writer is now live but the speaker playback entrypoint still needs the prerequisite stage orchestration (`ADSP` + `/dev/snd` materialization + app-type + SET replay + route) before PCM open can progress to `HW_PARAMS`.
- API implication: keep `audio play` as a bounded primitive, but the next feature unit should either add a higher-level speaker profile runner/command that performs prerequisites in order, or make `audio play --execute` refuse clearly when required prerequisites are absent.

## Command Summary

- `audio-status`: ok=True rc=0 dry_run_ok=False old_refusal=False execute_supported=False open_attempt=False hw_params=False prepare=False write_attempt=False done=False
- `audio-profiles`: ok=True rc=0 dry_run_ok=False old_refusal=False execute_supported=False open_attempt=False hw_params=False prepare=False write_attempt=False done=False
- `audio-profile`: ok=True rc=0 dry_run_ok=False old_refusal=False execute_supported=False open_attempt=False hw_params=False prepare=False write_attempt=False done=False
- `audio-stages`: ok=True rc=0 dry_run_ok=False old_refusal=False execute_supported=False open_attempt=False hw_params=False prepare=False write_attempt=False done=False
- `audio-play-dry-run`: ok=True rc=0 dry_run_ok=True old_refusal=False execute_supported=True open_attempt=False hw_params=False prepare=False write_attempt=False done=False
- `audio-play-execute-native-pcm`: ok=True rc=-2 dry_run_ok=False old_refusal=False execute_supported=True open_attempt=True hw_params=False prepare=False write_attempt=False done=False

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- No credentials are used.
- Public report contains metadata only; full command transcripts stay under `workspace/private/runs/audio/`.
