# Native Init V2973 Nyan Real Asset Prep

## Summary

- Cycle: `V2973`
- Track: Nyan Cat Player HUD / compact color stream enabler.
- Decision: `v2973-nyan-real-asset-ready`
- Result: `PASS`
- Scope: host-only private asset preparation; no device flash or runtime state.
- Media policy: source media, rendered frames, PCM, and A90VSTR output remain private and are not committed.

## Pipeline

- Video: ffmpeg `palettegen`/`paletteuse` quantizes MP4 frames to a bounded global palette before V2970 encodes `A90VSTR2` `pal8-rle`.
- Audio: ffmpeg renders bounded-volume 48 kHz stereo signed 16-bit little-endian PCM.
- ffmpeg available: `1`
- ffprobe available: `1`

## Output

- Output root: `workspace/private/demo-assets/video/v2973-nyancat-pal8-rle-preview`
- Source probe duration: `216.827937`
- Frame count: `300`
- Video: `540x360` @ `30/1`
- Format: `pal8-rle`, stream_version=`2`, palette_count=`128`
- Stream SHA256: `9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573`
- Stream bytes: `6559098`
- Encoded payload bytes: `6552510`
- Raw pal8 bytes: `58320000`
- Raw XBGR bytes: `233280000`
- Compression ratio milli vs pal8: `112`
- Audio PCM SHA256: `4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de`
- Audio PCM bytes: `1920000`

## Validation

- `py_compile`: `1`
- focused tests: `1`
- live host asset run: `1`
- Encoder roundtrip validation is covered by V2970 tests; this unit exercises it on real private Nyan content.

## Next

- Seed this private asset through the existing SD video cache path.
- Wire a `video demo nyan` / menu handler that uses the SHA-addressed stream and bounded PCM loop.
- Then run a rollbackable V2974/V2975 live Player HUD slice before attempting full looping playback.
