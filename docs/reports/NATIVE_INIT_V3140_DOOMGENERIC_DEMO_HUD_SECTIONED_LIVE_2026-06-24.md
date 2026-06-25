# Native Init V3140 DOOMGENERIC Sectioned Demo HUD Live Validation

## Summary

- Cycle: `V3140`
- Live artifact: `workspace/private/inputs/boot_images/boot_linux_v3139_doomgeneric_demo_hud_sectioned.img`
- Boot SHA256: `af80670a030d1b1ec53cfff85cef9bc3cd8543f00615a177cae8028ab71f1cc7`
- Init after flash: `A90 Linux init 0.10.123 (v3139-doomgeneric-demo-hud-sectioned)`
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
- Pre-flash health: V3137 booted, `status` OK, `selftest` fail=0.
- No Wi-Fi connect, DHCP, or Wi-Fi ping was run.

## Flash

- Local image marker matched expected V3139 version string.
- Local image SHA256 matched expected V3139 boot SHA.
- Recovery ADB became ready.
- Remote pushed image SHA256 matched local SHA.
- Boot partition readback prefix SHA256 matched local SHA.
- Native-init post-reboot verification passed through the flash helper.

## Post-Flash Health

- `version`: `0.10.123 build=v3139-doomgeneric-demo-hud-sectioned`.
- `status`: boot OK, SD runtime backend mounted writable, USB-local transport ready.
- `selftest`: pass=12 warn=1 fail=0.
- Note: two immediate post-flash serial commands were accidentally started in parallel; one saw a busy lock and one saw a fragmented response. The bridge recovered without reboot, and sequential `version`/`selftest` passed.

## Sectioned HUD Contract

- Runtime WAD path: SD runtime path, not bundled in boot.
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- WAD verify: present=1, regular=1, magic=IWAD, SHA256 match=1, ok=1.
- Engine: `doomgeneric-private-link-v3139-demo-hud-sectioned`.
- Sectioned HUD markers:
  - `video.demo.doom.dashboard.layout=top-frame-sectioned-hw-doom-input-footer`
  - `video.demo.doom.dashboard.sectioned_info=1`
  - `video.demo.doom.dashboard.text_scale=section3-main3-small2`
  - `a90.doomgeneric.v3139.demo_hud=sectioned-hw-doom-input`
  - `a90.doomgeneric.v3139.scale=producer-960x600-1to1-demo-hud-sectioned`
- Visible layout intent:
  - `HW INFO`: CPU/GPU as primary scale-3 line; memory, load, battery, and power as secondary line.
  - `DOOM INFO`: FPS/frame/poll as primary scale-3 line; WAD/shared/helper state as secondary line.
  - `KEY INPUT`: USB-NCM UDP EVDEV host path, key state, buttons, and short key log.

## Loop Timing

- First 240-frame bounded loop:
  - rc=0, frames_presented=240, shared_missed_frames=0.
  - draw avg/max: `4266/61217 us`.
  - total avg/max: `7769/63705 us`.
- Warm 240-frame bounded loop:
  - rc=0, frames_presented=240, shared_missed_frames=0.
  - draw avg/max: `4006/4430 us`.
  - total avg/max: `7437/17432 us`.
  - flip delta avg/max: `19885/33250 us`.

## Host Input Path

- USB-NCM host profile was rebound to the post-reboot NCM interface through NetworkManager.
- Host route to the USB-NCM device endpoint used the USB-NCM interface after rebinding.
- USB-NCM ping: 2/2 received, 0% packet loss.
- UDP input smoke:
  - Down packet: `seq=313901`, `right=1`, `active=1`.
  - All-up packet: `seq=313902`, `right=0`, `active=0`.
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

V3139 sectioned HUD is adopted for demo testing. The UI hierarchy is clearer than V3137 while keeping warm-run timing comfortably under the frame budget and preserving zero shared-frame misses.
