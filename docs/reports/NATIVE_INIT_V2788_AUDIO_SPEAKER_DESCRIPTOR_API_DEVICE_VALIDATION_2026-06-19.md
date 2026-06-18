# Native Init V2788 Audio Speaker Descriptor API Device Validation

## Summary

- Cycle: `V2788`
- Track: audio speaker descriptor API device validation.
- Decision: `v2788-audio-speaker-descriptor-api-device-pass`
- Result directory: `workspace/private/runs/audio/v2788-audio-speaker-descriptor-api-device-validation-20260619-060515`
- Candidate image SHA256: `358df5cc964b09738dba52371ab9cbd30ac01a4ec99e66f391cd57f0552c5390`
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2788 flashes the V2787 speaker descriptor test image and validates the read-only `audio speaker-map internal-speaker-safe` surface on device.
- The run proves the route API descriptor split survives in the native boot image: each of the six speaker-map entries exposes `id`, `role`, `channel`, `hardware`, and `safety` fields over the serial command surface.
- This is an observability-only validation: no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, PCM write, or playback command is executed.
- Expected pass: all six descriptors are present, `audio.speaker_map.read_only=1`, `route_write_attempted=0`, `playback_attempted=0`, and final rollback `selftest fail=0`.

## Command Summary

- `audio-status`: ok=True rc=0 audio=True profile=False speaker_map=0 descriptors=0 read_only=0
- `audio-profiles`: ok=True rc=0 audio=True profile=False speaker_map=0 descriptors=0 read_only=0
- `audio-profile`: ok=True rc=0 audio=True profile=True speaker_map=0 descriptors=0 read_only=0
- `audio-speaker-map`: ok=True rc=0 audio=True profile=False speaker_map=1 descriptors=1 read_only=1

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- No ADSP boot, `/dev/snd` materialization, audio route apply/reset, ACDB SET, PCM open, mixer write, or playback execute is performed by this validation.
- Public report contains metadata only; full command transcripts stay under `workspace/private/runs/audio/`.
