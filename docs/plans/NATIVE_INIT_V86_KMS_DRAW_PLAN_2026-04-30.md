# Native Init v86 KMS/Draw Plan (2026-04-30)

## Summary

- Target: `A90 Linux init 0.8.17 (v86)`
- Theme: `0.8.17 v86 KMS DRAW API`
- Scope: split only low-level DRM/KMS state and framebuffer drawing primitives into true `.c/.h` modules.
- Non-goals: do not split HUD/menu/input/displaytest policy yet; keep user-visible UI behavior stable.

## Implementation

- Add `a90_kms.c/h` as the owner of DRM/KMS dumb-buffer state, frame begin, frame present, framebuffer info, and probe output.
- Add `a90_draw.c/h` as the owner of framebuffer clear/rect/text/text-fit/outline/test-frame primitive drawing.
- Copy v85 to `init_v86.c` + `v86/*.inc.c`, bump version/build/kmsg/changelog markers, and link the new KMS/draw modules.
- Remove direct `kms_state` and `struct kms_display_state` ownership from the v86 include tree.
- Keep HUD/menu/input/displaytest in the v86 include tree, calling `a90_kms_framebuffer()` and `a90_draw_*()`.

## Validation

- Build static ARM64 with `-Wall -Wextra` and strip `stage3/linux_init/init_v86`.
- Verify strings: `A90 Linux init 0.8.17 (v86)`, `A90v86`, `0.8.17 v86 KMS DRAW API`.
- Confirm no direct `kms_state` or `struct kms_display_state` in `stage3/linux_init/v86`.
- Flash `stage3/boot_linux_v86.img` from native bridge through TWRP and verify `cmdv1 version/status`.
- Regress display paths: `kmsprobe`, `kmssolid`, `kmsframe`, `statushud`, `displaytest`, `cutoutcal`, `autohud`, `screenmenu`, `inputmonitor` q cancel.

## Next

- v87 should split one higher UI layer at a time, starting with HUD or input, not full menu/UI at once.
