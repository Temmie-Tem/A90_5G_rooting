# v135 Plan: Controller Policy Matrix

## Summary

v135 targets `A90 Linux init 0.9.35 (v135)` / `0.9.35 v135 POLICY MATRIX`.
The goal is not to add a new feature or broaden control channels. The goal is to
turn the menu-visible and power-page command safety policy into an explicit,
repeatable matrix that can be checked by PID1 and by host tooling.

Current baseline:

- latest verified build is `A90 Linux init 0.9.34 (v134)`;
- v134 exposure guardrail is flash-verified;
- local targeted v134 rescan is `PASS=15`, `WARN=1`, `FAIL=0`;
- remaining warning is accepted USB-local/localhost root-control boundary;
- recent F033 was caused by a subcommand policy mismatch: bare `mountsd` looked
  read-only to the controller but performed a remount side effect.

v135 should reduce this class of mistakes by making the controller policy
self-documenting and testable.

## Scope Decision

Choose `controller command policy matrix` for v135.

Rationale:

- The next fresh security scan has no blocker at this point.
- `a90_controller.c` currently keeps menu/power allowlists as string checks and
  several command-specific subcommand helpers.
- The shell command table has grown enough that new commands can accidentally
  miss menu/power policy review.
- v134 added `exposure` as an observation command; the next hardening step is to
  prove which commands are safe while the screen menu is visible.

Do not implement Wi-Fi, new listeners, auth changes, or a shell rewrite in v135.

## Key Changes

- Copy v134 into `init_v135.c` and `v135/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.35` / `v135` and add changelog text
  `0.9.35 v135 POLICY MATRIX`.
- Add a controller policy matrix API, preferably in `a90_controller.c/h`:
  - `a90_controller_policy_check()` for a single command vector;
  - `a90_controller_policy_matrix_run()` for all built-in matrix cases;
  - `a90_controller_policy_matrix_summary()` for compact status output;
  - optional entry accessor for verbose output.
- Add shell command `policycheck [status|run|verbose]`:
  - `policycheck` / `policycheck status`: print latest matrix summary;
  - `policycheck run`: run the built-in matrix and return non-zero on failure;
  - `policycheck verbose`: print each case, expected decision, actual decision,
    and reason.
- Add compact policy summary to `bootstatus` or `status` only if the output stays
  short enough. Prefer `bootstatus` because policy drift affects boot/control
  safety.
- Extend `local_security_rescan.py` with a wiring check that confirms:
  - `policycheck` command is registered;
  - matrix cases cover `mountsd`, `netservice`, `rshell`, `service`, `run`,
    `writefile`, `mountfs`, `reboot`, and `exposure`;
  - bare `mountsd` is not allowed while menu-visible.

## Required Matrix Cases

The matrix should be small but cover representative side-effect boundaries.

### Menu Visible, Normal Page

Expected allowed:

- `version`
- `status`
- `bootstatus`
- `exposure status`
- `exposure verbose`
- `storage`
- `runtime`
- `timeline`
- `logpath`
- `helpers status`
- `helpers verbose`
- `helpers manifest`
- `helpers plan`
- `helpers path a90_cpustress`
- `selftest status`
- `selftest verbose`
- `pid1guard status`
- `pid1guard verbose`
- `mountsd status`
- `netservice status`
- `rshell status`
- `rshell audit`
- `service list`
- `service status`
- `service status tcpctl`
- `diag summary`
- `diag paths`
- `wifiinv summary`
- `wifiinv paths`
- `wififeas summary`
- `wififeas gate`
- `hide`

Expected blocked:

- bare `mountsd`
- `mountsd ro`
- `mountsd rw`
- `mountsd off`
- `mountsd init`
- `netservice start`
- `netservice stop`
- `netservice enable`
- `netservice disable`
- `rshell start`
- `rshell stop`
- `rshell enable`
- `rshell disable`
- `rshell token show`
- `rshell rotate-token`
- `service start tcpctl`
- `service stop tcpctl`
- `service enable tcpctl`
- `service disable tcpctl`
- `service start rshell`
- `hudlog on`
- `hudlog off`
- `diag full`
- `diag bundle`
- `wifiinv refresh`
- `wififeas refresh`
- `userland test all`
- `busybox sh`
- `toybox sh`
- `run /bin/a90sleep 1`
- `runandroid /system/bin/toybox true`
- `writefile /tmp/x y`
- `mountfs tmpfs /tmp/x tmpfs`
- `mknodc /tmp/x 1 3`
- `umount /mnt/sdext`
- `reboot`
- `recovery`
- `poweroff`

### Menu Visible, Power Page

Expected allowed:

- `help`
- `version`
- `status`
- `bootstatus`
- `exposure status`
- `storage`
- `timeline`
- `last`
- `logpath`
- `logcat`
- `inputlayout`
- `inputmonitor`
- `uname`
- `pwd`
- `mounts`
- `reattach`
- `stophud`
- `hide`

Expected blocked:

- all network/service mutation commands;
- all filesystem write/mount/mknod commands;
- all process execution commands;
- `screenmenu` re-entry if it would change state unexpectedly;
- `reboot`, `recovery`, `poweroff` from serial unless already selected through
  the physical power menu path.

## Implementation Rules

- Keep controller policy pure: it may inspect command name, flags, argv, and
  menu/power state, but it must not execute command handlers or mutate services.
- Matrix checks must call the same controller policy path used by real shell
  dispatch, not a duplicate policy implementation.
- `policycheck run` must be non-destructive and safe to run during boot, during
  normal shell use, and while menu is visible.
- `policycheck` itself is an observation command and should be allowed while the
  menu is visible.
- Do not relax any existing busy gate as part of v135 unless the matrix proves it
  is a read-only observation command.
- Prefer adding explicit cases over broad wildcard rules. Broad rules are what
  caused the previous bare-subcommand mismatch class.

## Test Plan

- Local build:
  - build `init_v135.c` with all shared modules;
  - check `strings` for `A90 Linux init 0.9.35 (v135)`, `A90v135`,
    `0.9.35 v135 POLICY MATRIX`, and `policycheck [status|run|verbose]`.
- Static checks:
  - `git diff --check`;
  - host Python `py_compile` including `local_security_rescan.py`;
  - stale marker scan for v134 markers in v135 active files;
  - `rg` check that `policycheck` is registered in v135 shell table;
  - `rg` check that matrix cases mention at least the high-risk command names
    listed above.
- Device validation:
  - flash `stage3/boot_linux_v135.img` through native bridge/TWRP;
  - verify `version`, `status`, `bootstatus`, `selftest verbose`;
  - run `policycheck`, `policycheck run`, `policycheck verbose`;
  - run `screenmenu`, then verify observation commands still return rc=0;
  - while menu is visible, verify representative blocked commands return busy:
    `mountsd`, `mountsd rw`, `netservice start`, `rshell start`,
    `service start tcpctl`, `run /bin/a90sleep 1`, `writefile /tmp/x y`;
  - run `hide`, then verify normal shell commands still work.
- Security regression:
  - rerun `local_security_rescan.py` and require `FAIL=0`;
  - verify F032/F033 targeted checks still pass;
  - verify v134 `exposure guard` still returns rc=0.
- UI/regression:
  - `screenmenu` nonblocking behavior remains intact;
  - physical menu navigation still works;
  - `hide` returns immediately;
  - quick `native_soak_validate.py` remains PASS if time allows.

## Docs And Acceptance

- Add report `docs/reports/NATIVE_INIT_V135_POLICY_MATRIX_2026-05-07.md` after
  implementation.
- Update README/latest verified only after real-device flash and matrix runtime
  validation pass.
- Update security docs only after the local rescan and manual busy-gate checks
  pass.

Acceptance criteria:

- policy matrix PASS on device;
- menu-visible side-effect commands are denied;
- menu-visible observation commands still work;
- power-page policy is explicit and tested;
- bare-subcommand side-effect class is covered by matrix cases;
- no new listener, network exposure, or destructive behavior is introduced.

## Assumptions

- v135 is a control-policy hardening release, not a feature release.
- The matrix is allowed to be conservative. If a command is not clearly
  read-only, it should remain blocked while the menu is visible.
- Existing `blindmenu` rescue foreground behavior remains unchanged.
- Host `a90ctl.py` command argument encoding remains unchanged.
- Any future Wi-Fi/network-facing work should keep this matrix passing before it
  is considered verified.
