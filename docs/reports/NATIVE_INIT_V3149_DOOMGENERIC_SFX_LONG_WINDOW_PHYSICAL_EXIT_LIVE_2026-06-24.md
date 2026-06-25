# Native Init V3149 DOOM SFX Long Window + Physical Exit Live

Date: 2026-06-24

## Scope

- Candidate: `v3149-doomgeneric-sfx-long-window-physical-exit`
- Native init version: `0.10.131`
- Goal: remove the visible/audio stutter caused by periodic DOOM SFX worker refresh and add a native physical-button exit path for the DOOM loop.

## Artifact

- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3149_doomgeneric_sfx_long_window_physical_exit.img`
- Boot SHA256: `348dd806f20d2f2ea971f152a516a0aa5a2fcae0ed1098eb631b9abe2fae3b9b`
- Init SHA256: `2cffe2faf6d8cdf0ebba9c8cc3c7415d44468cc06ba11fb44af94662cf86a791`
- Ramdisk SHA256: `6101ed73825766886ae30b72b0343fd8479d068b47724a20c0adcfa94e86958f`
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Flash Gate

- Rollback baseline present and hash-confirmed:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`
    - `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - `boot_linux_v2237_supplicant_terminate_poll.img`
    - `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - `boot_linux_v48.img`
- Pre-flash live baseline:
  - `version`: `A90 Linux init 0.10.130 (v3148-doomgeneric-sfx-stream-refresh)`
  - `status`: `selftest: pass=12 warn=1 fail=0`
  - `selftest verbose`: `pass=12 warn=1 fail=0`
- Flash helper:
  - Command shape: `native_init_flash.py --from-native --expect-version v3149-doomgeneric-sfx-long-window-physical-exit --expect-sha256 <V3149_BOOT_SHA> <V3149_BOOT_IMAGE>`
  - Recovery/TWRP path was exercised by the checked helper before boot write.
  - Recovery ADB reached expected `recovery` state. Device serial redacted.
  - Remote image SHA256 matched local SHA256.
  - Boot partition prefix readback SHA256 matched `348dd806f20d2f2ea971f152a516a0aa5a2fcae0ed1098eb631b9abe2fae3b9b`.

## Post-Flash Health

- `version`: `A90 Linux init 0.10.131 (v3149-doomgeneric-sfx-long-window-physical-exit)`
- `status`: `BOOT OK`, `selftest: pass=12 warn=1 fail=0`
- `selftest verbose`: `pass=12 warn=1 fail=0`
- No rollback was required.

## DOOM Audio Validation

- Loop-start succeeded with runtime private WAD:
  - `video.demo.engine.active=doomgeneric-private-link-v3149-sfx-long-window-physical-exit`
  - `video.demo.sound.active=native-doom-sfx-pcm-stream-long-window-v3149`
  - `video.demo.doom.audio.stream_path=/cache/a90-runtime/a90-doomgeneric-v3149-sfx.pcmstream`
  - `audio.play.cap.effective_duration_ms=240000`
  - `audio.play.cap.duration_policy=doom-sfx-pcm-stream`
  - `audio.play.cap.doom_sfx_stream_ms=240000`
- Worker stability sample:
  - 20:13:30: `pid=657`, `done=0`, `duration_ms=240000`
  - 20:13:35: `pid=657`, `done=0`, `duration_ms=240000`
  - 20:13:41: `pid=657`, `done=0`, `duration_ms=240000`
  - 20:13:46: `pid=657`, `done=0`, `duration_ms=240000`
  - 20:13:52: `pid=657`, `done=0`, `duration_ms=240000`
- Result: pass. The V3148-style 13s worker refresh did not recur during this sample.

## Physical Button Exit Validation

- Built-in physical exit path is enabled in V3149.
- Static source path:
  - Physical exit listens on `event3,event0`.
  - Exit keys: `KEY_POWER`, `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN`.
  - Exit action: stop DOOM helper and stop the audio corun worker.
- Live capability check:
  - `inputscan.event=event3 name=gpio_keys class=buttons key_volup=1`
  - `inputscan.event=event0 name=qpnp_pon class=buttons key_power=1 key_voldown=1`
- Live event capture:
  - `doominputmux event3,event0 8 15000` timed out with `captured=0/8`.
  - Because no physical key event was observed during the capture window, the physical-exit behavior is not live-confirmed yet.

## Decision

- V3149 flash and health validation: pass.
- DOOM SFX long-window validation: pass.
- Physical-button exit source and input capabilities: pass.
- Physical-button exit live press confirmation: pending operator key event.
