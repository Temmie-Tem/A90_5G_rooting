# Native Init V3154 DOOMGENERIC Physical Exit HUD PID Adopt Live

## Summary

- Cycle: `V3154`
- Build: `v3154-doomgeneric-physical-exit-hud-pid-adopt`
- Init version: `0.10.136`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3154_doomgeneric_physical_exit_hud_pid_adopt.img`
- Boot SHA256: `d852e0f4484a98e6db263eeed044ca9b7ca6e4ba67fa2711d7e02152c33de1df`
- Result: PASS for flash, boot health, HUD pidfile lifecycle, and cleanup consistency.

## Flash And Health

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Flash scope: boot partition only.
- Local/remote/readback SHA256 all matched `d852e0f4484a98e6db263eeed044ca9b7ca6e4ba67fa2711d7e02152c33de1df`.
- Post-flash `version`: `A90 Linux init 0.10.136 (v3154-doomgeneric-physical-exit-hud-pid-adopt)`.
- Post-flash `status`: `BOOT OK`, `selftest: pass=12 warn=1 fail=0`, SD runtime mounted read/write, serial/NCM/tcpctl ready.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.

## DOOM Exit And HUD State

- Started DOOM with runtime WAD SHA256 `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`.
- Loop start: `video.demo.doom.loop_start.pid=657`, audio worker `pid=658`, `audio.start.rc=0`.
- No physical-button event was captured during the V3154 manual window:
  - `tail` window: no `return_menu` output.
  - `doominputmux event3,event0 4 30000`: `captured=0/4`, `rc=-110`.
- The DOOM loop was stopped explicitly to avoid leaving it running:
  - `video.demo.doom.loop_stop.pid=657`
  - `video.demo.doom.loop_stop.rc=0`
  - `video.demo.doom.audio.stop.rc=0`
  - `video.demo.doom.clear.reason=loop-stop`

## PID Adopt Validation

- Before V3154, V3153 physical-exit logs showed a child-started HUD could be alive while PID1 `status` still reported `autohud: stopped`.
- V3154 adds `/tmp/a90-autohud.pid` for HUD PID persistence/adoption.
- `screenmenu` after cleanup created pidfile:
  - `cat /tmp/a90-autohud.pid` -> `665`
  - `status` -> `autohud: running`
- `stophud` cleaned the same lifecycle:
  - `stophud` -> `autohud: stopped`
  - `cat /tmp/a90-autohud.pid` -> `ENOENT`
  - `status` -> `autohud: stopped`
- Final state restored with `screenmenu`; final `status` reports `autohud: running`.

## Notes

- One normal-mode `selftest verbose` attempt had serial character loss (`cmdv1 selft verb`) and no END marker. Retrying with `--input-mode slow` passed.
- V3154 physical-button exit needs one more manual press window to prove the full path on this exact image; V3153 already proved the physical exit ordering fix and V3154 proved the new PID lifecycle path.
