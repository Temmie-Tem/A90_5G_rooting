# Native Init v108 UI App Input Monitor Report

Date: `2026-05-04`
Version: `A90 Linux init 0.9.8 (v108)` / `0.9.8 v108 APP INPUTMON API`
Baseline: `A90 Linux init 0.9.7 (v107)`

## Summary

- v108 completes the first UI/App Architecture split batch after v106 ABOUT and v107 displaytest extraction.
- Added `a90_app_inputmon.c/h` and moved input monitor state formatting, raw/gesture trace rendering, and input layout screen drawing out of `v108/40_menu_apps.inc.c`.
- Kept low-level `a90_input.c/h`, shell command routing, menu control, storage/runtime/network policy, and existing physical-button gesture semantics unchanged.
- Real-device flash, input layout display, shell/HUD/menu regression, and quick soak passed.

## Code Changes

- Added `stage3/linux_init/init_v108.c` and `stage3/linux_init/v108/*.inc.c` copied from v107.
- Updated `stage3/linux_init/a90_config.h` to `0.9.8` / `v108`.
- Added `stage3/linux_init/a90_app_inputmon.c` and `stage3/linux_init/a90_app_inputmon.h`.
- Moved input monitor app state model, event formatting, gesture formatting, raw entry ring, framebuffer renderer, and input layout screen renderer behind `a90_app_inputmon_*` APIs.
- Kept `cmd_inputmonitor`, `waitkey`, `waitgesture`, and autohud/menu controller ownership in the v108 include tree.
- Updated ABOUT/changelog menu data for the v108 entry.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v108` | `fc2c06e0c0e0fc4998526fe957612d79e4c7f77b3b22db50e53882e87a98b9fb` |
| `stage3/ramdisk_v108.cpio` | `a7654b847d38278bece3f8568e4c691acc55e9679cd1b02b806516f7b4f4fbba` |
| `stage3/boot_linux_v108.img` | `fb30a357d5fefb0f2c91cda1200cda65e29cd02b1805f201edc31aef19c7a885` |

## Static Validation

- Static ARM64 build with `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS.
- Marker strings in init and boot image — PASS:
  - `A90 Linux init 0.9.8 (v108)`
  - `A90v108`
  - `0.9.8 v108 APP INPUTMON API`
- `git diff --check` — PASS.
- Host Python `py_compile` — PASS.
- v108 include tree no longer owns the old input monitor renderer internals (`INPUT_MONITOR_ROWS`, raw-entry renderer helpers, value/action color helpers) — PASS.
- Ramdisk includes `/init`, `/bin/a90sleep`, `/bin/a90_cpustress`, and `/bin/a90_rshell` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v108.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.8 (v108)" \
  --verify-protocol auto
```

Result: PASS.

- Local image marker and SHA check — PASS.
- Recovery ADB push and remote SHA check — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v108.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

Manual/host command regression:

- `version`, `status`, `bootstatus`, `selftest verbose` — PASS.
- `inputlayout` — PASS, console layout printed and framebuffer layout screen presented.
- `waitkey 1` + same-connection `q` cancel — PASS, framed result returned `rc=-125`.
- `waitgesture 1` + same-connection `q` cancel — PASS, framed result returned `rc=-125`.
- `inputmonitor 0` + same-connection `q` cancel — PASS, framebuffer monitor opened and framed cancel result returned `rc=-125`.
- `statushud`, `autohud 2`, `screenmenu`, `hide`, `storage` — PASS.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.8 (v108)" \
  --out tmp/soak/v108-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- `waitkey`, `waitgesture`, and live `inputmonitor` physical button events still require optional manual spot checks. The automated v108 validation covered command startup, framebuffer presentation, same-connection q cancel, nonblocking layout rendering, and the existing autohud/menu command path.
- v108 does not change Wi-Fi, storage, netservice, runtime, rshell, CPU stress, or low-level input decoder policy.
- Next candidate: v109 planning after the first UI/App Architecture split batch, likely focused on remaining UI app ownership or controller cleanup.
