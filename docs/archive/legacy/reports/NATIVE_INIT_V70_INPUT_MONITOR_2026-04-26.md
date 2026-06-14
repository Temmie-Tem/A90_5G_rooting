# Native Init v70 Input Monitor Report (2026-04-26)

## Summary

- Version: `A90 Linux init 0.8.1 (v70)`
- Source: `stage3/linux_init/init_v70.c`
- Goal: make physical-button debugging visible by showing raw key events and decoded gesture/action results together.
- Status: built, flashed, and verified through the serial bridge.

## What Changed

- Added `TOOLS / INPUT MONITOR` screen app.
- Added `inputmonitor [events]` shell command.
- Added raw event trace fields:
  - input node source: `event0` or `event3`
  - key name/code
  - `DOWN`, `UP`, or `REPEAT`
  - gap from previous raw event
  - hold duration on key release/repeat
- Added decoded gesture trace:
  - gesture name
  - button mask
  - click count
  - gesture duration
  - gap from previous gesture
  - menu action id
- Improved on-device readability:
  - raw events draw as two-line cards
  - `DOWN` is green, `UP` is yellow, `REPEAT` is cyan, unknown values are red
  - gesture title/detail are split across two lines
  - latest decoded gesture gets a large top panel: `SINGLE CLICK`, `DOUBLE CLICK`, `LONG HOLD`, or `COMBO INPUT`
  - the top panel separates buttons, mapped action, click count, duration, and gesture gap
- Refactored `waitgesture` and input monitor to share the same decoder helper.

## Input Monitor Usage

Serial/bridge command:

```bash
printf 'hide\ninputmonitor 12\n' | nc -w 120 127.0.0.1 54321
```

Interactive long-running mode:

```bash
printf 'hide\ninputmonitor 0\n' | nc -w 300 127.0.0.1 54321
```

- `inputmonitor 12`: records 12 raw key events, then exits.
- `inputmonitor 0`: runs until all three buttons are pressed together, `q`, or Ctrl-C.
- Three-button exit is immediate when all buttons are down, not delayed until release.
- The on-device app is available from `APPS > TOOLS > INPUT MONITOR`.
- In the on-device app, all three buttons together exits back to the menu.

## Build Artifacts

- `stage3/linux_init/init_v70`
  - SHA256 `d7082127bbfeafd0508cf7a3b90079dc0f3f1b8b8238140cceb5dfe9063d7d12`
- `stage3/ramdisk_v70.cpio`
  - SHA256 `98ae190435469f2817d6d04fce076e643f2cb5f9e1fbafd69d9c865e1d1907b3`
- `stage3/boot_linux_v70.img`
  - SHA256 `5e3657ba14705bdee9cc772cb8916601bfe1a92f31122475c1115896e2a42cb1`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v70.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.1 (v70)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

- local marker check: PASS
- local image SHA256: `5e3657ba14705bdee9cc772cb8916601bfe1a92f31122475c1115896e2a42cb1`
- TWRP ADB push: PASS
- remote `/tmp/native_init_boot.img` SHA256: PASS
- boot partition prefix SHA256: PASS
- reboot to native init: PASS
- bridge `version`: `A90 Linux init 0.8.1 (v70)` PASS

## Runtime Validation

Bridge command:

```bash
printf 'hide\nversion\nstatus\ninputlayout\nhelp\n' | nc -w 10 127.0.0.1 54321
```

Observed:

- `version` → `A90 Linux init 0.8.1 (v70)`
- `status` → `boot: BOOT OK shell 3S`
- `status` → `autohud: running`
- `inputlayout` → v69 single/double/long/combo mapping still present
- `help` → `inputmonitor [events]` listed
- `inputmonitor 0` → opens without framebuffer serial spam, `q` cancels with `-ECANCELED`
- `autohud 2` → HUD restored after monitor cancellation
- three-button combo → `VOLUP+VOLDOWN+POWER` / `HIDE/EXIT` observed, then HUD restore policy changed to always restart HUD

## Next Checks

- Run `inputmonitor 0` and press:
  - VOLUP click
  - VOLDOWN click
  - POWER click
  - VOLUP/VOLDOWN double-click
  - VOLUP/VOLDOWN long-press
  - VOLUP+VOLDOWN combo
- Compare raw gap/hold values against decoded gesture/action.
- Decide whether the auto HUD menu loop should move from raw press handling to the v70 decoder helper.
