# Native Init v99 Plan: BusyBox Static Userland Evaluation

Date: `2026-05-03`

## Summary

- Baseline: `A90 Linux init 0.8.29 (v98)`.
- Target: `A90 Linux init 0.8.30 (v99)` / `0.8.30 v99 BUSYBOX USERLAND`.
- Goal: evaluate static ARM64 BusyBox as an optional userland layer under the v98 SD runtime/helper contract.
- Scope is deliberately narrow: build/import, deploy, inventory, run wrapper, applet smoke tests, and BusyBox-vs-toybox comparison.
- BusyBox must not replace the PID 1 native shell, must not become a boot dependency, and must not weaken serial recovery.

## Current Baseline

v98 provides the right staging layer for static userland work:

```text
/mnt/sdext/a90          preferred runtime root when SD is healthy
/cache/a90-runtime      fallback runtime root when SD is unsafe/missing

bin/                    executable static helpers/userland binaries
pkg/helpers.manifest    optional helper/userland manifest
state/helper-state      helper inventory state
logs/helper-deploy.log  host deploy log target
```

Verified v98 state:

- `runtime`: `backend=sd root=/mnt/sdext/a90 fallback=no writable=yes`
- `helpers`: `entries=5 warn=0 fail=0 manifest=no`
- `selftest verbose`: `pass=10 warn=0 fail=0`
- `helper_deploy.py manifest` can generate manifest lines for known helper candidates
- `a90_helper_preferred_path()` can prefer runtime-root helpers while preserving ramdisk/cache fallback

Existing userland evidence:

- `toybox 0.8.13` static ARM64 was previously built and validated from `/cache/bin/toybox`.
- Existing netservice/tcpctl host tools still default to `/cache/bin/toybox`.
- `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md` is the baseline candidate report.

## Non-Goals

- No full Debian/Ubuntu/Alpine-style distro bootstrap.
- No package manager or dependency resolver.
- No replacement of the native init shell loop.
- No automatic internet download from the device.
- No dynamic linker or shared-library dependency.
- No writes to Android `system`, `vendor`, `efs`, modem, bootloader, or identity/security partitions.
- No remote shell or SSH service; that remains v100+.

## BusyBox Placement Policy

Primary target:

```text
/mnt/sdext/a90/bin/busybox
```

Optional fallback candidates:

```text
/cache/bin/busybox
/bin/busybox
```

Rules:

- BusyBox is optional in v99. Missing BusyBox is WARN/manual-test failure, not a boot failure.
- Native recovery commands must work with no BusyBox present.
- If BusyBox is deployed to SD, its manifest entry should use role `userland`.
- If BusyBox is added to ramdisk later, it must still be treated as optional unless a future plan explicitly changes boot policy.
- `toybox` remains a separate comparison candidate and should not be silently replaced.

Recommended manifest entries:

```text
# name path role required sha256 mode size
busybox /mnt/sdext/a90/bin/busybox userland no <sha256> 0755 <bytes>
toybox /mnt/sdext/a90/bin/toybox userland no <sha256> 0755 <bytes>
```

## Host Build / Import Policy

v99 should support two host-side paths.

### Build Locally

Add a host helper only if the toolchain and source acquisition are clear:

```text
scripts/revalidation/build_static_busybox.sh
```

Expected local artifacts:

```text
external_tools/userland/src/busybox-<version>/
external_tools/userland/build/busybox-<version>-aarch64-static.log
external_tools/userland/bin/busybox-aarch64-static-<version>
external_tools/userland/bin/busybox-aarch64-static
external_tools/userland/pkg/busybox-<version>-config
external_tools/userland/pkg/busybox-<version>-sha256.txt
```

Build requirements:

- Use `aarch64-linux-gnu-gcc`.
- Build static ARM64 output.
- Record BusyBox version, config, local source archive hash, final binary hash, and `file/readelf` evidence.
- Do not commit generated BusyBox binaries unless license/source/config handling is explicitly decided.

### Import Prebuilt

If a trusted local static BusyBox binary is provided manually:

```text
external_tools/userland/bin/busybox-aarch64-static
```

The import path must still record:

- source/provenance note
- `sha256sum`
- `file`
- `readelf -d` static evidence
- applet list snapshot

## Device-Side API

Add `a90_userland.c/h`.

Candidate public API:

```c
enum a90_userland_kind {
    A90_USERLAND_BUSYBOX,
    A90_USERLAND_TOYBOX,
};

struct a90_userland_entry {
    enum a90_userland_kind kind;
    char name[32];
    char preferred_path[256];
    char fallback_path[256];
    char selected_path[256];
    bool present;
    bool executable;
    long long size;
    char warning[160];
};

int a90_userland_scan(void);
int a90_userland_count(void);
int a90_userland_entry_at(int index, struct a90_userland_entry *out);
const char *a90_userland_path(const char *name);
int a90_userland_summary(char *out, size_t out_size);
```

Implementation constraints:

- `a90_userland` may depend on `a90_helper`, `a90_runtime`, `a90_util`, `a90_log`, and `a90_config`.
- `a90_userland` must not depend on HUD/menu/shell internals.
- `a90_userland` should only select paths and summarize inventory; shell command handlers should still use `a90_run`.
- Do not introduce a generic `PATH` search that can accidentally execute unknown SD files.

## Shell Commands

Add a small explicit command surface:

```text
userland
userland status
userland verbose
userland test [busybox|toybox|all]
busybox <applet> [args...]
toybox <applet> [args...]
```

Expected behavior:

- `userland` / `userland status`: concise BusyBox/toybox availability summary.
- `userland verbose`: path, size, executable bit, fallback decision.
- `userland test busybox`: non-destructive applet smoke test using BusyBox when present.
- `userland test toybox`: equivalent toybox comparison path when present.
- `busybox <applet> ...`: runs selected BusyBox path through `a90_run`.
- `toybox <applet> ...`: runs selected toybox path through `a90_run`.

Command policy:

- Missing BusyBox should return a clear non-zero rc for manual BusyBox commands.
- Missing BusyBox must not break `status`, `bootstatus`, `selftest`, `screenmenu`, `netservice`, or recovery commands.
- `busybox sh` is allowed for evaluation, but it is a foreground child process, not a replacement native shell.
- `busybox --install`, symlink farms, and global PATH mutation are out of scope for v99.

## Applet Smoke Test Matrix

The first applet set should stay read-only or low-risk:

| Applet | Command | Expected |
|---|---|---|
| help | `busybox --help` | exit 0, prints applet list |
| shell | `busybox sh -c 'echo A90_BUSYBOX_OK'` | exit 0, expected text |
| uname | `busybox uname -a` | exit 0 |
| ls | `busybox ls /proc` | exit 0 |
| cat | `busybox cat /proc/version` | exit 0 |
| ps | `busybox ps` or `busybox ps -A` | exit 0 if applet exists |
| mount | `busybox mount` | exit 0, read-only listing behavior |
| dmesg | `busybox dmesg` or `busybox dmesg -s 1024` | exit 0 if allowed |
| ifconfig/ip | `busybox ifconfig -a` or `busybox ip addr` | exit 0 if applet exists |
| kill | `busybox kill -0 1` | exit 0 |

Notes:

- Applet absence is WARN for the comparison report, not a v99 boot failure.
- Avoid destructive applets and write operations in boot selftest.
- Keep command timeouts short and use `a90_run` cancellation/timeout handling.

## Host-Side Tooling

Extend `scripts/revalidation/helper_deploy.py` or add a narrow wrapper:

```text
scripts/revalidation/busybox_userland.py
```

Candidate commands:

```text
busybox_userland.py status
busybox_userland.py local-info <busybox_path>
busybox_userland.py push <busybox_path>
busybox_userland.py manifest
busybox_userland.py verify
busybox_userland.py smoke
busybox_userland.py compare-toybox
```

Transport policy:

- Prefer v98 runtime-root discovery through `a90ctl.py runtime`.
- Prefer `helper_deploy.py push` or shared helper-deploy primitives if practical.
- Do not require NCM for v99; serial bridge plus existing deploy paths are acceptable.
- If NCM is active, host-side smoke can also run through tcpctl for coverage, but serial bridge remains the rescue control channel.

## Boot-Time Behavior

Boot should stay conservative:

- Run only a quick userland inventory after runtime/helper scan.
- Missing BusyBox should log WARN or "not installed" state but keep boot path PASS.
- Boot selftest may include a read-only userland inventory entry.
- Boot selftest must not run `busybox sh`, applet smoke tests, or any long-running command automatically.
- `status` and `bootstatus` should expose concise userland summary.

## Implementation Steps

1. Commit this plan before code changes.
2. Copy v98 source to `init_v99.c` and `v99/*.inc.c`.
3. Bump `a90_config.h` version/build/marker to `0.8.30` / `v99`.
4. Add `a90_userland.c/h` and wire quick inventory into boot/status/selftest.
5. Add explicit shell commands: `userland`, `busybox`, and `toybox`.
6. Add or extend host tooling for BusyBox local-info, manifest, push, verify, and smoke.
7. Build local v99 init and boot image.
8. Flash v99 and run device regression before updating latest verified docs.

## Test Plan

Local build:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v99 \
  stage3/linux_init/init_v99.c \
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

Static checks:

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/helper_deploy.py
strings stage3/linux_init/init_v99 | rg "A90 Linux init 0.8.30|A90v99|0.8.30 v99 BUSYBOX USERLAND"
```

Boot image:

- Reuse v98 boot image header/kernel args.
- Replace ramdisk with `stage3/ramdisk_v99.cpio`.
- Confirm ramdisk contains `/init`, `/bin/a90sleep`, and `/bin/a90_cpustress`.
- BusyBox should normally be deployed to SD runtime root, not required in ramdisk.

Device validation:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v99.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.30 (v99)" \
  --verify-protocol auto
```

Regression:

```text
version
status
bootstatus
runtime
helpers
userland
userland verbose
selftest verbose
storage
mountsd status
statushud
autohud 2
screenmenu
hide
netservice status
```

BusyBox smoke when deployed:

```text
userland test busybox
busybox --help
busybox sh -c 'echo A90_BUSYBOX_OK'
busybox ls /proc
busybox cat /proc/version
busybox ps
busybox mount
busybox kill -0 1
```

Toybox comparison:

```text
userland test toybox
toybox uname -a
toybox ifconfig -a
toybox route -n
```

## Acceptance

- v99 boots and verifies as `A90 Linux init 0.8.30 (v99)`.
- BusyBox, if present, runs from the SD runtime root or a documented fallback path.
- Missing BusyBox does not block boot or break existing native commands.
- Applet failures return meaningful rc through `a90_run`.
- Native recovery functions remain independent from BusyBox.
- BusyBox-vs-toybox applet coverage and reliability differences are recorded in a v99 report.
- README/latest verified and cleanup retention are updated only after real-device flash validation passes.

## Deferred To v100+

- TCP shell or SSH service.
- Dropbear packaging.
- BusyBox symlink farm and global PATH policy.
- Package manager semantics.
- Wi-Fi inventory or association.
- Long-running service manager expansion.
