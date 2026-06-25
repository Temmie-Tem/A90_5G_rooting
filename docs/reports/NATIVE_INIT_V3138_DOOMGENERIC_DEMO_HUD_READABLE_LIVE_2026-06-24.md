# Native Init V3138 DOOMGENERIC Readable Demo HUD Live Validation

## Summary

- Cycle: `V3138`
- Live artifact: `workspace/private/inputs/boot_images/boot_linux_v3137_doomgeneric_demo_hud_readable.img`
- Boot SHA256: `d1a6efd0dd0b4e4f8f13ae2828e754e58fc2af4dead585cfc5a322170cd93edb`
- Init after flash: `A90 Linux init 0.10.122 (v3137-doomgeneric-demo-hud-readable)`
- Result: PASS
- Current state after validation: continuous DOOM loop running.

## Safety Gate

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash scope: boot image only.
- Rollback images confirmed before flash:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`: expected SHA256 match.
  - `boot_linux_v2237_supplicant_terminate_poll.img`: expected SHA256 match.
  - `boot_linux_v48.img`: present, SHA256 captured.
- Recovery/TWRP availability: present per recovery guide and prior live validation material.
- Pre-flash health: V3135 booted, `status` OK, `selftest` fail=0.
- No Wi-Fi connect, DHCP, or Wi-Fi ping was run.

## Flash

- Local image marker matched expected V3137 version string.
- Local image SHA256 matched expected V3137 boot SHA.
- Recovery ADB became ready.
- Remote pushed image SHA256 matched local SHA.
- Boot partition readback prefix SHA256 matched local SHA.
- Native-init post-reboot verification passed through the flash helper.

## Post-Flash Health

- `version`: `0.10.122 build=v3137-doomgeneric-demo-hud-readable`.
- `status`: boot OK, SD runtime backend mounted writable, USB-local transport ready.
- `selftest`: pass=12 warn=1 fail=0.
- Note: the first manual post-flash selftest retry received a fragmented serial response without the final END marker; immediate retry succeeded with rc=0.

## DOOM HUD Contract

- Runtime WAD path: SD runtime path, not bundled in boot.
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- WAD verify: present=1, regular=1, magic=IWAD, SHA256 match=1, ok=1.
- Engine: `doomgeneric-private-link-v3137-demo-hud-readable`.
- Readable HUD markers:
  - `video.demo.doom.dashboard.readable_spacing=1`
  - `video.demo.doom.dashboard.text_scale=title5-main3-small2`
  - `a90.doomgeneric.v3137.demo_hud=fast-readable-spacing-title5-main3`
  - `a90.doomgeneric.v3137.scale=producer-960x600-1to1-demo-hud-readable`

## Loop Timing

- First 240-frame bounded loop:
  - rc=0, frames_presented=240, shared_missed_frames=0.
  - draw avg/max: `3805/242075 us`.
  - total avg/max: `8587/244566 us`.
  - Interpretation: one cold-run spike after flash.
- Warm 240-frame bounded loop:
  - rc=0, frames_presented=240, shared_missed_frames=0.
  - draw avg/max: `2809/3178 us`.
  - total avg/max: `7566/17544 us`.
  - flip delta avg/max: `19910/33297 us`.

## Host Input Path

- USB-NCM host profile was rebound to the post-reboot NCM interface through NetworkManager.
- Host route to the USB-NCM device endpoint used the USB-NCM interface after rebinding.
- USB-NCM ping: 2/2 received, 0% packet loss.
- UDP input smoke:
  - Down packet: `seq=313701`, `right=1`, `active=1`.
  - All-up packet: `seq=313702`, `right=0`, `active=0`.
- Continuous loop:
  - `loop-start 0` rc=0.
  - `loop-status`: active=1, continuous=1.

## Operator Command

Use the existing evdev keyboard bridge while the loop is active:

```sh
sudo python3 workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py \
  --input-backend evdev \
  --input-transport udp \
  --evdev-device /dev/input/event8 \
  --evdev-device /dev/input/event11 \
  --no-loop-start \
  --no-loop-stop
```

## Decision

V3137 readable HUD is adopted for demo testing. The readable text/spacing change preserved the V3135 fast path in warm-run timing and did not reintroduce shared-frame misses.
