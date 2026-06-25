# Native Init V3136 DOOMGENERIC Fast Demo HUD Live Validation

## Summary

- Flashed: `workspace/private/inputs/boot_images/boot_linux_v3135_doomgeneric_demo_hud_fast.img`
- Boot SHA256: `73a63d7946a9a53a6ab213eac663541c3a2f6266a1427488747a28895d8a3b5f`
- Init: `A90 Linux init 0.10.121 (v3135-doomgeneric-demo-hud-fast)`
- Result: PASS
- Device state after validation: V3135 booted, health checked, and continuous DOOM loop left running.

## Safety Gates

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py --from-native`
- Partition scope: boot image only through the checked helper.
- Rollback images present and verified:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`
  - `boot_linux_v2237_supplicant_terminate_poll.img`
  - `boot_linux_v48.img`
- Recovery/TWRP material: present per existing recovery guide and previous live report.
- Post-flash health: `selftest: pass=12 warn=1 fail=0`.

## Live Validation

- `version`: matched `A90 Linux init 0.10.121 (v3135-doomgeneric-demo-hud-fast)`.
- `status`: boot OK, SD runtime mounted writable, WAD runtime path present.
- WAD verify: SHA256 matched `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`, magic `IWAD`, bytes `4196020`.
- Dashboard markers:
  - `video.demo.doom.dashboard.profile=demo-hud-fast`
  - `video.demo.doom.dashboard.metrics_interval_frames=1800`
  - `video.demo.doom.dashboard.status_interval_frames=300`
  - `video.demo.doom.dashboard.clear_path=targeted-demo-hud-regions`
  - `video.demo.doom.loop.foreground_frame_log=0`
- USB-NCM host route and ping were verified; interface identifiers and IPs are intentionally omitted.
- UDP input smoke:
  - Sent `right` down, helper state file showed `seq=313503`, `right=1`, `active=1`.
  - Sent all-up, helper state file showed `seq=313504`, `active=0`.

## Timing Comparison

V3133 full HUD 240-frame reference:

- `shared_missed_frames=0`
- `timing.draw.avg_us=31041`
- `timing.draw.max_us=629070`
- `timing.total.avg_us=41923`
- `timing.total.max_us=631604`
- `flip_delta_max_us=632484`

V3135 fast HUD first 240-frame run:

- `shared_missed_frames=0`
- `timing.draw.avg_us=3144`
- `timing.draw.max_us=240054`
- `timing.total.avg_us=8454`
- `timing.total.max_us=242505`
- `flip_delta_max_us=33297`

V3135 fast HUD second 240-frame run, after cache warmup:

- `shared_missed_frames=0`
- `timing.draw.avg_us=2151`
- `timing.draw.max_us=2611`
- `timing.total.avg_us=7504`
- `timing.total.max_us=17519`
- `flip_delta_max_us=33304`

## Conclusion

The periodic visible hitch was confirmed as the V3133 full native HUD path, not DOOM frame generation or input. V3135 removes the repeatable full-HUD/sysfs/status stall from the normal frame loop. The only large V3135 first-run spike came from initial cache fill; a second run stayed within the 28ms frame budget with no shared-frame misses.

## Operator Notes

- Current playable command is already running: `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Host input command remains:
  `python3 workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py --input-backend evdev --input-transport udp --evdev-device /dev/input/event8 --evdev-device /dev/input/event11 --no-loop-start --no-loop-stop`
