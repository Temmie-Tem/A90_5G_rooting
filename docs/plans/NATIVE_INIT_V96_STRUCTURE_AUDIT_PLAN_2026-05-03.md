# v96 Plan: Structure Audit / Refactor Debt Cleanup

Date: `2026-05-03`

## Summary

- Target: `A90 Linux init 0.8.27 (v96)` / `0.8.27 v96 STRUCTURE AUDIT`
- Baseline: `A90 Linux init 0.8.26 (v95)` is latest verified.
- Goal: audit the v95 module split before adding SD runtime, BusyBox, remote shell, service manager, or Wi-Fi work.
- Scope: find duplication, stale direct access, unclear module boundaries, and low-risk mechanical cleanup candidates.
- Policy: v96 is mostly a cleanup/checkpoint version. Do not add user-facing SD/userland/network features.

This is the first step of the v96-v105 roadmap:
`docs/plans/NATIVE_INIT_LONG_TERM_ROADMAP_2026-05-03.md`.

## Why v96 Comes Before SD/Userland Expansion

v81-v95 moved major responsibilities into real `.c/.h` modules:

- log/timeline/console/cmdproto/run/service
- KMS/draw/input/HUD/menu/metrics
- shell/controller/storage/selftest
- USB gadget/netservice

That split is large enough that adding `/mnt/sdext/a90` runtime root, BusyBox, dropbear, or TCP shell now would make later cleanup more expensive. v96 should first verify that the module boundaries are coherent and that v95 behavior still has a clean rollback path.

## Audit Targets

### 1. USB Gadget vs Netservice

Check that responsibilities stay separated:

- `a90_usb_gadget.c/h` owns configfs/UDC/ACM primitive operations.
- `a90_netservice.c/h` owns NCM/tcpctl policy, flag state, helper execution, and service PID tracking.
- include-tree command handlers should call these APIs, not manipulate `/config/usb_gadget/g1/UDC` directly.

Searches:

```bash
rg -n "setup_acm_gadget|reap_tcpctl_child|/config/usb_gadget/g1/UDC|acm\\.usb0|ncm\\.usb0|a90_usbnet|a90_tcpctl" \
  stage3/linux_init/init_v95.c stage3/linux_init/v95 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- direct configfs/UDC writes are limited to `a90_usb_gadget.c` or helper binaries;
- NCM/tcpctl start/stop logic is in `a90_netservice.c`;
- shell/status/menu/selftest use status snapshots or public APIs.

### 2. Storage vs SD Runtime Policy

Check that v95 storage logic is ready for v97 SD runtime root:

- `a90_storage.c/h` owns SD mount/probe/cache fallback state.
- UI/shell/HUD should consume storage snapshots and paths through APIs.
- hardcoded `/mnt/sdext/a90` text in UI labels is acceptable, but path policy should not be duplicated.

Searches:

```bash
rg -n "/mnt/sdext|SD_WORKSPACE_DIR|SD_MOUNT_POINT|/cache/native-init.log|storage_state|boot_storage|mountsd" \
  stage3/linux_init/init_v95.c stage3/linux_init/v95 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- path constants come from `a90_config.h`;
- mutable storage state stays inside `a90_storage.c`;
- v97 can add runtime directories without rewriting unrelated HUD/menu code.

### 3. Run/Service Lifecycle Duplication

Check that command handlers do not reintroduce ad-hoc `fork`/`waitpid`/`kill` management.

Searches:

```bash
rg -n "fork\\(|waitpid\\(|kill\\(|setsid\\(|SIGTERM|SIGKILL" \
  stage3/linux_init/init_v95.c stage3/linux_init/v95 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- PID1 command execution uses `a90_run.c/h`;
- long-lived service PID state uses `a90_service.c/h`;
- helper binaries may still manage their own children internally.

### 4. Shell/Controller Busy Policy

Check that menu busy rules and command metadata do not drift between shell dispatch and controller.

Searches:

```bash
rg -n "busy|hide|hidemenu|resume|screenmenu|dangerous|power page|A90_COMMAND|a90_controller|a90_shell" \
  stage3/linux_init/init_v95.c stage3/linux_init/v95 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- command flags/types live through `a90_shell`;
- menu/power-page gate policy lives through `a90_controller`;
- `screenmenu` stays nonblocking;
- `blindmenu` stays foreground rescue UI.

### 5. HUD/Metrics/Input/Menu Layering

Check that UI modules have not formed circular dependencies:

- metrics should not call HUD/menu/shell/console;
- input should not call menu;
- draw should not call HUD/menu;
- menu model should not draw directly;
- HUD should render state but not own shell command dispatch.

Searches:

```bash
rg -n "#include \"a90_(hud|menu|input|metrics|draw|kms|shell|controller)\\.h\"" \
  stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- dependency direction matches `NATIVE_INIT_NEXT_WORK_2026-04-25.md`;
- any exception is documented in the v96 report.

### 6. Stale Names / Old API Residue

Check for old pre-module names that should not exist in v95 active code.

Searches:

```bash
rg -n "native_logf|native_log_ready|timeline_record\\(|cprintf\\(|console_fd|cmdv1x_decode|kms_state\\.|struct kms_display_state|cpustress_worker|setup_acm_gadget|reap_tcpctl_child" \
  stage3/linux_init/init_v95.c stage3/linux_init/v95 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- old names are absent from active v95 tree or only appear as internal module state where intended;
- false positives are listed in the report rather than blindly edited.

## Allowed Changes

v96 may apply low-risk cleanup if the audit finds concrete issues:

- move duplicated constants to `a90_config.h`;
- replace direct status/path access with existing API calls;
- remove dead forward declarations or stale helpers;
- rename misleading local functions if no behavior changes;
- add small comments to document module ownership only when ambiguity is real;
- add audit-only docs and report files.

## Deferred Changes

Do not include these in v96:

- SD runtime root directory expansion;
- helper deployment/package manifest;
- BusyBox integration;
- TCP shell/dropbear;
- service manager redesign;
- Wi-Fi inventory or bring-up;
- major command handler file migration;
- boot-critical policy changes.

## Implementation Plan

1. Copy v95 to `init_v96.c` and `v96/*.inc.c`.
2. Update version/build/kmsg/about/changelog:
   - `A90 Linux init 0.8.27 (v96)`
   - `A90v96`
   - `0.8.27 v96 STRUCTURE AUDIT`
3. Run the audit searches above and record findings.
4. Apply only low-risk cleanup patches with no user-facing behavior change.
5. Build `init_v96` using the same module set as v95.
6. Repack `stage3/boot_linux_v96.img` from v95 boot image arguments.
7. Flash and verify on device.
8. Write `docs/reports/NATIVE_INIT_V96_STRUCTURE_AUDIT_2026-05-03.md`.
9. Update README/latest verified only after real-device PASS.

## Local Validation

Build command should include the v95 module set:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v96 \
  stage3/linux_init/init_v96.c \
  stage3/linux_init/a90_util.c \
  stage3/linux_init/a90_log.c \
  stage3/linux_init/a90_timeline.c \
  stage3/linux_init/a90_console.c \
  stage3/linux_init/a90_cmdproto.c \
  stage3/linux_init/a90_run.c \
  stage3/linux_init/a90_service.c \
  stage3/linux_init/a90_kms.c \
  stage3/linux_init/a90_draw.c \
  stage3/linux_init/a90_input.c \
  stage3/linux_init/a90_hud.c \
  stage3/linux_init/a90_menu.c \
  stage3/linux_init/a90_metrics.c \
  stage3/linux_init/a90_shell.c \
  stage3/linux_init/a90_controller.c \
  stage3/linux_init/a90_storage.c \
  stage3/linux_init/a90_selftest.c \
  stage3/linux_init/a90_usb_gadget.c \
  stage3/linux_init/a90_netservice.c
```

Static checks:

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/netservice_reconnect_soak.py \
  scripts/revalidation/cleanup_stage3_artifacts.py
strings stage3/linux_init/init_v96 | rg "A90 Linux init 0.8.27 \\(v96\\)|A90v96|0.8.27 v96 STRUCTURE AUDIT"
```

## Device Validation

Flash:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v96.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.27 (v96)" \
  --verify-protocol auto
```

Baseline regression:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py "selftest verbose"
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py "mountsd status"
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py "autohud 2"
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py "netservice status"
```

Optional regression if USB/NCM is available:

```bash
python3 scripts/revalidation/a90ctl.py "netservice start"
# host config may require sudo ip addr replace 192.168.7.1/24 dev <enx...>
ping -c 3 -W 2 192.168.7.2
python3 scripts/revalidation/tcpctl_host.py ping
python3 scripts/revalidation/tcpctl_host.py status
python3 scripts/revalidation/a90ctl.py "netservice stop"
```

## Acceptance

- v95 behavior is preserved.
- `selftest` remains known-good with `fail=0`.
- Audit report lists each finding as one of:
  - fixed in v96,
  - intentional false positive,
  - deferred to v97+,
  - unsafe to change without device-specific test.
- README/latest verified points to v96 only after flash validation.
- v97 can start from a cleaner boundary for SD runtime root work.
