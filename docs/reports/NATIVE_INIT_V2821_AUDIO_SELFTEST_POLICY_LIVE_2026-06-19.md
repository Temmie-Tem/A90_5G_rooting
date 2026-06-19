# Native Init V2821 Audio Selftest Policy Live Validation

## Summary

- Cycle: `V2821`
- Track: post-promotion audio Tier C device observability.
- Decision: `v2821-audio-status-selftest-device-pass`
- Result directory: `workspace/private/runs/audio/v2819-audio-status-selftest-live-20260619-120947`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2820_audio_selftest_policy.img`
- Candidate SHA256: `73094ccf1288fa142ae8520d3b47ac6bb31a5c4be90e920e1e27714acbbbea41`
- Candidate version/tag observed: `1`
- `audio status` marker pass: `1` (16/16)
- `selftest verbose` audio marker pass: `1` (8/8)
- Rollback attempted: `1`
- Rollback recovery fallback used: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2821 flashes the V2820 `0.10.2` audio selftest policy image and validates the read-only `audio status` plus `selftest verbose` surfaces on hardware.
- Expected pass: `audio status` retains the promoted `0.10.0` core metadata, and `selftest verbose` emits a PASS `audio` row with `boost=blocked` and `sp=unverified`.
- This validation intentionally performs no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, mixer write, speaker write, or playback.

## Missing Markers

- `audio status`: `[]`
- `selftest verbose`: `[]`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- Public report contains metadata only; full serial transcripts stay under `workspace/private/runs/audio/`.
- Rollback completed through the recovery fallback path and ended at `v2321` with `selftest fail=0`; no residual candidate boot state remained.
