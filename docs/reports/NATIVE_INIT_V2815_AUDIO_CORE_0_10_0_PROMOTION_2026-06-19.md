# Native Init V2815 Audio Core 0.10.0 Promotion

## Summary

- Run ID: `V2815`
- Purpose: promote the device-validated native audio core candidate to the `0.10.0` line.
- Promoted audio-core candidate: `A90 Linux init 0.10.0 (v2812-audio-core-promotion-candidate)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2812_audio_core_promotion_candidate.img`
- Boot SHA256: `9cf680ae7dce1dac53b58a72e98668f5f6347bc14d6a64428f06ce2af830cdd0`
- Device flash in this run: no; this is a documentation/promotion decision over the V2812 artifact after V2814 live validation.
- Safety rollback net: `v2321` remains the checked rollback target until the flash-gate contract is deliberately updated.

## Evidence

- V2812 built the `0.10.0` candidate artifact and recorded the source-build metadata.
- V2814 flashed that candidate, ran `audio play --mode listen --execute`, and reported `v2814-late-manifest-play-pass-before-rollback`.
- V2814 evidence includes ADSP/card/control publication after late deploy, manifest wait ready, ACDB SET replay hold/all-set/deallocate, route apply/reset, PCM write/drain, amplitude/duration caps, and rollback to `v2321` with `selftest fail=0`.
- The public V2814 report is metadata-only; private ACDB payloads and raw transcripts remain under `workspace/private/`.

## Decision

- The native `audio play` core-function gate is closed for the `0.10.0` candidate.
- The audio feasibility investigation is closed; remaining audio work is post-promotion productization: route naming, status/UI polish, speaker map, and optional boot chime.
- Video becomes eligible only if the operator explicitly charters it; it is not auto-started by this promotion.

## Boundaries

- No new flash, runtime audio write, Wi-Fi action, forbidden partition write, or raw payload commit was performed in V2815.
- Do not treat this report as permission to weaken the `v2321` rollback safety net; AGENTS.md remains authoritative for flash gates.
