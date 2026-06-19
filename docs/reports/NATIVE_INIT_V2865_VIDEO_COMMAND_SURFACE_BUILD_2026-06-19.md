# NATIVE_INIT V2865 — Video command surface static build

Date: 2026-06-19
Scope: native-init source implementation + host static build validation
Device action: none
Decision: `v2865-video-command-surface-build-pass`

## Summary

V2864 proved the resident `v2321` baseline exposes a usable DRM/KMS display path:
`/dev/dri/card0`, connected DSI output, `DRM_CAP_DUMB_BUFFER=1`, and `1080x2400@60`.
V2865 turns that result into the first native Video command surface in source, without
flashing it yet.

Implemented commands:

- `video` / `video status`: read-only KMS/video status markers.
- `video frame [bars|checker|mono|0xRRGGBB]`: one bounded CPU-rendered frame through the
  existing KMS dumb-buffer path.
- `video demo ...`: alias for the same single-frame path.

The command explicitly keeps the current Video safety boundary visible in status output:
Venus is not used, KGSL is not used, raw DSI is blocked, and power/backlight-style writes
are blocked.

## Source changes

### `workspace/public/src/native-init/v319/30_status_hud.inc.c`

Adds:

- `cmd_video_status()`:
  - prints `video.status.*` markers;
  - reads existing KMS state through `a90_kms_info()`;
  - performs no DRM open, no buffer allocation, and no display write.
- `cmd_video_frame()`:
  - supports `bars`, `checker`, `mono`, and solid `0xRRGGBB` patterns;
  - uses only `a90_kms_begin_frame()`, `a90_kms_framebuffer()`, existing `a90_draw_*()` helpers,
    and `a90_kms_present()`;
  - emits `video.frame.*` markers on success.
- `handle_video()`:
  - default subcommand is `status`;
  - validates command usage and keeps frame/demo paths explicit.

### `workspace/public/src/native-init/v319/80_shell_dispatch.inc.c`

Adds the top-level command table entry:

```text
video [status|frame [bars|checker|mono|0xRRGGBB]]
```

The command is grouped under `A90_CMD_GROUP_DISPLAY`.

### `workspace/public/src/native-init/a90_controller.c`

Allows only the read-only forms while the menu/HUD guard is active:

- `video`
- `video status`

`video frame` / `video demo` remain blocked by the existing busy policy while the menu is
active, so an operator must clear the HUD/menu with `hide` before presenting a new frame.

## Validation

Host static validation only:

- Built the full native-init translation unit with `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra`.
- Stripped and inspected the private binary with `file`.
- Binary type: `ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped`.
- Private validation binary: `workspace/private/builds/native-init/v2865-video-command-surface/init_v2865_video_command_surface`.
- Private binary SHA256: `b8aebe576559336b7ad25179cf675a280bbe4a59dfb9b303c254454396535231`.
- `strings` on the private binary confirms the new `video.status.*`, `video.frame.*`, and
  `A90 VIDEO FRAME` markers are present.
- `git diff --cached --check` passed before commit.

The static build emitted pre-existing `a90_usb_gadget.c` `snprintf` truncation warnings from
USB gadget inventory code. No new warning was attributable to the V2865 `video` code.

## Safety

- No build artifact is committed.
- No boot image was packed or flashed in this unit.
- No device action was performed.
- No Wi-Fi, audio, Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO,
  or GDSC action was run.
- The new frame path reuses the existing KMS dumb-buffer abstraction that V2864 proved live.

## Next unit

V2866 should build a rollbackable test boot image from this source and live-validate:

1. flash only via `workspace/public/src/scripts/revalidation/native_init_flash.py`;
2. health-check `version`, `status`, and `selftest verbose`;
3. run `video status` while HUD is active and confirm it is allowed/read-only;
4. run `hide`, then `video frame bars` or `video frame checker`;
5. confirm `video.frame.presented=1` and final `selftest fail=0`;
6. rollback to `v2321` and verify final `selftest fail=0`.

Do not expand to Bad Apple / Nyan Cat / DOOM until this single-frame path is live-proven.
