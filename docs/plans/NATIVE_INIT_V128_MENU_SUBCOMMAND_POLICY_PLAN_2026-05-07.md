# v128 Plan: Menu Subcommand Policy API

Date: 2026-05-07
Baseline: `A90 Linux init 0.9.27 (v127)`
Target: `A90 Linux init 0.9.28 (v128)` / `0.9.28 v128 MENU SUBCOMMAND POLICY`

## Summary

v127 closed F023 by making non-power menu-active command handling
deny-by-default. v128 is not a security closure requirement; it is a controlled
UX relaxation for safe read-only subcommands while preserving the v127 security
boundary.

The goal is to keep side-effect commands blocked while the menu is visible, but
allow selected status/query subcommands that are useful during live screen/menu
debugging.

## Design Rule

Keep v127 as the default:

```text
menu visible + non-power page
  -> deny by default
  -> allow only explicit read-only command/subcommand pairs
```

No command should be allowed because its top-level command name is harmless. The
policy must look at the operation that will run.

## Candidate Safe Operations

These are candidates, not automatic approvals. Each one must stay read-only.

| command | allowed form | reason |
|---|---|---|
| `selftest` | `selftest`, `selftest status`, `selftest verbose` | Reads last boot/manual result; `selftest run` should remain blocked because it re-runs probes. |
| `pid1guard` | `pid1guard`, `pid1guard status`, `pid1guard verbose` | Reads guard state; `pid1guard run` should remain blocked. |
| `helpers` | `helpers`, `helpers status`, `helpers verbose`, `helpers manifest`, `helpers plan`, `helpers path <name>` | Inventory/read-only helper information. `helpers verify` should remain blocked if it performs filesystem/hash work beyond simple display. |
| `runtime` | `runtime` | Already allowed in v127. Keep as top-level read-only. |
| `mountsd` | `mountsd`, `mountsd status` | Read-only status only. `ro`, `rw`, `off`, `init` remain blocked. |
| `hudlog` | `hudlog`, `hudlog status` | Status only. `on`/`off` remain blocked because they change display privacy state. |
| `diag` | `diag`, `diag summary`, `diag paths` | Summary/path display only. `full` and `bundle` remain blocked. |
| `wifiinv` | `wifiinv`, `wifiinv summary`, `wifiinv paths` | Read cached inventory only. `refresh` remains blocked. |
| `wififeas` | `wififeas`, `wififeas summary`, `wififeas gate`, `wififeas paths` | Read cached feasibility only. `refresh` remains blocked. |
| `netservice` | `netservice`, `netservice status` | Status only. `start`, `stop`, `enable`, `disable`, `token show`, `token rotate` remain blocked. |
| `rshell` | `rshell`, `rshell status`, `rshell audit` | Status/audit only. `start`, `stop`, `enable`, `disable`, `token show`, `rotate-token` remain blocked. |
| `service` | `service`, `service list`, `service status [name]` | Service inventory only. `start`, `stop`, `enable`, `disable` remain blocked. |

## Always Blocked While Menu Is Visible

These commands or forms must remain blocked in non-power menu-active state:

- process execution: `run`, `runandroid`, `busybox`, `toybox`, `userland test`
- filesystem mutation: `writefile`, `mountfs`, `mknodc`, `mknodb`, `mkdir`, `umount`
- storage mutation: `mountsd ro`, `mountsd rw`, `mountsd off`, `mountsd init`
- display/privacy mutation: `hudlog on`, `hudlog off`, `clear`, `kmssolid`, `kmsframe`, `displaytest`, `cutoutcal`, `statushud`, `watchhud`
- input wait loops: `readinput`, `waitkey`, `waitgesture`, `inputmonitor`, `blindmenu`
- service/network mutation: `netservice start|stop|enable|disable|token`, `rshell start|stop|enable|disable|token|rotate-token`, `service start|stop|enable|disable`, `startadbd`, `stopadbd`, `usbacmreset`
- power/destructive: `reboot`, `recovery`, `poweroff`, `prepareandroid`

## Implementation Plan

1. Copy v127 to `init_v128.c` and `v128/*.inc.c`; bump `a90_config.h` to
   `0.9.28` / `v128` and add changelog `0.9.28 v128 MENU SUBCOMMAND POLICY`.
2. Add argument-aware policy API in `a90_controller.c/h`:

```c
enum a90_controller_busy_reason a90_controller_command_busy_reason_ex(
    const char *name,
    unsigned int flags,
    int argc,
    char **argv,
    bool menu_active,
    bool power_page_active);
```

3. Keep the existing `a90_controller_command_busy_reason()` wrapper for retained
   older call sites and have it preserve v127 conservative behavior.
4. Change only v128 `execute_shell_command()` to call the `_ex()` API with
   `argc/argv`.
5. Implement small helpers for exact safe subcommand checks:

```text
subcmd_absent_or_status(argv, argc)
subcmd_one_of(argv, argc, allowed[])
service_status_or_list_only(argv, argc)
```

6. Log decisions using the existing busy path. Do not add noisy logs for every
   allowed observation command.

## Test Plan

### Static

- Build v128 static ARM64 init.
- Check `strings` for `A90 Linux init 0.9.28 (v128)`, `A90v128`, and
  `0.9.28 v128 MENU SUBCOMMAND POLICY`.
- `git diff --check`.
- host Python `py_compile` for revalidation scripts.
- Add/keep a small host-side controller policy harness covering every allowed
  and blocked subcommand form.

### Device

Flash `stage3/boot_linux_v128.img` with:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v128.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.28 (v128)" \
  --verify-protocol auto
```

With `screenmenu` visible, verify allowed:

- `status`, `storage`, `timeline`, `logpath`
- `mountsd status`
- `diag summary`, `diag paths`
- `hudlog status`
- `helpers status`, `helpers path a90_tcpctl`
- `selftest status`, `selftest verbose`
- `pid1guard status`, `pid1guard verbose`
- `netservice status`, `rshell status`, `rshell audit`
- `service list`, `service status autohud`

With `screenmenu` visible, verify blocked with `rc=-16 status=busy`:

- `run /bin/a90sleep 1`
- `runandroid /system/bin/toybox true`
- `writefile /tmp/a90-v128-test blocked`
- `mountfs /dev/null /tmp tmpfs`
- `mknodc /tmp/a90-v128-node 1 3`
- `mknodb /tmp/a90-v128-block 1 0`
- `mountsd rw`, `mountsd off`, `mountsd init`
- `diag full`, `diag bundle`
- `hudlog on`, `hudlog off`
- `netservice start`, `netservice enable`, `netservice token show`, `netservice token rotate`
- `rshell start`, `rshell enable`, `rshell token show`, `rshell rotate-token test`
- `service start tcpctl`, `service enable rshell`
- `startadbd`, `stopadbd`, `usbacmreset`, `recovery`, `reboot`, `poweroff`

After `hide`, verify representative commands still work as before:

- `run /bin/a90sleep 1`
- `selftest verbose`
- `status`

## Acceptance Criteria

- v127 F023 mitigation remains intact: risky side-effect commands are still
  blocked while menu is visible.
- Safe read-only subcommands are available without needing `hide`.
- No mutating subcommand is allowed only because its parent command has a status
  mode.
- F021/F030 trust-boundary status is unchanged.
- README/latest verified/report are updated only after real-device flash PASS.

## Deferred

- Token or physical-confirmation policy for USB ACM/bridge root shell.
- Full authorization framework or role model.
- Moving shell command handlers out of the include tree.
