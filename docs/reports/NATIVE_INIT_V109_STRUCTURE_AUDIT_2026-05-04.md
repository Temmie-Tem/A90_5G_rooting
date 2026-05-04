# Native Init v109 Structure Audit 2

Date: `2026-05-04`
Build: `A90 Linux init 0.9.9 (v109)`
Marker: `0.9.9 v109 STRUCTURE AUDIT 2`
Baseline: `A90 Linux init 0.9.8 (v108)`

## Summary

v109 is a behavior-preserving structure audit baseline after the v106-v108 UI app split.
It copies the verified v108 include tree, bumps the build marker to v109, and records the remaining high-value cleanup boundaries before v110.

No user-facing runtime feature was added. The observed behavior remains the v108 native init UI/runtime baseline.

## Source Changes

- Added `stage3/linux_init/init_v109.c` and `stage3/linux_init/v109/*.inc.c` from v108.
- Updated `stage3/linux_init/a90_config.h` to `0.9.9` / `v109`.
- Added v109 ABOUT/changelog entries in `a90_app_about.c`, `a90_menu.c`, and `a90_menu.h`.
- Added the v109 changelog case to the v109 menu controller include tree.

## Structure Audit Findings

Largest remaining ownership surfaces after v108:

| Area | Evidence | Next action |
|---|---:|---|
| menu/app controller | `v109/40_menu_apps.inc.c` remains about 1.6k lines | v110 should target only small controller cleanup if low-risk boundaries are clear |
| shell dispatch | `v109/80_shell_dispatch.inc.c` remains about 1.1k lines | keep handler table in include tree unless visibility risk is reduced |
| storage/android/network shell handlers | `v109/70_storage_android_net.inc.c` remains about 1.0k lines | defer handler split until service/runtime behavior is stable |
| cutout calibration | `struct cutout_calibration_state` still appears in both app module and include-tree controller | candidate for later display/app controller cleanup, not v109 |
| auto HUD loop | `auto_hud_loop()` still owns active-app routing and menu rendering orchestration | v110 can isolate controller state, but should not change foreground/rescue behavior |

Benign internal state found in compiled modules:

- `console_fd` is private inside `a90_console.c`.
- `kms_state` is private inside `a90_kms.c`.
- `tcpctl_pid` is exposed only through status structs/API, not raw include-tree globals.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v109` | `c86c587fbb1eab9f615ef136b96812310b53fe4cb54ed94f851c29c2d0b81ee9` |
| `stage3/ramdisk_v109.cpio` | `263168d48eb98858142b238c91b8899e1b9dca9a34b4e7f7503dc0c5fd6aebf8` |
| `stage3/boot_linux_v109.img` | `71ee6051770944d4b48bf59bf1cefceda0331da0a413768a645d2aa1fdda7db9` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

Ramdisk contents:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.9 (v109)`
  - `A90v109`
  - `0.9.9 v109 STRUCTURE AUDIT 2`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `native_soak_validate.py`, `diag_collect.py` — PASS.
- v109 include tree stale marker check for `A90v108`, `_v108`, and `init_v108.c` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v109.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.9 (v109)" \
  --verify-protocol auto
```

Result:

- Native bridge v108 to TWRP recovery path succeeded after hiding active menu.
- Boot partition prefix SHA matched `stage3/boot_linux_v109.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.9 (v109)` — PASS.

Command regression:

| Command | Result |
|---|---|
| `version` | PASS |
| `status` | PASS |
| `bootstatus` | PASS |
| `selftest verbose` | PASS, `pass=11 warn=0 fail=0` |
| `inputlayout` | PASS |
| `displaytest safe` | PASS |
| `screenmenu` | PASS, immediate nonblocking return |
| `hide` | PASS |

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.9 (v109)" \
  --out tmp/soak/v109-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- Two manual regression invocations initially failed because the host command was passed as a single shell argument (`"selftest verbose"`) instead of argv tokens (`selftest verbose`). The soak runner and explicit tokenized calls passed; this was host invocation error, not native init regression.
- v109 confirms the next practical work item is v110 app/menu controller cleanup, not a larger shell or service split.
