# v97 Plan: SD Runtime Root

Date: `2026-05-03`

## Summary

- Target: `A90 Linux init 0.8.28 (v97)` / `0.8.28 v97 SD RUNTIME ROOT`
- Baseline: `A90 Linux init 0.8.27 (v96)` is latest verified.
- Goal: promote `/mnt/sdext/a90` from a storage workspace into a deterministic native runtime root when the SD card is healthy.
- Scope: define runtime directories, health probes, fallback behavior, shell/HUD/selftest visibility, and future helper path policy.
- Policy: keep boot non-blocking. If SD runtime is missing or unsafe, warn and fall back to `/cache` instead of stopping shell/HUD boot.

This is v97 of the v96-v105 roadmap: `docs/plans/NATIVE_INIT_LONG_TERM_ROADMAP_2026-05-03.md`.

## Current Baseline

v96 already has:

- `a90_storage.c/h` for boot storage state, SD probe, cache fallback, `storage`, and `mountsd`.
- SD mount point: `/mnt/sdext`.
- Current workspace root: `/mnt/sdext/a90`.
- Current SD directories prepared by `a90_storage.c`:
  - `bin`
  - `logs`
  - `tmp`
  - `rootfs`
  - `images`
  - `backups`
- SD identity marker: `/mnt/sdext/a90/.a90-native-id`.
- SD native log path: `/mnt/sdext/a90/logs/native-init.log`.
- Fallback root: `/cache`.

The missing piece is a formal runtime contract. v97 should define what each directory means, how it is checked at boot, and how later v98-v100 work can safely place helpers, BusyBox, and remote services there.

## Proposed Runtime Layout

Runtime root candidates:

```text
/mnt/sdext/a90        # preferred runtime root when SD is healthy
/cache                # fallback runtime root when SD is missing/unsafe
```

Preferred SD layout:

```text
/mnt/sdext/a90/
├── bin/              # executable static helpers, v98+ deployment target
├── etc/              # simple config files and service flags, v97 creates only
├── logs/             # native-init.log and later diagnostic bundles
├── tmp/              # scratch files, boot probes, short-lived runtime data
├── state/            # persistent state owned by native init services
├── pkg/              # helper/package manifests and staged payloads
├── run/              # volatile runtime pid/socket/status files
├── images/           # optional local boot/helper image stash, not auto-flashed
├── backups/          # manually created backups, never auto-overwritten
└── rootfs/           # future rootfs experiments, inert in v97
```

Fallback `/cache` layout should be minimal:

```text
/cache/a90-runtime/
├── logs/
├── tmp/
├── state/
└── run/
```

`/cache` fallback must not pretend to support the full SD helper/package model. It is a rescue runtime root for logs, state, and minimal operation.

## Key Changes

### 1. Add Runtime API

Add `stage3/linux_init/a90_runtime.c/h`.

Candidate status model:

```c
struct a90_runtime_status {
    bool initialized;
    bool fallback;
    bool writable;
    char backend[16];
    char root[PATH_MAX];
    char bin[PATH_MAX];
    char etc[PATH_MAX];
    char logs[PATH_MAX];
    char tmp[PATH_MAX];
    char state[PATH_MAX];
    char pkg[PATH_MAX];
    char run[PATH_MAX];
    char warning[160];
    char detail[192];
};
```

Candidate API:

```c
int a90_runtime_init(const struct a90_storage_status *storage);
int a90_runtime_get_status(struct a90_runtime_status *out);
const char *a90_runtime_root(void);
const char *a90_runtime_bin_dir(void);
const char *a90_runtime_log_dir(void);
const char *a90_runtime_tmp_dir(void);
const char *a90_runtime_state_dir(void);
const char *a90_runtime_warning(void);
bool a90_runtime_using_fallback(void);
int a90_runtime_cmd_runtime(void);
```

Ownership rule:

- `a90_storage` decides whether SD is mounted, expected, and writable.
- `a90_runtime` decides the runtime root directory contract and health of runtime subdirectories.
- v98 helper deployment should depend on `a90_runtime`, not raw `SD_WORKSPACE_DIR`.

### 2. Runtime Directory Constants

Extend `a90_config.h` with path constants instead of scattering string literals:

```c
#define A90_RUNTIME_CACHE_ROOT "/cache/a90-runtime"
#define A90_RUNTIME_SD_ROOT SD_WORKSPACE_DIR
#define A90_RUNTIME_BIN_DIR "bin"
#define A90_RUNTIME_ETC_DIR "etc"
#define A90_RUNTIME_LOGS_DIR "logs"
#define A90_RUNTIME_TMP_DIR "tmp"
#define A90_RUNTIME_STATE_DIR "state"
#define A90_RUNTIME_PKG_DIR "pkg"
#define A90_RUNTIME_RUN_DIR "run"
```

v97 may keep existing `SD_WORKSPACE_DIR` names for compatibility, but new runtime-facing code should use `A90_RUNTIME_*` constants.

### 3. Boot Flow Integration

In `v97/90_main.inc.c`, boot flow should become:

```text
cache mount
storage probe
log path selection
runtime init from storage status
selftest
USB/console/HUD/shell as before
```

Boot splash should show concise state:

```text
[ STORAGE] SD MAIN READY
[ RUNTIME] SD ROOT READY
```

Fallback example:

```text
[ STORAGE] WARN FALLBACK /cache
[ RUNTIME] CACHE ROOT READY
```

### 4. Shell/UI Visibility

Add command:

```text
runtime
```

Expected output:

```text
runtime: backend=sd root=/mnt/sdext/a90 fallback=no writable=yes
runtime: bin=/mnt/sdext/a90/bin
runtime: etc=/mnt/sdext/a90/etc
runtime: logs=/mnt/sdext/a90/logs
runtime: tmp=/mnt/sdext/a90/tmp
runtime: state=/mnt/sdext/a90/state
runtime: pkg=/mnt/sdext/a90/pkg
runtime: run=/mnt/sdext/a90/run
```

Update summaries:

- `status`: add one-line runtime status.
- `bootstatus`: add one-line runtime status after selftest summary.
- HUD: show warning when runtime falls back to `/cache`.
- `selftest verbose`: add a runtime check entry.

### 5. Selftest Expansion

Extend selftest with read-only/non-destructive runtime checks:

- runtime initialized;
- selected root exists;
- required directories exist;
- `tmp`, `state`, and `run` writable if backend is SD or cache;
- `bin`, `etc`, `pkg` existence only, no package execution.

`FAIL` remains warn-only for boot policy, but known-good A90 should produce `fail=0`.

### 6. Fallback Policy

Fallback is required if:

- SD is not present;
- SD UUID mismatch;
- SD mount fails;
- SD workspace identity marker fails;
- SD runtime required directory creation fails;
- runtime read/write probe fails.

Fallback behavior:

- root becomes `/cache/a90-runtime`;
- create minimal fallback directories;
- show persistent warning in HUD/status;
- do not start future SD-only services automatically;
- boot remains interactive.

## Explicit Non-Goals

- No helper deployment manifest yet.
- No BusyBox integration.
- No dropbear/custom TCP shell.
- No Wi-Fi work.
- No package manager.
- No automatic flashing from `images/`.
- No writes to Android system/vendor/data/efs/key partitions.
- No removal of existing `mountsd` command.

## Implementation Plan

1. Copy v96 to `init_v97.c` and `v97/*.inc.c`.
2. Update version/build/kmsg/about/changelog:
   - `A90 Linux init 0.8.28 (v97)`
   - `A90v97`
   - `0.8.28 v97 SD RUNTIME ROOT`
3. Add `a90_runtime.c/h`.
4. Add runtime path constants in `a90_config.h`.
5. Call `a90_runtime_init()` after storage probe.
6. Add `runtime` shell command and status/bootstatus summaries.
7. Extend selftest with runtime entry.
8. Build `init_v97`, generate `ramdisk_v97.cpio`, repack `boot_linux_v97.img`.
9. Flash and verify on device.
10. Write `docs/reports/NATIVE_INIT_V97_SD_RUNTIME_ROOT_2026-05-03.md`.
11. Update README/latest verified only after PASS.

## Validation

Local build:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v97 \
  stage3/linux_init/init_v97.c \
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
  stage3/linux_init/a90_runtime.c \
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
strings stage3/linux_init/init_v97 | rg "A90 Linux init 0.8.28 \\(v97\\)|A90v97|0.8.28 v97 SD RUNTIME ROOT"
```

Device flash:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v97.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.28 (v97)" \
  --verify-protocol auto
```

Device regression:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py runtime
python3 scripts/revalidation/a90ctl.py "selftest verbose"
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py "mountsd status"
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py "autohud 2"
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py "netservice status"
```

Optional fallback test when safe:

- boot once with SD absent or intentionally unmounted before runtime init only if recovery path is confirmed;
- verify `/cache/a90-runtime` fallback and HUD warning;
- do not make this mandatory for initial v97 PASS unless the physical test window is safe.

## Acceptance

- Healthy SD selects `/mnt/sdext/a90` as runtime root.
- Runtime directories exist and are reported deterministically.
- Known-good A90 selftest remains `fail=0`.
- `/cache/a90-runtime` fallback is implemented and documented.
- Existing `storage`, `mountsd`, HUD/menu, netservice, and serial behavior remain compatible with v96.
- v98 can use `a90_runtime_bin_dir()` and manifest paths without touching storage internals.
