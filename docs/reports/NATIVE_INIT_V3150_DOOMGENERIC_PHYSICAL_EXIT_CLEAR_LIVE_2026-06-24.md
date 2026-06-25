# Native Init V3150 DOOM Physical Exit Clear Live

Date: 2026-06-24

## Scope

- Candidate: `v3150-doomgeneric-physical-exit-clear`
- Native init version: `0.10.132`
- Goal: make DOOM physical-button exit visibly clear the stale DOOM frame and stop the loop/audio path.

## Artifact

- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3150_doomgeneric_physical_exit_clear.img`
- Boot SHA256: `fe51d9fd185b209d16a2e168392931fa53e47a6649df76bafe6b402ab0feed20`
- Init SHA256: `cc917f3f8453a43b9bd05eab1c31137a56a37c87926876d6817ba43c0ed8cfe9`
- Ramdisk SHA256: `5cc2a5e909e8b4210503b52ec8c0893da3f29d07aeacae3b6e95fd7dfbcc8bce`
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Flash Gate

- Rollback baseline present and hash-confirmed:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`
    - `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - `boot_linux_v2237_supplicant_terminate_poll.img`
    - `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - `boot_linux_v48.img`
- Pre-flash live baseline:
  - `version`: `A90 Linux init 0.10.131 (v3149-doomgeneric-sfx-long-window-physical-exit)`
  - `status`: `selftest: pass=12 warn=1 fail=0`
  - `selftest verbose`: `pass=12 warn=1 fail=0`
- Flash helper:
  - Command shape: `native_init_flash.py --from-native --expect-version v3150-doomgeneric-physical-exit-clear --expect-sha256 <V3150_BOOT_SHA> <V3150_BOOT_IMAGE>`
  - Recovery/TWRP path was exercised by the checked helper before boot write.
  - Recovery ADB reached expected `recovery` state. Device serial redacted.
  - Remote image SHA256 matched local SHA256.
  - Boot partition prefix readback SHA256 matched `fe51d9fd185b209d16a2e168392931fa53e47a6649df76bafe6b402ab0feed20`.

## Post-Flash Health

- `version`: `A90 Linux init 0.10.132 (v3150-doomgeneric-physical-exit-clear)`
- `status`: `BOOT OK`, `selftest: pass=12 warn=1 fail=0`
- `selftest verbose`: `pass=12 warn=1 fail=0`
- No rollback was required.

## DOOM Start

- Loop-start succeeded with runtime private WAD:
  - `video.demo.engine.active=doomgeneric-private-link-v3150-physical-exit-clear`
  - `video.demo.sound.active=native-doom-sfx-pcm-stream-long-window-v3150`
  - `video.demo.doom.audio.stream_path=/cache/a90-runtime/a90-doomgeneric-v3150-sfx.pcmstream`
  - `audio.play.cap.effective_duration_ms=240000`
  - `audio.play.cap.duration_policy=doom-sfx-pcm-stream`
  - `audio.play.worker.pid=743`
  - `video.demo.doom.loop_start.pid=742`

## Physical Button Exit Validation

- Before operator press, repeated `loop-status` showed:
  - `video.demo.doom.loop_status.active=1`
  - `video.demo.doom.loop_status.pid=742`
- Bounded raw event capture:
  - Command: `doominputmux event3,event0 6 60000`
  - Captured `KEY_VOLUMEUP` down/up on `event3`.
  - Captured `KEY_VOLUMEDOWN` down on `event0`.
- During the same capture window, the background DOOM loop emitted:
  - `doomstop-clear: presented framebuffer 1080x2400 on crtc=133`
  - `video.demo.doom.clear.reason=physical-button-exit`
  - `video.demo.doom.clear.rc=0`
  - `video.demo.doom.audio.stop.requested=1`
  - `audio.stop.worker.status_pid=743`
  - `audio.stop.worker.status_stop_rc=0`
- After the operator press:
  - `video.demo.doom.loop_status.active=0`
  - `video.demo.doom.loop_status.pid=-1`
  - `/proc/743/status`: `No such file or directory`
  - `status`: `reaper: ... last_pid=743 last=signal=15`

## Residual

- `audio play-status` still reports the stale worker status file:
  - `audio.play.worker.done=0`
  - `audio.play.worker.pid=743`
- The process is gone and reaper confirms signal termination, so audio execution stopped. The stale status file is a reporting cleanup issue for a follow-up unit, not a live worker.

## Decision

- V3150 flash and health validation: pass.
- Physical button event capture: pass.
- Physical button loop exit: pass.
- Physical button display clear: pass.
- Audio worker process termination: pass.
- Audio status file freshness: follow-up recommended.
