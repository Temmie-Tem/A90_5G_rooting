# Native Init V3048 DOOMGENERIC Batch Input Live

## Summary

- Cycle: `V3048`
- Track: active Video playback / DOOM capstone.
- Decision: `v3048-doomgeneric-batch-input-live-pass`
- Result: PASS
- Device flash: `yes`
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3047_doomgeneric_batch_input.img`
- Boot SHA256: `93ad90ddeb83a5100ed5a690cb059a5476ce5f47f049af661b38bb7c9dc86b12`
- Installed init: `A90 Linux init 0.10.82 (v3047-doomgeneric-batch-input)`

## Flash Gate

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img`: present, SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img`: present, SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img`: present, SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
- TWRP/recovery material: present under `workspace/private/inputs/firmware/twrp/`.
- Pre-flash resident: `A90 Linux init 0.10.81 (v3045-doomgeneric-continuous-loop)`.
- Pre-flash health: `status rc=0`, `selftest fail=0`.

## Flash

- Tool: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Mode: `--from-native --expect-android-magic --expect-sha256 93ad90ddeb83a5100ed5a690cb059a5476ce5f47f049af661b38bb7c9dc86b12 --expect-version "A90 Linux init 0.10.82 (v3047-doomgeneric-batch-input)"`.
- Local image magic check: PASS.
- Remote push SHA256: PASS.
- Boot partition readback SHA256: PASS.
- Post-reboot `version` and `status`: PASS.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.

## Batch Input Validation

- `doompad reset`: PASS, input-state path `/tmp/a90-doomgeneric-v3047-input.state`, update rc `0`.
- `doompad state 1 0x11`: PASS.
  - Reported `doompad.state_batch seq=1 mask=0x11 active=1`.
  - Status reflected `forward=1 fire=1 active=1`.
- `doompad status`: PASS, reported `doompad.batch=state-mask-v3047` and `doompad.mask=0x11`.
- `doompad state 2 0x00`: PASS.
  - Reported `doompad.state_batch seq=2 mask=0x00 active=0`.
  - Status reflected `active=0`.

## DOOM Loop Validation

- Command: `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`.
- Result: PASS, `video.demo.doom.loop_start.active=1`.
- Continuous marker: `video.demo.doom.loop_start.continuous=1`.
- Loop status after host input sampling and an additional 10 second wait: `active=1 continuous=1 frames=0`.
- Cleanup: `video demo doom loop-stop` returned `rc=0`; `doompad reset` returned `rc=0`.
- Final health after cleanup: `selftest pass=12 warn=1 fail=0`.

## Host Input Validation

- Host keyboard session emitted only batch state commands:
  - `doompad state 1 0x01`
  - `doompad state 2 0x11`
  - `doompad state 3 0x00`
  - `doompad state 4 0x00`
- `session_all_state=True`.
- 20 live `doompad state` command samples all returned `rc=0 status=ok`.
- Latency sample:
  - min: `5.93ms`
  - p50: `6.24ms`
  - p95: `7.18ms`
  - max: `7.20ms`
- Final sampled device state: `doompad.seq=119`, `doompad.mask=0x00`, `active=0`.

## Notes

- One immediate post-flash `selftest verbose` request returned a partial serial stream without an `A90P1 END` marker. A subsequent `version` command re-aligned cmdv1 output and the repeated selftest passed with `fail=0`; this was recorded as bridge/protocol desynchronization, not resident health failure.
- After loop cleanup, `video demo doom loop-status` reported `active=0`; the still-visible DOOM menu was the last presented KMS framebuffer, not a still-running DOOM loop.
- The framebuffer was cleared manually with `kmssolid black`, which returned `rc=0`.
- DOOM audio was confirmed inactive by contract: `video.demo.sound.active=disabled-nosound-nomusic`, and the private helper argv includes `-nosound -nomusic`.
- Native audio output itself was checked separately: `audio chime --duration-ms 300 --amplitude-milli 80 --execute` started worker pid `665`, and `audio play-status` reported `bytes_done=57600`, `done=1`, `rc=0`.
- No OTG keyboard, evdev injection, uinput, host USB HID injection, Wi-Fi connect, DHCP, ping, sysfs write, GPIO, regulator, PMIC, GDSC, modem, EFS, or forbidden partition path was used.
- V3047 remained installed because boot, health, DOOM loop, and batch input validation passed.

## Conclusion

- The priority 1 optimization is live: host input can now send a complete key mask with one `doompad state <seq> <mask>` transaction instead of one serial transaction per key edge.
- The priority 2 tuning is live: host defaults are now `hold-ms=110` and `poll-ms=10`.
- The measured command path no longer shows the previous 0.5s-class host-side delay during focused state-command sampling; remaining perceived delay should next be investigated in terminal key-read cadence, dashboard rendering/poll interaction under real curses input, and the file-to-helper frame consumption path.
