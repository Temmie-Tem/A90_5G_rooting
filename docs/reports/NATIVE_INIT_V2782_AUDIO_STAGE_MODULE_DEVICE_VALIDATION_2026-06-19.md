# Native Init V2782 Audio Stage Module Device Validation

## Summary

- Cycle: `V2782`
- Track: audio stage module device validation.
- Decision: `v2782-audio-stage-module-device-pass`
- Result directory: `workspace/private/runs/audio/v2782-audio-stage-module-device-validation-20260619-044123`
- Candidate image SHA256: `6bb5aa207e378ea6a98115085e2af3316acc16ccf71ab4d5974b6f4d76f734ca`
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2779 splits the explicit stage contract into `a90_audio_stage.{h,c}` while preserving the read-only native-init API surface.
- This run flashes the V2779 test image, checks the stage-module-backed read-only audio commands on device, confirms prereq does not claim runtime state is verified, then rolls back to V2321.
- V2782 uses the V2781 hardened runner path: selftest validation accepts the structured protocol envelope when the human text stream is desynchronized, and rollback can fall back to recovery-mode flashing if native-to-recovery handoff times out after the device reaches recovery.
- Expected pass: `audio.prereq.read_only=1`, `write_attempted=0`, `playback_attempted=0`, all stage commands present, no `audio.prereq.error`, and final rollback `selftest fail=0`.

## Command Summary

- `audio-status`: ok=True rc=0 audio=True prereq_version=False read_only=False stage_order=False commands=0 snd_ready=False dry_run_ok=False prereq_error=False
- `audio-profiles`: ok=True rc=0 audio=True prereq_version=False read_only=False stage_order=False commands=0 snd_ready=False dry_run_ok=False prereq_error=False
- `audio-profile`: ok=True rc=0 audio=True prereq_version=False read_only=False stage_order=False commands=0 snd_ready=False dry_run_ok=False prereq_error=False
- `audio-stages`: ok=True rc=0 audio=True prereq_version=False read_only=False stage_order=False commands=0 snd_ready=False dry_run_ok=False prereq_error=False
- `audio-prereq`: ok=True rc=0 audio=True prereq_version=True read_only=True stage_order=True commands=1 snd_ready=True dry_run_ok=False prereq_error=False
- `audio-play-dry-run`: ok=True rc=0 audio=True prereq_version=False read_only=False stage_order=False commands=0 snd_ready=False dry_run_ok=True prereq_error=False

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- No audio route apply, ACDB SET, PCM open, mixer write, or playback execute is performed by this validation.
- Public report contains metadata only; full command transcripts stay under `workspace/private/runs/audio/`.
