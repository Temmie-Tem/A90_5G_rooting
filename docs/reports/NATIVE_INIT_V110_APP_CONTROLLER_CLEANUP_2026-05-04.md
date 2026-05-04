# Native Init v110 App Controller Cleanup

Date: `2026-05-04`
Build: `A90 Linux init 0.9.10 (v110)`
Marker: `0.9.10 v110 APP CONTROLLER CLEANUP`
Baseline: `A90 Linux init 0.9.9 (v109)`

## Summary

v110 is a behavior-preserving menu/app controller cleanup release.
It moves the auto-menu state/request IPC helpers out of the include tree and into `a90_controller.c/h`, while preserving the v109 UI/menu/runtime behavior.

No new user-facing feature was added.

## Source Changes

- Added `stage3/linux_init/init_v110.c` and `stage3/linux_init/v110/*.inc.c` from v109.
- Updated `stage3/linux_init/a90_config.h` to `0.9.10` / `v110`.
- Extended `a90_controller.c/h` with menu IPC APIs:
  - `a90_controller_clear_menu_ipc()`
  - `a90_controller_clear_menu_request()`
  - `a90_controller_set_menu_active()`
  - `a90_controller_set_menu_state()`
  - `a90_controller_menu_is_active()`
  - `a90_controller_menu_power_is_active()`
  - `a90_controller_request_menu_show()`
  - `a90_controller_request_menu_hide()`
  - `a90_controller_consume_menu_request()`
- Removed the local auto-menu IPC implementation from `v110/10_core_log_console.inc.c`.
- Updated v110 include callsites to use `a90_controller_*` APIs.
- Added v110 ABOUT/changelog entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v110` | `df5ab53f2696f97772541e0afdb3e0b0bc1866a87e83357d78de6ae272d02a12` |
| `stage3/ramdisk_v110.cpio` | `19c20660c81deb25b349ef884c2ebbfca93966f8a767553f83648c61123f3124` |
| `stage3/boot_linux_v110.img` | `ebf69421c19f20f681ef7c074c7112e7307281ce6009bd7433be55ff5e86d055` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

Ramdisk contents remain:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.10 (v110)`
  - `A90v110`
  - `0.9.10 v110 APP CONTROLLER CLEANUP`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `native_soak_validate.py`, `diag_collect.py` — PASS.
- v110 include tree stale marker check for `A90v109`, `_v109`, and `init_v109.c` — PASS.
- v110 include tree no longer defines local `clear_auto_menu_ipc`, `set_auto_menu_active`, `auto_menu_is_active`, `request_auto_menu_*`, or `consume_auto_menu_request` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v110.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.10 (v110)" \
  --verify-protocol auto
```

Result:

- Native bridge v109 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v110.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.10 (v110)` — PASS.

Controller regression:

| Check | Result |
|---|---|
| `screenmenu` | PASS, immediate nonblocking return |
| `status` while menu visible | PASS |
| `recovery` while menu visible | PASS, busy gate returned `rc=-16 status=busy` |
| `hide` | PASS |
| `displaytest safe` | PASS |
| `autohud 2` | PASS |

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.10 (v110)" \
  --out tmp/soak/v110-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- The cleanup reduces include-tree controller responsibility without moving app renderers or command handlers.
- The next practical step is v111 extended soak RC to validate v109-v110 before service/runtime expansion.
