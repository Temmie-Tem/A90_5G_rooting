# Native Init V3134 DOOMGENERIC Demo HUD Live Validation

## Summary

- Cycle: `V3134`
- Candidate flashed: `v3133-doomgeneric-demo-hud`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3133_doomgeneric_demo_hud.img`
- Boot SHA256: `63630b80e18d27b82d34693791371c2d89fd757f384704a2042b57f92340744e`
- Result: PASS.

## Flash Gate

- Rollback baseline present: `boot_linux_v2321_usb_clean_identity_rodata.img`
  SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper fallback present: `boot_linux_v2237_supplicant_terminate_poll.img`
  SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Final fallback present: `boot_linux_v48.img`
  SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- TWRP recovery material present under `workspace/private/inputs/firmware/twrp/`.
- Current resident before flash: `A90 Linux init 0.10.119 (v3131-doomgeneric-monotonic-input-thread)`.
- Pre-flash health: `selftest pass=12 warn=1 fail=0`.

## Flash Result

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Mode: `--from-native`
- Local image marker check: PASS.
- Recovery ADB: PASS.
- Remote pushed SHA256: matched candidate.
- Boot write: PASS.
- Boot readback prefix SHA256: matched candidate.
- Post-flash version/status check: PASS.
- New resident: `A90 Linux init 0.10.120 (v3133-doomgeneric-demo-hud)`.
- Post-flash selftest: `pass=12 warn=1 fail=0`.

## DOOM HUD Validation

- First DOOM verify attempt was blocked by active auto menu; `hide` cleared it.
- WAD verify: PASS.
  - Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
  - SHA256 matched `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Runtime dashboard markers:
  - `video.demo.doom.dashboard.native=1`
  - `video.demo.doom.dashboard.layout=top-frame-metrics-logs-input`
  - `video.demo.doom.dashboard.metrics_interval_frames=30`
  - `video.demo.doom.dashboard.metrics_pacing=cached-frame-interval`
  - `video.demo.doom.dashboard.large_frame=0`
  - `video.demo.doom.dashboard.frame_mode=standard-dashboard`
  - `video.demo.doom.dashboard.frame_scale=1:1`
- Continuous DOOM loop started:
  - `video.demo.doom.loop_start.active=1`
  - `video.demo.doom.loop_start.pid=658`
  - `video.demo.doom.loop_start.continuous=1`
- Serial fallback input smoke:
  - `doompad key right 1`: state updated, input-state file updated, UNIX dgram sent.
  - `doompad key right 0`: state updated, input-state file updated, UNIX dgram sent.

## Host UDP/NCM Validation

- Initial host route was wrong after USB re-enumeration:
  `192.168.7.2 via 192.168.0.1 dev enx0000000005e1`.
- Existing NetworkManager profile was present:
  `a90-v725-ncm-bench`, manual IPv4 `192.168.7.1/24`.
- The profile was pinned to an old interface name, so it was updated to current USB/NCM
  interface `enx72651370d818` and activated without sudo:
  `nmcli connection modify a90-v725-ncm-bench connection.interface-name enx72651370d818`
  then `nmcli connection up a90-v725-ncm-bench`.
- Post-activation route:
  `192.168.7.2 dev enx72651370d818 src 192.168.7.1`.
- Ping: `2 transmitted, 2 received, 0% packet loss`.
- UDP input smoke:
  - Sent packet `seq=1003 mask=0x08`; device input-state showed `right=1 active=1`.
  - Sent packet `seq=1004 mask=0x00`; device input-state showed `right=0 active=0`.

## Safety

- Only the boot partition was flashed.
- Flash was performed only through `native_init_flash.py`.
- No `/efs`, `/sec_efs`, modem, RPMB, keymaster, vbmeta, bootloader, Wi-Fi connect/dhcp/ping, PMIC, regulator, GPIO, or GDSC path was touched.
- The DOOM loop was intentionally left running for operator visual validation.
