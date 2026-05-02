# v93 Plan: Storage API First Split

Date: `2026-05-02`

## Summary

- Target: `A90 Linux init 0.8.24 (v93)` / `0.8.24 v93 STORAGE API`
- Goal: move boot storage state, SD workspace probing, `/cache` fallback policy, and `mountsd`/`storage` command logic behind a compiled `a90_storage.c/h` API.
- Baseline: v92 is verified with shell/controller APIs, nonblocking `screenmenu`, CPU stress helper, SD workspace fallback, and NCM/TCP control retained.
- Scope decision: v93 splits **storage only**. Netservice/USB gadget policy remains in the include tree and becomes the primary v94 candidate.
- This plan is documentation only. Code, boot image, README latest verified, and changelog stay on v92 until v93 is built, flashed, and verified.

## Current Shape

- `v92/00_prelude.inc.c` owns `cache_mount_ready` and `struct boot_storage_state` as file-static PID1 state.
- `v92/50_boot_services.inc.c` owns `setup_base_mounts()` and `mount_cache()`, while `/cache` readiness directly controls log fallback and boot storage fallback.
- `v92/60_shell_basic_commands.inc.c` still contains reusable storage-adjacent helpers: `mount_line_for_path()`, `read_ext4_uuid()`, `write_text_file_sync()`, `ensure_sd_workspace()`, `ensure_sd_identity_marker()`, and `sd_write_read_probe()`.
- `v92/70_storage_android_net.inc.c` mixes unrelated domains: boot SD probing, `mountsd`/`storage`, Android layout/run/adbd helpers, netservice start/stop, USB reattach, and recovery/reboot/poweroff commands.
- HUD currently receives storage status through `current_hud_storage_status()`, which reads `boot_storage` directly.
- Netservice is already partly stabilized by `a90_run` and `a90_service`, but it still has USB re-enumeration side effects and should not be moved in the same version as boot-critical storage.

## Target Boundary

```text
init_v93.c / include tree
  -> boot orchestration, splash hook wrappers, command registration
  -> Android layout/run/adbd, netservice, reboot/recovery remain in include tree

a90_storage.c/h
  -> /cache mount helper
  -> SD block/UUID/mount/workspace/RW probe
  -> boot storage state and fallback policy
  -> mountsd/storage command implementations
  -> storage status snapshot for HUD and shell

minimal a90_dev block helper, if needed
  -> /sys/class/block/<name>/dev -> /dev/block/<name>
```

`a90_storage` may depend on `a90_config`, `a90_util`, `a90_log`, `a90_timeline`, and `a90_console`. It must not depend on HUD/menu/shell dispatch/netservice.

## Key Changes

- Copy v92 to `init_v93.c` and `v93/*.inc.c`, then update version, boot marker, ABOUT, and changelog strings.
- Add `a90_storage.c/h` and move storage state into internal static module state.
- Add a tiny boot-progress hook so the storage module can report splash lines without calling HUD/menu functions directly:
  - `struct a90_storage_boot_hooks`
  - `a90_storage_probe_boot(const struct a90_storage_boot_hooks *hooks, void *ctx)`
- Replace direct global reads with a status snapshot API:
  - `a90_storage_get_status(struct a90_storage_status *out)`
  - `a90_storage_root()`
  - `a90_storage_backend()`
  - `a90_storage_warning()`
  - `a90_storage_using_fallback()`
- Move command implementations behind API calls:
  - `a90_storage_cmd_storage()`
  - `a90_storage_cmd_mountsd(char **argv, int argc)`
- Move or expose block-device lookup safely:
  - Preferred: add minimal `a90_dev.c/h` with `a90_dev_get_block_path()` and update `mountsystem`/`prepareandroid` call sites later as needed.
  - Fallback: keep the helper local to `a90_storage.c` only if no other v93 compiled module needs it.
- Keep these out of v93:
  - `prepareandroid`, `runandroid`, `startadbd`, `stopadbd`
  - `netservice status/start/stop/enable/disable`
  - USB gadget configfs helper policy
  - reboot/recovery/poweroff raw-control behavior

## Candidate API

```c
struct a90_storage_status {
    bool probed;
    bool sd_present;
    bool sd_mounted;
    bool sd_expected;
    bool sd_rw_ok;
    bool fallback;
    char backend[16];
    char root[PATH_MAX];
    char sd_uuid[40];
    char warning[128];
    char detail[160];
};

struct a90_storage_boot_hooks {
    void (*set_line)(void *ctx, int line, const char *text);
    void (*draw_frame)(void *ctx);
};

int a90_storage_mount_cache(void);
void a90_storage_set_cache_ready(bool ready);
int a90_storage_probe_boot(const struct a90_storage_boot_hooks *hooks, void *ctx);
int a90_storage_get_status(struct a90_storage_status *out);
const char *a90_storage_root(void);
const char *a90_storage_backend(void);
const char *a90_storage_warning(void);
bool a90_storage_using_fallback(void);
int a90_storage_cmd_storage(void);
int a90_storage_cmd_mountsd(char **argv, int argc);
```

## Boot Flow After v93

```text
setup_base_mounts()
a90_log_select_or_fallback(NATIVE_LOG_FALLBACK)
a90_storage_mount_cache()
  -> cache ok: a90_log_select_or_fallback(NATIVE_LOG_PRIMARY)
  -> cache fail: log remains /tmp fallback
a90_storage_probe_boot(storage_boot_hooks)
  -> expected SD + workspace + RW probe ok: log moves to SD path
  -> failure: cache or tmp fallback warning retained
setup_acm_gadget()
console attach
autohud starts with a90_storage_get_status() snapshot
netservice boot-if-enabled remains include-tree code for v93
```

## Test Plan

- Local build: static ARM64 build with v93 source plus existing modules and new `a90_storage.c`; include `a90_dev.c` only if block helper is extracted.
- Static checks: `git diff --check`, host Python `py_compile`, and `strings` markers for `A90 Linux init 0.8.24 (v93)`, `A90v93`, and `0.8.24 v93 STORAGE API`.
- Structure checks:
  - `rg "struct boot_storage_state|boot_storage\.|cache_mount_ready" stage3/linux_init/v93` should show no direct include-tree ownership except intentional wrapper code.
  - `rg "a90_storage_" stage3/linux_init/v93 stage3/linux_init/a90_storage.*` should show call sites through the new API.
  - Netservice implementation remains in `v93/70_storage_android_net.inc.c` or a renamed include file, not in `a90_storage.c`.
- Device flash: `native_init_flash.py stage3/boot_linux_v93.img --from-native --expect-version "A90 Linux init 0.8.24 (v93)" --verify-protocol auto`.
- Storage regression:
  - `version`, `status`, `bootstatus`, `logpath`, `timeline`, `storage`, `mountsd status`
  - `mountsd ro`, `mountsd rw`, `mountsd init`, `mountsd off`, then `mountsd status`
  - SD-present normal boot should keep `/mnt/sdext/a90/logs/native-init.log`
  - SD missing/mismatch path should retain visible fallback warning and use `/cache` or `/tmp` safely
- UI regression:
  - `statushud`, `autohud 2`, `screenmenu`, `hide`, log tail panel storage warning display
- Network regression:
  - `netservice status/start/stop/enable/disable` should behave like v92
  - NCM ping/TCP control smoke remains valid when netservice is enabled

## Acceptance Criteria

- v93 boots with the same SD/cache behavior as v92.
- No regression in `storage`, `mountsd`, `logpath`, boot timeline replay, or HUD storage warning display.
- `a90_storage.c/h` owns storage state; the include tree no longer reaches into `boot_storage` directly.
- Netservice remains behaviorally unchanged and is explicitly queued for v94.
- README/latest verified and changelog are updated only after real device flash validation passes.

## Follow-Up Candidates

- v94: `a90_netservice.c/h` and possibly `a90_usb_gadget.c/h` for NCM/tcpctl/USB configfs policy.
- v95: SD userland operation model: `/mnt/sdext/a90/bin`, helper deployment, log/archive policy, and optional BusyBox/dropbear staging.
- Later: Android/TWRP read-only network inventory for Wi-Fi firmware/driver research.

## Assumptions

- v93 is structural cleanup, not a new user-facing feature.
- Storage is boot-critical, so it gets its own version and flash validation rather than being bundled with netservice.
- `a90_storage` can print command output via `a90_console`, but it must not call shell dispatch, menu, HUD, or netservice directly.
- `/cache` remains the safe fallback root and SD remains the preferred workspace only after UUID/workspace/RW checks pass.
