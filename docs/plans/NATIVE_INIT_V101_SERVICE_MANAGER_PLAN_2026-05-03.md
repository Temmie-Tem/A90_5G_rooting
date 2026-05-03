# v101 Plan: Minimal Service Manager

Date: `2026-05-03`

## Summary

- v101 target: `A90 Linux init 0.9.1 (v101)` / `0.9.1 v101 SERVICE MANAGER`.
- Baseline: v100 verified remote shell over USB NCM.
- Goal: turn the existing PID-only `a90_service.c/h` registry into a small service manager view for status, lifecycle, and enable policy.
- Scope is intentionally small: add a common service metadata/status layer and a `service` shell command, but keep each service's real start/stop implementation in its current owner.
- This is not a daemon supervisor and must not block PID1 boot, serial rescue, or HUD/menu responsiveness.

## Current Problem

v100 already tracks service PIDs for:

- `autohud` via `A90_SERVICE_HUD`
- `tcpctl` via `A90_SERVICE_TCPCTL`, started by `a90_netservice`
- `adbd` via `A90_SERVICE_ADBD`
- `rshell` via `A90_SERVICE_RSHELL`

However, service state is spread across command handlers and modules:

- `status` manually reaps and prints `adbd`, `autohud`, netservice, and `rshell` state.
- `netservice status/start/stop/enable/disable` owns NCM and `tcpctl` policy.
- `rshell status/start/stop/enable/disable` owns token remote shell policy and starts NCM if needed.
- boot path manually starts `autohud`, optional `netservice`, and optional `rshell` in sequence.

The immediate value of v101 is not new features. The value is a consistent operator view:

```text
service list
service status [name]
service start <name>
service stop <name>
service enable <name>
service disable <name>
```

## Design Direction

### 1. Extend `a90_service.c/h`, do not replace service owners

`a90_service` should own metadata and PID registry helpers:

```c
enum a90_service_kind {
    A90_SERVICE_KIND_DISPLAY,
    A90_SERVICE_KIND_NETWORK,
    A90_SERVICE_KIND_REMOTE,
    A90_SERVICE_KIND_ANDROID,
};

enum a90_service_flag {
    A90_SERVICE_FLAG_NONE = 0,
    A90_SERVICE_FLAG_BOOT_OPTIONAL = 1u << 0,
    A90_SERVICE_FLAG_RAW_CONTROL = 1u << 1,
    A90_SERVICE_FLAG_REQUIRES_NCM = 1u << 2,
    A90_SERVICE_FLAG_DANGEROUS = 1u << 3,
};

struct a90_service_info {
    enum a90_service_id id;
    const char *name;
    const char *description;
    enum a90_service_kind kind;
    unsigned int flags;
    pid_t pid;
    bool running;
    bool enabled;
    const char *enable_path;
};
```

Candidate API:

```c
const char *a90_service_name(enum a90_service_id id);
int a90_service_id_from_name(const char *name, enum a90_service_id *out);
int a90_service_info(enum a90_service_id id, struct a90_service_info *out);
int a90_service_count(void);
enum a90_service_id a90_service_id_at(int index);
void a90_service_reap_all(void);
```

The existing APIs stay valid:

```c
pid_t a90_service_pid(enum a90_service_id service);
void a90_service_set_pid(enum a90_service_id service, pid_t pid);
void a90_service_clear(enum a90_service_id service);
int a90_service_reap(enum a90_service_id service, int *status_out);
int a90_service_stop(enum a90_service_id service, int timeout_ms);
```

### 2. Keep service start/stop policy in current owners

Do not move `start_auto_hud()`, `a90_netservice_start()`, `rshell_start_service()`, or `cmd_startadbd()` wholesale into `a90_service.c` in v101.

Reason: those functions depend on UI state, USB re-enumeration, token files, NCM helpers, and existing shell output behavior. Moving them all at once would create high risk and obscure failures.

Instead, v101 include tree should add a thin controller layer, likely in `v101/80_shell_dispatch.inc.c` or a small new include section:

```text
service start autohud  -> start_auto_hud(...)
service stop autohud   -> cmd_stophud()
service start tcpctl   -> a90_netservice_start()
service stop tcpctl    -> a90_netservice_stop()
service start rshell   -> rshell_start_service(true)
service stop rshell    -> rshell_stop_service()
service start adbd     -> cmd_startadbd()
service stop adbd      -> cmd_stopadbd()
```

This keeps behavior identical while exposing one operator command.

### 3. Treat netservice and tcpctl carefully

`tcpctl` is not independent from NCM:

- Starting `tcpctl` means starting `netservice`, because `a90_netservice_start()` configures NCM, IP, and then spawns `a90_tcpctl`.
- Stopping `tcpctl` through the common service command should call `a90_netservice_stop()` only if the user explicitly chooses the `tcpctl`/`netservice` service target.
- `netservice start|stop|enable|disable` remains as a compatibility command.

Recommended names:

```text
service status tcpctl
service start tcpctl
service stop tcpctl
```

Optional alias:

```text
service status netservice
```

But internally it should still map to `A90_SERVICE_TCPCTL` plus `a90_netservice_status()`.

### 4. Preserve rshell opt-in safety

`rshell` is disabled by default and token-authenticated.

`service start rshell` may start NCM first, so it is re-enumeration-sensitive. Mark it with:

```text
RAW_CONTROL | REQUIRES_NCM | DANGEROUS
```

`service enable rshell` should use the existing `rshell_set_enabled(true)` and `rshell_start_service(true)` path. `service disable rshell` should stop first or remove the flag using the same semantics as `rshell disable`.

The existing `rshell` command remains the detailed command for token operations:

```text
rshell token [show]
rshell rotate-token [value]
```

### 5. Enable policy is per-service, not universal

Not all tracked services have enable flags today:

| Service | Runtime PID | Enable flag | v101 command behavior |
|---|---:|---|---|
| `autohud` | yes | no stable boot flag | start/stop/status only |
| `tcpctl` / `netservice` | yes | `/cache/native-init-netservice` | start/stop/enable/disable/status |
| `rshell` | yes | runtime state `remote-shell.enabled` | start/stop/enable/disable/status |
| `adbd` | yes but unstable | no | start/stop/status only, no enable |

If `service enable autohud` or `service enable adbd` is requested, return `-EOPNOTSUPP` with a clear message.

## Key Changes

- Copy v100 to `stage3/linux_init/init_v101.c` and `stage3/linux_init/v101/*.inc.c`.
- Bump version markers:
  - `INIT_VERSION "0.9.1"`
  - `INIT_BUILD "v101"`
  - `A90 Linux init 0.9.1 (v101)`
  - `A90v101`
  - `0.9.1 v101 SERVICE MANAGER`
- Extend `a90_service.c/h` with service metadata/status APIs.
- Add `service [list|status|start|stop|enable|disable] [name]` shell command in the v101 include tree.
- Update `help`, `status`, `bootstatus`, and `selftest verbose` to use the common service info where low-risk.
- Keep compatibility commands:
  - `autohud`, `stophud`
  - `startadbd`, `stopadbd`
  - `netservice ...`
  - `rshell ...`
- Keep raw-control behavior for commands that can re-enumerate USB or interrupt framed responses:
  - `netservice start|stop|enable|disable`
  - `rshell start|stop|enable|disable`
  - `service start|stop|enable|disable tcpctl`
  - `service start|stop|enable|disable rshell`

## Non-Goals

- No systemd/OpenRC clone.
- No dependency solver.
- No automatic restart/supervision loop.
- No new long-running service type beyond existing `autohud`, `tcpctl`, `rshell`, and `adbd` placeholder.
- No Dropbear promotion.
- No Wi-Fi enablement.
- No service parallel boot.
- No command handler file split beyond what is needed for the service command.

## Implementation Order

1. Copy v100 source tree to v101 and bump markers.
2. Extend `a90_service.c/h` metadata APIs without behavior changes.
3. Add read-only `service list/status` command and test locally.
4. Add `service start/stop` dispatch for existing owners.
5. Add `service enable/disable` only for `tcpctl` and `rshell`.
6. Update `status`, `bootstatus`, and `selftest verbose` summaries where safe.
7. Build `init_v101`, create ramdisk/boot image, flash, and validate.
8. Write v101 report and promote latest verified only after real-device PASS.

## Test Plan

### Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v101 \
  stage3/linux_init/init_v101.c \
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
  stage3/linux_init/a90_netservice.c \
  stage3/linux_init/a90_runtime.c \
  stage3/linux_init/a90_helper.c \
  stage3/linux_init/a90_userland.c
```

Confirm markers:

```bash
strings stage3/linux_init/init_v101 | rg 'A90 Linux init 0\.9\.1 \(v101\)|A90v101|0\.9\.1 v101 SERVICE MANAGER'
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/rshell_host.py \
  scripts/revalidation/helper_deploy.py
rg -n 'A90v100|0\.9\.0 v100|init_v100' stage3/linux_init/init_v101.c stage3/linux_init/v101
```

The stale marker scan should return only intentional historical changelog text.

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v101.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.1 (v101)" \
  --verify-protocol auto
```

Baseline commands:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py 'selftest verbose'
python3 scripts/revalidation/a90ctl.py service
python3 scripts/revalidation/a90ctl.py 'service list'
python3 scripts/revalidation/a90ctl.py 'service status autohud'
python3 scripts/revalidation/a90ctl.py 'service status tcpctl'
python3 scripts/revalidation/a90ctl.py 'service status rshell'
python3 scripts/revalidation/a90ctl.py 'service status adbd'
```

Lifecycle regression:

```bash
python3 scripts/revalidation/a90ctl.py 'service stop autohud'
python3 scripts/revalidation/a90ctl.py 'service start autohud'
python3 scripts/revalidation/a90ctl.py 'service enable tcpctl'
python3 scripts/revalidation/a90ctl.py 'service status tcpctl'
ping -c 3 -W 2 192.168.7.2
python3 scripts/revalidation/tcpctl_host.py ping
python3 scripts/revalidation/a90ctl.py 'service disable tcpctl'
python3 scripts/revalidation/rshell_host.py --bridge-timeout 60 start
python3 scripts/revalidation/rshell_host.py --timeout 20 smoke
python3 scripts/revalidation/a90ctl.py 'service status rshell'
python3 scripts/revalidation/a90ctl.py 'service stop rshell'
python3 scripts/revalidation/a90ctl.py 'service disable rshell'
python3 scripts/revalidation/a90ctl.py version
```

ADB placeholder regression:

```bash
python3 scripts/revalidation/a90ctl.py 'service status adbd'
python3 scripts/revalidation/a90ctl.py startadbd || true
python3 scripts/revalidation/a90ctl.py 'service status adbd'
python3 scripts/revalidation/a90ctl.py stopadbd || true
```

UI regression:

```bash
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py 'autohud 2'
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py 'cpustress 3 2'
```

## Acceptance

- `service list/status` shows all tracked services with consistent `running`, `pid`, `enabled`, `kind`, and flags.
- `service start/stop autohud` behaves like `autohud`/`stophud`.
- `service start/stop tcpctl` behaves like netservice start/stop and preserves serial rescue after USB re-enumeration.
- `service start/stop rshell` behaves like `rshell start/stop`, with token auth intact and no orphan `a90_rshell` process after stop.
- Unsupported enable/disable requests return a clear error and do not change boot behavior.
- v100 compatibility commands still work.
- Boot remains warn-only for optional services; shell/HUD still appears even if netservice or rshell startup fails.
- README/latest verified/report/task queue are updated only after real-device flash validation passes.

## Expected Report

After PASS, write:

```text
docs/reports/NATIVE_INIT_V101_SERVICE_MANAGER_2026-05-03.md
```

Record:

- artifact hashes for `init_v101`, `ramdisk_v101.cpio`, `boot_linux_v101.img`
- service command outputs
- tcpctl/NCM lifecycle evidence
- rshell lifecycle evidence
- serial rescue rollback evidence
- unsupported enable/disable behavior

## Next After v101

If v101 passes, the next roadmap item is v102 diagnostics/log bundle. That should consume the service manager view instead of scraping each command independently.
