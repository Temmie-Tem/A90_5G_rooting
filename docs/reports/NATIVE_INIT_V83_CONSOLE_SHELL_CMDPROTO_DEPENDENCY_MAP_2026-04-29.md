# Native Init v83 Console/Shell/Cmdproto Dependency Map (2026-04-29)

## Summary

- Baseline: `A90 Linux init 0.8.13 (v82)`
- Scope: dependency map for the planned v83 `console + shell + cmdproto` boundary split.
- Source entrypoint: `stage3/linux_init/init_v82.c`
- Current shape: one PID1 translation unit made from `v82/*.inc.c`, plus true API modules for config/util/log/timeline.
- Goal for this map: identify which state and functions must move together so v83 can split responsibilities without changing behavior.

## Include Order

`stage3/linux_init/init_v82.c:9` includes the v82 tree in this order:

```text
00_prelude
10_core_log_console
20_device_display
30_status_hud
40_menu_apps
50_boot_services
60_shell_basic_commands
70_storage_android_net
80_shell_dispatch
90_main
```

This order currently hides several cross-file dependencies because every helper is `static` inside one translation unit. v83 should not blindly move files to separate `.c` objects until these hidden dependencies are given explicit headers.

## Global State Map

Defined in `stage3/linux_init/v82/00_prelude.inc.c:48`:

| State | Current Owner | Main Consumers | v83 Candidate Owner |
| --- | --- | --- | --- |
| `console_fd` | global prelude | `cprintf`, `read_line`, `cmd_cat`, `run`, `runandroid`, `startadbd` | `a90_console` |
| `last_console_reattach_ms` | global prelude | `reattach_console` | `a90_console` |
| `adbd_pid` | global prelude | `status`, `startadbd`, `stopadbd` | later `a90_service` or Android/adbd helper |
| `hud_pid` | global prelude | `status`, `autohud`, `stophud`, display commands | later `a90_hud` or `a90_service` |
| `tcpctl_pid` | global prelude | `status`, `netservice`, reap | later `a90_netservice` |
| `boot_storage` | global prelude | storage/status/HUD | later `a90_storage` |
| `last_result` | global prelude | `last`, command execution | `a90_shell` |
| `shell_protocol_seq` | global prelude | `cmdv1`, `cmdv1x` frames | `a90_cmdproto` |
| `kms_state` | global prelude | display/status/menu/HUD | later `a90_kms` |

The v83 split should prioritize the first, second, seventh, and eighth rows. Moving unrelated process/service state in the same patch would raise risk.

## Console Dependency Map

### Current Console Responsibilities

Console behavior is spread across multiple include files:

- Output sink: `cprintf()` writes formatted text to `console_fd` at `stage3/linux_init/v82/10_core_log_console.inc.c:37`.
- Initial attach: `attach_console()` opens `/dev/ttyGS0`, configures termios, assigns `console_fd`, and dup2s stdio at `stage3/linux_init/v82/50_boot_services.inc.c:116`.
- Reattach: `reattach_console()` closes/reopens the serial fd and optionally announces on the console at `stage3/linux_init/v82/50_boot_services.inc.c:187`.
- Line input: `read_line()` owns echo, backspace, Ctrl-C, Ctrl-U, escape consumption, idle reattach, poll-fault reattach at `stage3/linux_init/v82/50_boot_services.inc.c:240`.
- Prompt: `print_prompt()` formats `a90:<cwd>#` at `stage3/linux_init/v82/50_boot_services.inc.c:577`.
- TTY node wait is unexpectedly in the menu file: `wait_for_tty_gs0()` at `stage3/linux_init/v82/40_menu_apps.inc.c:5301`.

### Direct `console_fd` Consumers

These call sites prevent `console_fd` from being hidden immediately:

- `cmd_cat()` streams file bytes directly to `console_fd` at `stage3/linux_init/v82/60_shell_basic_commands.inc.c:356`.
- `cmd_run()` dup2s `console_fd` into child stdio at `stage3/linux_init/v82/70_storage_android_net.inc.c:552`.
- `cmd_runandroid()` dup2s `console_fd` into child stdio at `stage3/linux_init/v82/70_storage_android_net.inc.c:602`.
- `cmd_startadbd()` dup2s `console_fd` into child stdio at `stage3/linux_init/v82/70_storage_android_net.inc.c:683`.
- `read_line()` uses direct `write_all(console_fd, ...)` for echo/editing at `stage3/linux_init/v82/50_boot_services.inc.c:313`.

v83 should introduce small console APIs before hiding the fd:

```text
a90_console_printf()
a90_console_write()
a90_console_fd()
a90_console_dup_stdio()
a90_console_readline()
a90_console_reattach()
```

`a90_console_fd()` is intentionally a transitional API. The better long-term shape is `a90_console_dup_stdio()` and `a90_console_write()`, but `cmd_cat` and `run` need a low-risk bridge first.

### Cancel Input

Cancel input is logically console-owned but consumed by run, CPU stress, HUD watch, and input tools:

- `enum cancel_kind` is defined in `stage3/linux_init/v82/00_prelude.inc.c:102`.
- `read_console_cancel_event()` is implemented at `stage3/linux_init/v82/10_core_log_console.inc.c:199`.
- `poll_console_cancel()` is implemented at `stage3/linux_init/v82/10_core_log_console.inc.c:209`.
- `command_cancelled()` prints/logs standardized cancel results at `stage3/linux_init/v82/10_core_log_console.inc.c:223`.

Current cancel consumers:

| Consumer | Location | Notes |
| --- | --- | --- |
| `cmd_watchhud` | `stage3/linux_init/v82/30_status_hud.inc.c:712` | blocking display loop |
| `cmd_cpustress` | `stage3/linux_init/v82/60_shell_basic_commands.inc.c:268` | local worker stress test |
| `wait_child_cancelable` | `stage3/linux_init/v82/70_storage_android_net.inc.c:506` | `run` and `runandroid` |
| `cmd_readinput` | `stage3/linux_init/v82/40_menu_apps.inc.c:1151` | raw input read loop |
| `wait_for_input_gesture` | `stage3/linux_init/v82/40_menu_apps.inc.c:1715` | button gesture loop |
| `wait_for_key_press` | `stage3/linux_init/v82/40_menu_apps.inc.c:1839` | menu/app waits |
| `cmd_inputmonitor` | `stage3/linux_init/v82/40_menu_apps.inc.c:2284` | raw + gesture monitor |

v83 should move the cancel enum and functions with `a90_console`, not with `a90_shell`, because cancel is a property of the active console input stream.

## Shell Dependency Map

### Current Shell Responsibilities

The shell currently owns too much:

- command table and flags at `stage3/linux_init/v82/80_shell_dispatch.inc.c:504`
- lookup at `stage3/linux_init/v82/80_shell_dispatch.inc.c:572`
- auto-menu busy gate at `stage3/linux_init/v82/80_shell_dispatch.inc.c:592`
- A90P1 protocol frames at `stage3/linux_init/v82/80_shell_dispatch.inc.c:645`
- result rendering at `stage3/linux_init/v82/80_shell_dispatch.inc.c:699`
- command execution, duration, last result, HUD stop, logging at `stage3/linux_init/v82/80_shell_dispatch.inc.c:724`
- main shell read/parse/dispatch loop at `stage3/linux_init/v82/80_shell_dispatch.inc.c:835`

The `command_handler` typedef is currently defined late in `stage3/linux_init/v82/70_storage_android_net.inc.c:1162`, which works only because of the single-translation-unit include trick. v83 should move command type definitions into a shell header before the command table is compiled.

### Command Handler Sources

`80_shell_dispatch` wraps handlers implemented across multiple files:

| Handler Family | Current File | v83 Treatment |
| --- | --- | --- |
| basic shell/status/log/timeline | `60_shell_basic_commands` | leave as command implementation layer |
| device display probes | `20_device_display` | leave until v85 |
| HUD/display/input/menu apps | `30_status_hud`, `40_menu_apps` | leave until v85 |
| storage/android/run/adbd/netservice | `70_storage_android_net` | leave until v84 |
| reboot/recovery/poweroff wrappers | `80_shell_dispatch` and `70_storage_android_net` | keep raw/reboot behavior unchanged |

For v83, the shell module should own dispatch mechanics but not absorb every command implementation yet.

### Auto Menu Gate

The shell checks UI/menu state before allowing commands:

- IPC helpers live in `stage3/linux_init/v82/10_core_log_console.inc.c:75`.
- Shell busy policy lives in `stage3/linux_init/v82/80_shell_dispatch.inc.c:592`.
- Hide word handling lives in `stage3/linux_init/v82/80_shell_dispatch.inc.c:867`.
- Menu state is written by screen menu code in `stage3/linux_init/v82/40_menu_apps.inc.c`.

This is not purely console or shell. v83 can keep this as a transitional dependency, but the long-term owner should be a small `a90_menu_state` or UI state module so `console` does not learn menu policy.

## Cmdproto Dependency Map

### Current Cmdproto Responsibilities

`cmdv1` and `cmdv1x` are split between boot-service parsing helpers and shell dispatch:

- `hex_digit_value()` at `stage3/linux_init/v82/50_boot_services.inc.c:386`
- `parse_cmdv1x_token()` at `stage3/linux_init/v82/50_boot_services.inc.c:399`
- `decode_cmdv1x_args()` at `stage3/linux_init/v82/50_boot_services.inc.c:454`
- `shell_protocol_status()` at `stage3/linux_init/v82/80_shell_dispatch.inc.c:632`
- `shell_protocol_begin()` at `stage3/linux_init/v82/80_shell_dispatch.inc.c:645`
- `shell_protocol_end()` at `stage3/linux_init/v82/80_shell_dispatch.inc.c:656`
- `print_cmdv1x_error()` at `stage3/linux_init/v82/80_shell_dispatch.inc.c:673`
- protocol dispatch in `shell_loop()` at `stage3/linux_init/v82/80_shell_dispatch.inc.c:875`

### Cmdproto Dependencies

Cmdproto currently depends on:

```text
cprintf
shell_protocol_seq
command flags
save_last_result
a90_logf
execute_shell_command
strerror/errno formatting
```

The clean v83 boundary should be:

```text
a90_shell_loop
  -> a90_console_readline
  -> a90_shell_split_args
  -> a90_cmdproto_decode_if_needed
  -> a90_shell_execute(argv, argc, protocol_mode)
       -> a90_cmdproto_begin/end only when framed
```

`cmdproto` should not know how command lookup works. It should only encode/decode framed protocol metadata and print stable A90P1 records.

## Call Flow Map

### Normal Raw Command

```text
main
  -> shell_loop
    -> print_prompt
    -> read_line
       -> reattach_console on idle/fault/eof
    -> split_args
    -> execute_shell_command(protocol=false)
       -> find_command
       -> auto_menu_is_active / command_allowed_during_auto_menu
       -> stop_auto_hud if CMD_DISPLAY
       -> command->handler
       -> save_last_result
       -> print_shell_result
```

### `cmdv1`

```text
shell_loop
  -> detect argv[0] == cmdv1
  -> execute_shell_command(argv+1, protocol=true)
     -> shell_protocol_begin
     -> command->handler
     -> shell_protocol_end
```

### `cmdv1x`

```text
shell_loop
  -> detect argv[0] == cmdv1x
  -> decode_cmdv1x_args
     -> parse_cmdv1x_token
  -> execute_shell_command(decoded_argv, protocol=true)
  -> print_cmdv1x_error on decode failure
```

### Destructive/Reboot Commands

`reboot`, `recovery`, and `poweroff` have `CMD_NO_DONE` in `stage3/linux_init/v82/80_shell_dispatch.inc.c:567`. If they actually reboot, a framed command may not emit `A90P1 END`. Host tooling already keeps reboot/recovery paths on raw bridge control, and v83 should preserve that rule.

## Proposed v83 Module Boundary

### `a90_console.c/h`

Owns:

- `console_fd`
- `last_console_reattach_ms`
- tty wait/attach/reattach
- console printf/raw write
- line input and prompt support
- cancel polling/classification
- stdio dup helper for child processes

Transitional public API:

```text
int a90_console_wait_tty(void);
int a90_console_attach(void);
int a90_console_reattach(const char *reason, bool announce);
void a90_console_printf(const char *fmt, ...);
ssize_t a90_console_readline(char *buf, size_t size);
int a90_console_dup_stdio(void);
int a90_console_write(const void *buf, size_t len);
enum a90_cancel_kind a90_console_read_cancel_event(void);
enum a90_cancel_kind a90_console_poll_cancel(int timeout_ms);
int a90_console_cancelled(const char *tag, enum a90_cancel_kind cancel);
```

### `a90_cmdproto.c/h`

Owns:

- `shell_protocol_seq`
- A90P1 begin/end formatting
- protocol status string mapping
- `cmdv1x` length-prefixed hex argv decoding
- framed decode error output

It may depend on `a90_console` for output and `a90_log` for decode errors. It should not own the command table.

### `a90_shell.c/h`

Owns:

- `struct shell_command`
- `enum command_flags`
- `struct shell_last_result`
- command table
- command lookup
- busy gate around auto menu state
- raw/cmdv1/cmdv1x dispatch flow
- shell loop

It may depend on `a90_console`, `a90_cmdproto`, `a90_log`, `a90_util`, and command implementation headers or transitional include prototypes.

## Recommended v83 Execution Order

1. Create v83 copy from v82 and bump to `0.8.14 (v83)`.
2. Add `a90_console.h` with API names, but keep implementation movement minimal.
3. Replace direct call sites:
   - `cprintf` -> `a90_console_printf`
   - `poll_console_cancel` -> `a90_console_poll_cancel`
   - `read_console_cancel_event` -> `a90_console_read_cancel_event`
   - child `dup2(console_fd, ...)` -> `a90_console_dup_stdio`
   - `write_all(console_fd, ...)` file streaming -> `a90_console_write`
4. Move console fd state and implementation into `a90_console.c`.
5. Move `cmdv1x` decode and A90P1 frame helpers into `a90_cmdproto.c`.
6. Move shell table/execution/loop into `a90_shell.c` only after console/cmdproto compile cleanly.
7. Keep command implementation bodies in the v83 include tree unless the split is trivial.

## Risk Register

| Risk | Why It Matters | Mitigation |
| --- | --- | --- |
| hiding `console_fd` too early | `cat`, `run`, `runandroid`, `adbd` still need raw fd semantics | add `a90_console_write` and `a90_console_dup_stdio` first |
| moving `wait_for_tty_gs0` from menu file | it is currently used by boot and reattach despite living near menu code | move with console and keep behavior byte-for-byte |
| moving cmdproto before shell types | cmdproto needs flags/status but should not need command table internals | define small protocol input struct or pass primitives |
| framed reboot commands | successful reboot can cut connection before `A90P1 END` | keep host reboot/recovery paths raw and leave `CMD_NO_DONE` unchanged |
| auto-menu busy gate ownership | shell policy currently calls menu IPC helpers from core file | keep transitional API in v83; extract UI state later |
| broad command handler churn | many handlers print with console and use global state | v83 should not move all command implementations at once |

## v83 Acceptance Checks

- Local build:
  - static ARM64 build with `init_v83.c + a90_util.c + a90_log.c + a90_timeline.c + new v83 modules`
  - `strings` confirms `A90 Linux init 0.8.14 (v83)` and a v83 changelog marker
- Host checks:
  - `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py`
  - `git diff --check`
- Device checks:
  - flash from native through TWRP
  - `cmdv1 version/status` via `native_init_flash.py --verify-protocol auto`
  - `a90ctl.py version`
  - `a90ctl.py status`
  - `a90ctl.py logpath`
  - `a90ctl.py timeline`
  - `a90ctl.py bootstatus`
  - `a90ctl.py storage`
  - `a90ctl.py 'mountsd status'`
  - `a90ctl.py 'displaytest safe'`
  - `a90ctl.py 'autohud 2'`
  - cancel regression: `watchhud`, `cpustress`, or `run /bin/a90sleep` with q/Ctrl-C

## Conclusion

The safest v83 cut is not “move shell first.” The safer cut is:

```text
console fd/cancel API
  -> cmdproto frame/decode API
  -> shell dispatch API
```

`console` is the root dependency. Once console output/input/cancel is explicit, cmdproto and shell can be split without dragging the entire UI/storage/netservice tree with them.
