# Native Init V2829 Audio Route-Map Safety Labels Live Validation

## Summary

- Cycle: `V2829`
- Track: post-promotion audio Tier C route-map observability.
- Decision: `v2829-audio-status-selftest-device-pass`
- Result directory: `workspace/private/runs/audio/v2829-audio-status-selftest-live-20260619-131615`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v2828_audio_route_map_safety.img`
- Candidate SHA256: `f7ad559ec519c7c9d8f537d3549ec4699dac911900ae5cb972ae50681133d69f`
- Candidate version/tag observed: `1`
- `audio status` marker pass: `1` (16/16)
- `selftest verbose` audio marker pass: `1` (8/8)
- `screenapp audio-map` marker pass: `1` (6/6)
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Finding

- V2829 flashes the V2828 `0.10.6` route-map safety-label candidate and validates that the image boots, exposes `audio status`, and still renders the display-only audio route-map screen.
- V2828 source tests cover the label delta (`BOOST WRITE BLOCKED`, `SP UNVERIFIED`, per-side route/observer/boost counts). This live run checks the candidate image and renderer on hardware after that safety-label polish.
- The screenapp validation is intentionally display/KMS only; it performs no ADSP boot, `/dev/snd` materialization, route apply/reset, ACDB SET, PCM open, mixer write, speaker write, or playback.

## Missing Markers

- `audio status`: `[]`
- `selftest verbose`: `[]`
- `screenapp audio-map`: `[]`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is written.
- No forbidden partitions are touched.
- Public report contains metadata only; full serial transcripts stay under `workspace/private/runs/audio/`.
