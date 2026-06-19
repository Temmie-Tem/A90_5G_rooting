# Native Init V2825 Audio Screenapp Route Map Live Validation

## Summary

- Cycle: `V2825`
- Track: post-promotion audio Tier C speaker/route map observability.
- Decision: `v2825-audio-status-selftest-device-pass`
- Result directory: `workspace/private/runs/audio/v2825-audio-status-selftest-live-20260619-124845`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2824_audio_screenapp_map.img`
- Candidate SHA256: `2f6b1c902ee3ad1e06850feb04df847cc4c85881154af0ae28f4ce6c56d8035c`
- Candidate version/tag observed: `1`
- `audio status` marker pass: `1` (16/16)
- `selftest verbose` audio marker pass: `1` (8/8)
- `screenapp audio-map` marker pass: `1` (6/6)
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2825 flashes the V2824 `0.10.4` audio route-map image and validates the display-only `screenapp audio-map` path on hardware.
- The screenapp validation is intentionally display/KMS only; it performs no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, mixer write, speaker write, or playback.
- Expected pass: existing `audio status`/`selftest verbose` audio markers remain present, and `screenapp audio-map` reports `screenapp.presented=1`.

## Missing Markers

- `audio status`: `[]`
- `selftest verbose`: `[]`
- `screenapp audio-map`: `[]`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- Public report contains metadata only; full serial transcripts stay under `workspace/private/runs/audio/`.
