# Native Init V2972 Nyan pal8-rle Synthetic Live Validation

## Summary

- Cycle: `V2972`
- Track: Video playback / Nyan Cat compact color stream bring-up.
- Decision: `v2972-nyan-pal8-rle-synthetic-live-pass-rollback-ok`
- Result: `PASS`
- Candidate: `v2972-nyan-pal8-rle-synthetic` / `0.10.58`
- Candidate image SHA256: `b6f945bbf63245db443152e2b4545aa32abc70e0d241dbc71efe3161fa610e1d`
- Rollback target: `v2321-usb-clean-identity-rodata` / `0.9.285`
- Rollback image SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Final rollback health: `version_ok=1`, `selftest_fail0=1`

## What Changed

- Added native `A90VSTR2` / `pal8-rle` cache playback support for variable-size streams.
- Fixed the live cache gate so V2 streams accept a positive regular-file size instead of requiring a fixed computed total size.
- Fixed the V2 wire ABI by packing `video_stream_header_v2` and `video_stream_frame_record_v2`; the host encoder emits a 20-byte frame record (`<IIIQ`), while the default C layout padded it to 24 bytes.

## Synthetic Fixture

- Private asset root: `workspace/private/demo-assets/video/v2972-nyan-pal8-rle-synthetic/` (not committed)
- Stream SHA256: `a6c1729f894327c41fbc6dfacc1f25023216a9fe7bd50672a77bbcd4d74faf77`
- Manifest SHA256: `770887b4eea92746f750f78a6582686fe5c344a61aa9d6dbb43bd5d1c7ee562f`
- Geometry: `160x120` @ `30/1` fps
- Frames: `90`
- Format: `pal8-rle`, stream_version=`2`, palette_count=`10`
- Encoded payload bytes: `59706`; stream file bytes: `61622`
- Raw pal8 bytes: `1728000`; raw XBGR bytes: `6912000`; compression_ratio_milli=`34`

## Live Evidence

- Run evidence: `workspace/private/runs/video/v2972-nyan-pal8-rle-synthetic-live-20260620-132018/` (private)
- Cache source: `hit`
- Remote cache manifest: `/mnt/sdext/a90/runtime/video/cache/sha256-a6c1729f894327c41fbc6dfacc1f25023216a9fe7bd50672a77bbcd4d74faf77/manifest.json`
- `video.cache.stream_size=61622`
- `video.cache.stream_expected_size=0` (variable-size V2 sentinel)
- `video.cache.stream_size_match=1`
- `video.cache.format=pal8-rle`
- `video.stream.presented=90` / requested `90` / total `90`
- `video.stream.dropped_frames=0`
- `video.stream.bytes=59706`
- `video.stream.elapsed_ns=2973269635`
- `video.stream.fps_milli=30269`
- `video.stream.present_mode=setcrtc`
- `video.stream.layout=player-hud`
- `video.stream.pixel_format=pal8-rle`
- `video.stream.beat_flash.enabled=0` / source=`none`
- Post-play candidate selftest: `fail=0`

## Validation

- `python3 -m py_compile` for touched Python and tests: pass.
- `python3 -m unittest tests.test_build_native_init_boot_v2972_nyan_pal8_rle_synthetic tests.test_native_video_nyan_pal8_rle_decoder_v2971 tests.test_prepare_nyan_pal8_rle_v2970`: 13 tests pass.
- AArch64 static source build: pass; final boot SHA256 `b6f945bbf63245db443152e2b4545aa32abc70e0d241dbc71efe3161fa610e1d`.
- Live flash via checked helper: boot partition only, readback SHA matched.
- Candidate health: `version/status/selftest` clean before playback.
- Synthetic cache playback: pass (`90/90`, dropped `0`, pixel_format `pal8-rle`, layout `player-hud`).
- Rollback via checked helper to `v2321`: readback SHA matched; final `selftest fail=0`.

## Safety

- No private media, boot image, raw run logs, or SD-cache payloads are committed.
- Device persistent write scope was limited to the boot partition through `native_init_flash.py`; SD runtime cache contains only the private synthetic fixture.
- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
