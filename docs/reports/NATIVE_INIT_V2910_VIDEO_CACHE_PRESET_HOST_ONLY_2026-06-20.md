# Native Init V2910 Video Cache Preset Host-Only

## Summary

- Cycle: `V2910`
- Track: active Video playback pipeline on existing KMS display.
- Decision: `v2910-video-cache-preset-host-only-pass`
- Device action: `no`
- Scope: add a named native-init video cache preset for the already-proven SD SHA cache.

## Change

- Adds `video cache preset badapple-scale [status|verify|play] [options]` as a first-class command surface.
- The preset maps to the V2900/V2906/V2909 SD cache SHA `878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890`.
- The preset is explicitly named `badapple-scale`, not real Bad Apple content: the cached asset ID remains `v2874-synthetic-mono1-checker-6501f`.
- The command reuses the existing `video cache status|verify|play` implementation after resolving the preset to its content SHA.
- `--trust-cache`, `--frames`, `--present`, and audio-sync options stay on the existing `play` path.

## Rationale

- V2909 proved the fast repeat-test pattern: full SD cache verification once, then explicit `--trust-cache` playback without rehashing the multi-GB stream.
- This unit makes that pattern callable without manually typing the long SHA.
- Large frames still live on the SD SHA-addressed cache; the boot image carries only command logic and small metadata.

## Safety

- Host-only source change; no flash or live device action in this unit.
- No video payloads, raw frames, boot images, or private logs are committed.
- Playback remains the existing KMS dumb-buffer/page-flip stream path; no Venus, GPU, raw DSI, panel, backlight, PMIC, PWM, regulator, GPIO, or GDSC path is added.
- Rollback target remains `v2321-usb-clean-identity-rodata` for any future live validation.

## Validation

- Focused test: `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_video_cache_command_v2904` (`9` tests).
- AArch64 compile: `build_native_init_boot_v724.build_init()` to private `workspace/private/builds/native-init/v2910-video-cache-preset-compile/init_v2910_video_cache_preset`; `file` reports static stripped AArch64 ELF.
- Compile warnings: pre-existing USB gadget basename truncation warnings only; no V2910 video-cache warning.
- Whitespace: `git diff --check`.

## Next

- Build a V2911 candidate image with this preset surface, then live-validate `video cache preset badapple-scale status|verify|play --trust-cache` against the existing SD cache and roll back to `v2321`.
