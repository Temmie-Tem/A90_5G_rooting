# Native Init v98 Plan: Helper Deployment / Package Manifest

Date: `2026-05-03`

## Summary

- Baseline: `A90 Linux init 0.8.28 (v97)`.
- Target: `A90 Linux init 0.8.29 (v98)` / `0.8.29 v98 HELPER DEPLOY`.
- Goal: define and implement a safe helper deployment model on the v97 runtime root.
- Scope is deliberately narrow: helper inventory, manifest/hash verification, runtime-vs-ramdisk helper selection, and host-side deployment/verification support.
- BusyBox userland evaluation, dropbear/TCP shell, Wi-Fi, and package manager behavior stay deferred to v99+.

## Current Baseline

v97 established the runtime root contract:

```text
/mnt/sdext/a90          preferred runtime root when SD is healthy
/cache/a90-runtime      fallback runtime root when SD is unsafe/missing

bin/                    executable static helpers
etc/                    config
logs/                   runtime logs
tmp/                    scratch
state/                  service state
pkg/                    manifests/staged payloads
run/                    pid/socket-like transient state
```

Verified v97 state:

- `runtime`: `backend=sd root=/mnt/sdext/a90 fallback=no writable=yes`
- `selftest verbose`: `pass=9 warn=0 fail=0`
- `status`/`bootstatus` expose runtime root health
- `a90_runtime.c/h` provides runtime directory APIs

v98 should depend on `a90_runtime_*` APIs, not raw `SD_WORKSPACE_DIR` path access.

## Non-Goals

- No network download from the device.
- No dynamic linker or shared-library dependency.
- No writes to Android `system`, `vendor`, `efs`, modem, bootloader, or identity/security partitions.
- No automatic replacement of boot-critical ramdisk helpers.
- No BusyBox shell adoption yet.
- No dropbear/OpenSSH or TCP shell service yet.
- No package manager with dependency resolution.

## Proposed Runtime Layout

```text
/mnt/sdext/a90/
├── bin/
│   ├── a90_cpustress
│   ├── a90_usbnet
│   ├── a90_tcpctl
│   └── toybox
├── pkg/
│   ├── helpers.manifest
│   └── staged/
├── state/
│   └── helper-state
└── logs/
    └── helper-deploy.log
```

Initial helper candidates:

| helper | source today | v98 policy |
|---|---|---|
| `a90_cpustress` | ramdisk `/bin/a90_cpustress` | mirror to SD as optional preferred helper, keep ramdisk fallback |
| `a90_usbnet` | `/cache/bin/a90_usbnet` | inventory/verify only first; do not make boot depend on SD copy until verified |
| `a90_tcpctl` | `/cache/bin/a90_tcpctl` | inventory/verify only first; preserve current netservice behavior |
| `toybox` | `/cache/bin/toybox` | inventory/verify only; BusyBox/toybox policy remains v99+ |
| `a90sleep` | ramdisk `/bin/a90sleep` | keep ramdisk recovery helper; optional SD mirror |

## Manifest Format

Use a small line-oriented manifest. It must be easy to parse in static C without JSON dependencies.

Recommended file: `/mnt/sdext/a90/pkg/helpers.manifest`

```text
# name path role required sha256 mode size
a90_cpustress /mnt/sdext/a90/bin/a90_cpustress ramdisk-mirror no <sha256> 0755 <bytes>
a90_usbnet /mnt/sdext/a90/bin/a90_usbnet net-helper no <sha256> 0755 <bytes>
a90_tcpctl /mnt/sdext/a90/bin/a90_tcpctl tcp-control no <sha256> 0755 <bytes>
toybox /mnt/sdext/a90/bin/toybox userland no <sha256> 0755 <bytes>
a90sleep /mnt/sdext/a90/bin/a90sleep test-helper no <sha256> 0755 <bytes>
```

Rules:

- `required=yes` should be avoided in v98; missing SD helpers must not block boot.
- Hash mismatch is WARN for optional helpers and FAIL only for manual deploy verification.
- Manifest path is runtime-root dependent, not hardcoded to SD when fallback is active.
- Parser should ignore blank lines and `#` comments.
- Unknown fields should make that line invalid but must not crash PID1.

## Device-Side API

Add `a90_helper.c/h`.

Candidate public API:

```c
struct a90_helper_entry {
    char name[64];
    char path[256];
    char role[64];
    char expected_sha256[65];
    char actual_sha256[65];
    unsigned int expected_mode;
    unsigned int actual_mode;
    long long expected_size;
    long long actual_size;
    bool present;
    bool executable;
    bool hash_match;
    bool required;
    char warning[160];
};

int a90_helper_scan(void);
int a90_helper_count(void);
int a90_helper_entry_at(int index, struct a90_helper_entry *out);
int a90_helper_find(const char *name, struct a90_helper_entry *out);
const char *a90_helper_manifest_path(void);
const char *a90_helper_preferred_path(const char *name, const char *fallback);
int a90_helper_print_inventory(bool verbose);
```

Implementation constraints:

- `a90_helper` may depend on `a90_runtime`, `a90_util`, `a90_log`, and `a90_config`.
- `a90_helper` must not depend on HUD/menu/shell internals.
- If SHA256 implementation is too large for PID1, v98 may use size/mode/presence first and reserve SHA256 for host-side validation; document that explicitly if chosen.
- Hashing large files must be bounded and non-blocking enough for manual commands; boot path should use cached manifest summary or quick presence/mode checks only.

## Shell Commands

Add:

```text
helpers
helpers status
helpers verbose
helpers path <name>
helpers verify [name]
```

Expected behavior:

- `helpers` / `helpers status`: concise inventory summary.
- `helpers verbose`: one line per helper with path, present, mode, size, hash state, role.
- `helpers path <name>`: prints preferred executable path and fallback decision.
- `helpers verify [name]`: performs full hash verification where available and returns non-zero only for required helper failures or explicit requested helper mismatch.

Preserve existing command behavior:

- `cpustress` may prefer SD `a90_cpustress` only if verified executable; otherwise use ramdisk `/bin/a90_cpustress`.
- `netservice` should continue using current `/cache/bin/a90_usbnet` and `/cache/bin/a90_tcpctl` until a later plan explicitly migrates netservice helpers.
- `run` remains general-purpose and does not automatically search helper paths.

## Host-Side Tooling

Add `scripts/revalidation/helper_deploy.py`.

Commands:

```text
helper_deploy.py status
helper_deploy.py manifest
helper_deploy.py push <local_path> <name>
helper_deploy.py verify
helper_deploy.py rollback <name>
```

Default path assumptions:

- control: serial bridge `127.0.0.1:54321`
- runtime root: discover with `a90ctl.py runtime`
- deploy target: `<runtime_root>/bin`
- manifest target: `<runtime_root>/pkg/helpers.manifest`

Transport policy:

- Prefer existing bridge commands and safe device-side `run`/`cat`/`stat` primitives where practical.
- If NCM/TCP file transfer is not ready, v98 may keep host deploy as manifest generation + operator-assisted `adb push`/TWRP copy procedure.
- Do not make network availability a v98 boot requirement.

## Boot-Time Behavior

Boot must stay safe:

- Quick helper scan may run after `a90_runtime_init()`.
- Missing optional helper must produce WARN/log only.
- Boot selftest should include a helper manifest summary:
  - PASS when manifest absent but helper deployment is optional
  - WARN when manifest exists but optional helper is missing/mismatched
  - FAIL only if a manifest marks a helper `required=yes` and it is missing/mismatched
- `status` and `bootstatus` should expose concise helper summary.

## Test Plan

Local:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v98 \
  stage3/linux_init/init_v98.c \
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
  stage3/linux_init/a90_helper.c
```

Static checks:

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/netservice_reconnect_soak.py \
  scripts/revalidation/cleanup_stage3_artifacts.py \
  scripts/revalidation/helper_deploy.py
```

Artifact checks:

- `strings stage3/linux_init/init_v98` contains:
  - `A90 Linux init 0.8.29 (v98)`
  - `A90v98`
  - `0.8.29 v98 HELPER DEPLOY`
- `stage3/ramdisk_v98.cpio` contains `/init`, `/bin/a90sleep`, `/bin/a90_cpustress`.
- `stage3/boot_linux_v98.img` is generated by reusing v97 boot args and replacing ramdisk.

Device flash:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v98.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.29 (v98)" \
  --verify-protocol auto
```

Regression:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py runtime
python3 scripts/revalidation/a90ctl.py helpers
python3 scripts/revalidation/a90ctl.py helpers verbose
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py mountsd status
python3 scripts/revalidation/a90ctl.py cpustress 3 2
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py autohud 2
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py netservice status
```

Host helper deploy:

```bash
python3 scripts/revalidation/helper_deploy.py status
python3 scripts/revalidation/helper_deploy.py manifest
python3 scripts/revalidation/helper_deploy.py verify
```

## Acceptance

- v98 boot image flashes and verifies with `cmdv1 version/status`.
- Missing SD helper manifest does not block boot.
- `helpers` command reports runtime root, manifest path, and helper inventory.
- Optional helper mismatch is visible as WARN, not boot failure.
- `cpustress` still runs and cancels using a valid helper path.
- Netservice remains compatible with v97 behavior.
- Report `docs/reports/NATIVE_INIT_V98_HELPER_DEPLOY_2026-05-03.md` records artifact hashes and device validation.
- README/latest verified and cleanup retention are updated only after real-device validation passes.

## Deferred To v99+

- BusyBox applet policy and shell integration.
- Dropbear/custom TCP shell.
- Moving netservice helper canonical paths from `/cache/bin` to SD.
- Package dependency model.
- Remote download/install.
