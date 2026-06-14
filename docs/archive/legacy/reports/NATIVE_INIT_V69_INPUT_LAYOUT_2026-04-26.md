# Native Init v69 Input Layout Report

Date: `2026-04-26`

## Summary

`A90 Linux init 0.8.0 (v69)` adds a physical-button gesture layout for
VOL+/VOL-/POWER. The old single-click menu behavior remains, while double-click,
long-press, and combo gestures become explicit input actions.

- official version: `0.8.0`
- build tag: `v69`
- display name: `A90 Linux init 0.8.0 (v69)`
- creator: `made by temmie0214`

## Input Layout

| gesture | action |
|---|---|
| `VOLUP` click | previous item |
| `VOLDOWN` click | next item |
| `POWER` click | select |
| `VOLUP` double or long | page previous |
| `VOLDOWN` double or long | page next |
| `POWER` double | back |
| `POWER` long | reserved / ignored for safety |
| `VOLUP + VOLDOWN` | back |
| `VOLUP + POWER` | status shortcut |
| `VOLDOWN + POWER` | log shortcut |
| all buttons | hide / exit menu |

Timing:

- double click window: `350ms`
- long press threshold: `800ms`

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v69` | `bf9a5cc337d8ae0ca705c027053a0e81e3d4436926e331e089952b8916a280e9` |
| `stage3/ramdisk_v69.cpio` | `28fbb2f9ae618086bc704a73529d3cb3c4ebac050052f6dbd396d51503508ada` |
| `stage3/boot_linux_v69.img` | `1a333b5ee8e1c73722b9165f569f17a3257119690fccba3ce160b952792252d8` |

## Source Changes

- `stage3/linux_init/init_v69.c`
  - `INIT_VERSION "0.8.0"`
  - `INIT_BUILD "v69"`
  - `inputlayout` command added
  - `waitgesture [count]` command added
  - `inputlayout` allowed while auto menu is active
  - `screenmenu` and `blindmenu` now consume gesture actions
  - `POWER long` is intentionally not bound to reboot/poweroff/recovery

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v69.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.0 (v69)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local marker/SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init 0.8.0 (v69)`

## Runtime Validation

`inputlayout`:

```text
inputlayout: single click
  VOLUP    -> previous item
  VOLDOWN  -> next item
  POWER    -> select
inputlayout: double click / long press
  VOLUP    -> page previous (5 items)
  VOLDOWN  -> page next (5 items)
  POWER x2 -> back
  POWER long -> reserved/ignored for safety
inputlayout: combos
  VOLUP+VOLDOWN -> back
  VOLUP+POWER   -> status shortcut
  VOLDOWN+POWER -> log shortcut
  all buttons   -> hide/exit menu
timing: double=350ms long=800ms
```

`version`:

```text
A90 Linux init 0.8.0 (v69)
made by temmie0214
version: 0.8.0 build=v69
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

`timeline`:

```text
00     1451ms init-start         rc=0 errno=0 A90 Linux init 0.8.0 (v69)
11     1619ms display-splash     rc=0 errno=0 boot splash applied
13     3884ms autohud            rc=0 errno=0 started refresh=2
14     3884ms shell              rc=0 errno=0 interactive shell ready
```

## Manual Follow-up

- `waitgesture 5`로 실제 button gesture 분류를 하나씩 육안/serial로 확인한다.
- 자동 HUD loop에도 gesture state machine을 붙일지 별도 검토한다.
