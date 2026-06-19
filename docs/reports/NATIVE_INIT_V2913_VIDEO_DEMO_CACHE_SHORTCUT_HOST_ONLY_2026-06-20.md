# Native Init V2913 Video Demo Cache Shortcut Host-Only

## Summary

- Cycle: `V2913`
- Track: active Video playback pipeline on existing KMS display.
- Decision: `v2913-video-demo-cache-shortcut-host-only-pass`
- Result: PASS
- Device flash: `no`
- Scope: make the already-proven SD-card frame cache easier to reuse for fast video tests.

## Rationale

- Pre-storing video frames is the right optimization, but the correct storage target is the SD/runtime SHA cache, not the boot image.
- The V2912 cache asset is multi-GB (`2106428092` bytes), so embedding frames into boot/ramdisk would bloat every flash, slow image packing/flashing, and make rollback artifacts harder to manage.
- The SD cache already preserves the expensive generated stream across test boots; V2909/V2912 proved the fast repeat pattern: full verify once, then `--trust-cache` playback with manifest and size checks.

## Included Delta

- Adds `video demo badapple-scale [status|verify|play] [--trust-cache] ...` as a thin native shortcut over `video cache preset badapple-scale`.
- Keeps existing `video demo` frame-pattern behavior for `bars`, `checker`, `mono`, and colors.
- Emits explicit demo policy markers:
  - `video.demo.storage=sd-sha-cache`
  - `video.demo.boot_asset_policy=boot-image-carries-player-not-frames`
- Adds `video.status.next_demo=video demo badapple-scale [status|verify|play] [--trust-cache]`.

## Safety

- No new storage writes are added by the command surface.
- No raw frame, PCM, boot image, or generated cache payload is committed.
- No Venus, GPU, raw DSI, backlight, PMIC, PWM, regulator, GPIO, or GDSC path is added.
- `--trust-cache` remains explicit; default cache playback still uses the existing full-SHA path.

## Validation

- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_video_cache_command_v2904`
  - Result: `10` tests passed.
- AArch64 compile check:
  - Output: `workspace/private/builds/native-init/v2913-video-demo-cache-shortcut-compile/init_v2913_video_demo_cache_shortcut`
  - `file`: `ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped`
  - Compile warnings: existing `a90_usb_gadget.c` configfs-name truncation warnings only.
- `git diff --check`: passed.

## Next

- Build a V2914 candidate image carrying the shortcut.
- Live-validate `video demo badapple-scale status`, `verify`, and a bounded `play --trust-cache` slice against the existing SD cache, then roll back to `v2321`.
