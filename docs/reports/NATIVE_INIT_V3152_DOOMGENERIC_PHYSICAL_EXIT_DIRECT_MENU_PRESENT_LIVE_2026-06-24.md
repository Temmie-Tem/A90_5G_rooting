# Native Init V3152 DOOMGENERIC Physical Exit Direct Menu Present Live

## Summary

- Cycle: `V3152`
- Resident after flash: `A90 Linux init 0.10.134 (v3152-doomgeneric-physical-exit-direct-menu-present)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3152_doomgeneric_physical_exit_direct_menu_present.img`
- Boot SHA256: `8ca9370514591728c7ef8006aa4e321192c0dd0f2803610551edf7bbcba370ab`
- Result: PARTIAL PASS

## Why

V3151 proved that the physical-button exit handler ran, but it tried to start/own autohud from the DOOM background child. That left `menu active` true while PID1 reported `autohud: stopped`, producing the black-screen-plus-busy state reported by the operator.

V3152 changes the exit path to:

- keep physical-button DOOM loop exit,
- clear the DOOM frame,
- stop DOOM SFX audio,
- directly present one native menu frame,
- request menu show only for an already-running autohud,
- avoid starting a new HUD service from the DOOM child.

## Flash Gate

- Local candidate SHA256 matched expected: `8ca9370514591728c7ef8006aa4e321192c0dd0f2803610551edf7bbcba370ab`.
- Rollback baseline present and SHA matched:
  - `boot_linux_v2321_usb_clean_identity_rodata.img`
  - SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper fallback present and SHA matched:
  - `boot_linux_v2237_supplicant_terminate_poll.img`
  - SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Final fallback present: `boot_linux_v48.img`.
- TWRP recovery material present:
  - `workspace/private/inputs/firmware/twrp/recovery.img`
  - `workspace/private/inputs/firmware/twrp/twrp_recovery.tar`
- Flash path: checked helper only, `native_init_flash.py --from-native`.
- Remote transfer SHA256 matched.
- Boot partition readback SHA256 matched.
- Recovery/TWRP path was exercised by the helper before boot write.

## Post-Flash Health

- Helper post-flash verify: `version/status rc=0 status=ok`.
- `version`: `0.10.134 build=v3152-doomgeneric-physical-exit-direct-menu-present`.
- `selftest verbose`: `pass=12 warn=1 fail=0`.
- Final status after cleanup:
  - `selftest: pass=12 warn=1 fail=0`
  - `autohud: running`
  - `transport.serial=ready`
  - `transport.ncm=ready`
  - `transport.tcpctl=ready`

## DOOM Validation

- Runtime WAD: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Runtime WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- DOOM loop start: PASS
  - Engine: `doomgeneric-private-link-v3152-physical-exit-direct-menu-present`
  - Helper: `/bin/a90_doomgeneric_private_engine_v3152`
  - Audio worker started with V3152 SFX stream.
- Physical-button capture attempt 1:
  - Command: `doominputmux event3,event0 8 60000`
  - Result: timeout, `captured=0/8`
- Physical-button capture attempt 2:
  - Command: `doominputmux event3,event0 8 75000`
  - Result: timeout, `captured=0/8`
- Because no physical button events arrived during the capture windows, the V3152 direct-menu-present exit path was not live-triggered in this run.
- Cleanup:
  - `video demo doom loop-stop`: PASS
  - audio stop: PASS
  - `screenmenu`: PASS

## Residual

- Live flash and health are complete.
- The black-screen fix is present in the resident image and marker-verified in the boot artifact.
- Physical-button live validation remains a human checkpoint: rerun DOOM loop, start `doominputmux event3,event0`, then press POWER/VOLUP/VOLDOWN while the capture is active.
- One post-flash selftest attempt hit the known host-side serial framing issue (`A90P1 END marker not found`) with partial PASS output. Restarting the host bridge recovered it; V3152 selftest then completed with `fail=0`.

## Follow-Up Measurement

- Measurement method: host-side timestamped serial-line capture around `doominputmux event3,event0 8 90000`.
- Resident: `A90 Linux init 0.10.134 (v3152-doomgeneric-physical-exit-direct-menu-present)`.
- First key event: `KEY_VOLUMEDOWN value=1`.
- Observed deltas from first key-down:
  - Physical button clear reason: `+109.191ms`
  - Audio stop requested: `+109.223ms`
  - Direct menu present marker: `+2774.837ms`
  - Return-menu active marker: `+2774.857ms`
- Exit completed and loop status afterward was inactive:
  - `video.demo.doom.loop_status.active=0`
  - `pid=-1`
- Final health after measurement:
  - `selftest: pass=12 warn=1 fail=0`
  - `transport.serial=ready`
  - `transport.ncm=ready`
- Interpretation: physical button detection and clear are fast enough. The visible return-to-menu delay is dominated by the synchronous `audio.stop` route reset running before `video_demo_doom_restore_menu_after_exit()`. The next UX fix should present the menu before audio shutdown, or move DOOM audio stop/reset into an asynchronous cleanup path.
- Cleanup: `screenmenu` was run after measurement to restore a live autohud menu.
