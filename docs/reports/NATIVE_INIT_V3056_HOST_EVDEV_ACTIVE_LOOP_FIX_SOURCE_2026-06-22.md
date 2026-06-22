# Native Init V3056 Host Evdev Active Loop Fix Source

## Summary

- Cycle: `V3056`
- Track: active Video playback / DOOM host input path.
- Result: PASS
- Device flash: `no`
- Device action: bounded status/loop query only

## Problem

The V3055 evdev backend could exit immediately before printing `evdev input active`.
The live failure was not an evdev key mapping problem. The device already had the
continuous DOOM loop running, so the initial `video demo doom loop-start 0 ...`
returned `rc=-16` with `video.demo.doom.loop_start.active=1`. The host script
treated that as a startup failure and returned without entering the evdev read loop.

## Included Delta

- `DoomLoopKeeper.start()` now treats `loop-start rc=-16` plus an explicit active
  marker as success.
- The active markers accepted are:
  - `video.demo.doom.loop_start.active=1`
  - `video.demo.doom.loop_status.active=1`
- Generic busy/error responses without an active marker are still failures.
- TTY and evdev startup failures now print a short stderr reason instead of
  silently returning.
- Adds a regression test for active-loop `rc=-16` attach behavior.

## Live Evidence

- Bridge process was present and `a90ctl version` returned init
  `0.10.85 (v3053-doomgeneric-audio-corun)`.
- `video demo doom loop-status` returned:
  - `video.demo.doom.loop_status.active=1`
  - `video.demo.doom.loop_status.continuous=1`
  - `video.demo.doom.loop_status.frames=0`
- Re-running `video demo doom loop-start 0 --wad runtime-private --sha256 ...`
  returned:
  - `video.demo.doom.loop_start.active=1`
  - `video.demo.doom.loop_start.rc=-16`
  - cmdv1 end status `error`

## Validation

- `py_compile`:
  - `workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py`
  - `tests/test_host_doompad_evdev_v3055.py`
- Focused unittest:
  - `tests.test_host_doompad_evdev_v3055`
  - `tests.test_native_doomgeneric_visible_loop_source_v3033`
- Direct evdev-open live smoke from this non-interactive agent could not be run
  because `sudo -n` required interactive authentication. The operator-side command
  remains the live confirmation path.

## Operator Retest

With the loop already active, this command should now stay attached instead of
returning immediately:

```bash
sudo python3 workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py --input-backend evdev --evdev-device /dev/input/event8
```

If the selected event node does not emit normal key events, pass multiple keyboard
nodes:

```bash
sudo python3 workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py --input-backend evdev --evdev-device /dev/input/event8 --evdev-device /dev/input/event11
```

## Safety

- No boot image was built or flashed.
- No forbidden partition, raw flash path, OTG injection, uinput injection, sysfs
  write, GPIO, PMIC, regulator, or Wi-Fi action was used.
- Device interaction was limited to cmdv1 version/status/loop-status/loop-start
  diagnosis over the existing serial bridge.

## Next Unit

- Run ID: `V3057`
- Scope: remove the remaining device-side file polling IPC or start the larger
  UDP/NCM input channel, depending on whether the next priority is lower-risk
  incremental latency reduction or full serial/input transport separation.
