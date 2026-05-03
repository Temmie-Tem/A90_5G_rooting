# v102 Plan: Diagnostics / Log Bundle

Date: `2026-05-03`

## Summary

- v102 target: `A90 Linux init 0.9.2 (v102)` / `0.9.2 v102 DIAGNOSTICS`.
- Baseline: v101 verified minimal service manager.
- Goal: make boot/runtime regressions easy to collect, compare, and hand off.
- Scope is intentionally read-only: add a `diag` shell command and a host-side collector, but do not change service lifecycle, USB/NCM policy, storage mount policy, or Wi-Fi behavior.
- Diagnostics must be safe to run repeatedly from serial bridge and should not require NCM, although host tooling may optionally collect NCM/remote-shell information when available.

## Current Problem

v101 has enough modules and operators that manual validation now requires many separate commands:

```text
version
status
bootstatus
selftest verbose
storage
runtime
helpers verbose
userland verbose
service list
rshell status
netservice status
mounts
cat /proc/partitions
logcat
```

That is workable during interactive development, but poor for regressions:

- command output is not captured as one timestamped artifact;
- repeated manual collection is inconsistent across versions;
- host-side evidence is split between serial bridge output, NCM ping, tcpctl, rshell smoke, and local artifact hashes;
- log snippets are hard to compare when a later refactor changes boot timing or service state.

v102 should make the default failure report deterministic and diffable.

## Design Direction

### 1. Add read-only `diag` command

Recommended shell surface:

```text
diag [summary|full|bundle|paths]
```

Behavior:

- `diag` / `diag summary`: compact operator view for serial console.
- `diag full`: verbose read-only report printed to console.
- `diag bundle`: write a timestamped text bundle under runtime logs if writable, otherwise `/cache` fallback.
- `diag paths`: print intended bundle/log paths only.

The command must not:

- start or stop services;
- rebind USB;
- mount/unmount/format SD;
- run CPU stress;
- rotate rshell tokens;
- collect private identity/security partition data;
- dump large binary partitions.

### 2. Keep diagnostics textual and diffable

A bundle should be plain UTF-8 text with stable section headers:

```text
[A90 DIAG]
[version]
[bootstatus]
[selftest]
[storage]
[runtime]
[helpers]
[userland]
[service]
[network]
[rshell]
[mounts]
[partitions]
[logs]
[host-notes]
```

Each section should prefer existing module APIs or existing command handlers instead of duplicating policy.

Candidate device-side content:

- version banner, `INIT_VERSION`, `INIT_BUILD`, kernel uname;
- boot summary and timeline count;
- selftest summary and optional verbose entries;
- storage status and mountsd status-equivalent state;
- runtime status and key directories;
- helper inventory summary and optional verbose inventory;
- userland BusyBox/toybox summary;
- service list/status for `autohud`, `tcpctl`, `adbd`, `rshell`;
- netservice read-only status;
- rshell read-only status without token display by default;
- `/proc/mounts`;
- `/proc/partitions`;
- current log path and recent native log tail.

### 3. Add a small diag module only if it reduces duplication

Preferred implementation is a small `a90_diag.c/h` compiled module.

Candidate API:

```c
int a90_diag_print_summary(void);
int a90_diag_print_full(void);
int a90_diag_write_bundle(char *out_path, size_t out_size);
const char *a90_diag_default_dir(void);
```

Allowed dependencies:

```text
diag -> config/util/log/timeline/storage/runtime/helper/userland/service/netservice/selftest/console
```

Forbidden dependencies:

```text
diag -> hud/menu/input/kms draw internals
```

Reason: diagnostics is an operator/reporting layer, not a UI renderer.

### 4. Add host-side collector script

Add `scripts/revalidation/diag_collect.py`.

Default mode should use serial bridge and `a90ctl.py`:

```bash
python3 scripts/revalidation/diag_collect.py --out tmp/diag/latest.txt
```

Recommended behavior:

- run `diag full` through `a90ctl.py`;
- run `diag bundle` if requested and print device-side path;
- collect host-side current git commit, tracked diff status, boot image SHA if provided;
- optionally run NCM ping/tcpctl/rshell checks when explicitly requested;
- write a host-side timestamped text file under `tmp/diag/` or a user-specified path.

Non-default optional flags:

```text
--device-bundle
--boot-image stage3/boot_linux_v102.img
--ncm-ping 192.168.7.2
--tcpctl
--rshell-smoke
```

The collector should not hide destructive failures by default. Optional network checks can be skipped if NCM is disabled.

### 5. Preserve raw-control boundaries

`diag` must not wrap or trigger these commands internally:

```text
reboot
recovery
poweroff
usbacmreset
netservice start|stop|enable|disable
rshell start|stop|enable|disable|rotate-token
service start|stop|enable|disable tcpctl|rshell|adbd
mountsd ro|rw|off|init
```

If those states are needed, `diag` should report the existing state only.

## Key Changes

- Copy v101 to `stage3/linux_init/init_v102.c` and `stage3/linux_init/v102/*.inc.c`.
- Bump version markers:
  - `INIT_VERSION "0.9.2"`
  - `INIT_BUILD "v102"`
  - `A90 Linux init 0.9.2 (v102)`
  - `A90v102`
  - `0.9.2 v102 DIAGNOSTICS`
- Add `diag [summary|full|bundle|paths]` to help and command table.
- Add `a90_diag.c/h` if implementation stays cleaner than embedding all logic in the v102 include tree.
- Add `scripts/revalidation/diag_collect.py` for host-side serial-first collection.
- Update docs/report only after real-device PASS.

## Non-Goals

- No Wi-Fi inventory; that is v103.
- No Wi-Fi enablement; that is v104 only if v103 supports it.
- No new service manager behavior.
- No service supervisor or automatic restart.
- No USB re-enumeration inside diagnostics.
- No binary partition backup.
- No private token display by default.
- No log upload or external network dependency.

## Implementation Order

1. Copy v101 source tree to v102 and bump markers.
2. Define bundle section format and path policy.
3. Add read-only `diag summary/full` first.
4. Add `diag bundle` with runtime log dir fallback.
5. Add host-side `diag_collect.py` serial-first collector.
6. Build v102 boot image and flash.
7. Validate device commands and host collector.
8. Write v102 report and promote latest verified only after real-device PASS.

## Test Plan

### Local Build

- Build v102 static ARM64 init with existing v101 modules plus `a90_diag.c` if added.
- Confirm `strings` include:
  - `A90 Linux init 0.9.2 (v102)`
  - `A90v102`
  - `0.9.2 v102 DIAGNOSTICS`
  - `diag [summary|full|bundle|paths]`

### Static Checks

- `git diff --check`
- Host Python compile:
  - `scripts/revalidation/a90ctl.py`
  - `scripts/revalidation/native_init_flash.py`
  - `scripts/revalidation/rshell_host.py`
  - `scripts/revalidation/diag_collect.py`
- Stale marker scan for v102 tree:
  - no `A90v101` boot marker in v102 source;
  - no `0.9.1 v102` mixed version string;
  - no stale `init_v101` references in v102 source.

### Device Validation

Flash:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v102.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.2 (v102)" \
  --verify-protocol auto
```

Serial commands:

```text
version
status
bootstatus
selftest verbose
diag
diag full
diag paths
diag bundle
storage
runtime
helpers verbose
userland verbose
service list
rshell status
netservice status
statushud
autohud 2
screenmenu
hide
```

Host collector:

```bash
python3 scripts/revalidation/diag_collect.py --out tmp/diag/v102-smoke.txt
python3 scripts/revalidation/diag_collect.py --device-bundle --out tmp/diag/v102-bundle.txt
```

Optional network checks if NCM is already enabled or explicitly requested:

```bash
python3 scripts/revalidation/diag_collect.py --ncm-ping 192.168.7.2 --tcpctl --out tmp/diag/v102-ncm.txt
```

## Acceptance Criteria

- `diag full` prints a complete read-only snapshot without hanging the shell.
- `diag bundle` writes a text bundle to runtime logs or `/cache` fallback and reports the path.
- Running `diag` repeatedly does not change service, USB, mount, token, or network state.
- Host collector produces a timestamped file that includes device diag output and host metadata.
- v101 user-visible behavior remains intact: HUD/menu, service command, rshell status, storage/runtime/helpers/userland, selftest, and serial bridge recovery.

## Assumptions

- v101 is latest verified before v102 implementation.
- SD runtime root is usually available, but `/cache` fallback must work.
- Serial bridge remains the primary diagnostics path.
- NCM/tcpctl/rshell diagnostics are optional and must not be required for basic collection.
- README/latest verified/report/task queue are updated only after v102 real-device validation passes.
