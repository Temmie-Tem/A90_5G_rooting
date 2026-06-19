# Native Init V2819 Audio Status/Selftest Live Validation

## Summary

- Cycle: `V2819`
- Track: post-promotion audio Tier C device observability.
- Decision: `v2819-audio-status-selftest-marker-missing-before-rollback`
- Result directory: `workspace/private/runs/audio/v2819-audio-status-selftest-live-20260619-115753`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2818_audio_status_selftest.img`
- Candidate SHA256: `6eb4f6d864a2d6b0cc1c188e298706cfa668c2b4f02a8f78f18eae8d1d7ecee5`
- Candidate version/tag observed: `1`
- `audio status` marker pass: `0` (13/16)
- `selftest verbose` audio marker pass: `0` (0/8)
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2819 flashes the V2818 `0.10.1` audio observability image and validates the new read-only status/selftest surfaces on hardware.
- Expected pass: `audio status` exposes the promoted `0.10.0` core metadata and safety fields, `selftest verbose` exposes the static audio row, and final rollback to `v2321` ends with `selftest fail=0`.
- This validation intentionally performs no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, mixer write, speaker write, or playback.

## Missing Markers

- `audio status`: `['audio.status.route.control_count=13', 'audio.status.speaker.count=6', 'audio.status.safety.max_amplitude_milli=200']`
- `selftest verbose`: `['selftest audio:', 'core=0.10.0', 'profile=internal-speaker-safe', 'route=13', 'speakers=6', 'cap=200', 'boost=blocked', 'sp=unverified']`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- Public report contains metadata only; full serial transcripts stay under `workspace/private/runs/audio/`.
## Post-Run Analysis

- The candidate boot and rollback path worked: V2818 booted as `0.10.1`, and rollback to `v2321` ended with `selftest fail=0`.
- `audio status` did expose the V2816 core-promotion surface. The three reported missing `audio status` markers were validator-key drift: the implementation prints `audio.status.profile.route_control_count=13`, `audio.status.profile.speaker_count=6`, and `audio.status.safety.amplitude_cap_milli=200`.
- `selftest verbose` did not print the V2817 `audio` row in the captured output. The summary still reported `entries=13` and `warn=2`, and the visible row numbers skipped `10`, so the audio record appears to be recorded but not emitted/captured as a visible verbose row.
- Follow-up: V2820 should focus on the selftest audio-row visibility path and use the corrected `audio status` marker names; no audio playback or runtime audio write is needed.
