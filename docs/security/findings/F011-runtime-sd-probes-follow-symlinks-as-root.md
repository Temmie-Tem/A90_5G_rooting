# F011. Runtime SD probes follow symlinks as root

## Metadata

| field | value |
|---|---|
| finding_id | `1e3d3c36abf88191868b4bb217332756` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/1e3d3c36abf88191868b4bb217332756 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-04T10:30:16.719678Z` |
| committed_at | `2026-05-03 05:34:37 +0900` |
| commit_hash | `c60950b27aeba3148b6f88c55972b532ecb61cf8` |
| relevant_paths | `stage3/linux_init/a90_config.h | stage3/linux_init/v97/90_main.inc.c | stage3/linux_init/a90_runtime.c | stage3/linux_init/a90_util.c` |
| has_patch | `false` |

## CSV Description

The new v97 runtime initialization promotes the SD workspace to a runtime root and, during boot, writes `.runtime-rw-test` files in the `tmp`, `state`, and `run` subdirectories. Those paths are attacker-controllable if an attacker can prepare or replace the SD card contents. The code accepts pre-existing paths as directories via `ensure_dir()` and then opens the predictable probe filename with `O_CREAT | O_TRUNC` but without `O_NOFOLLOW` or `lstat`/directory ownership checks. A crafted SD filesystem can therefore place a symlink such as `/mnt/sdext/a90/state/.runtime-rw-test` pointing to another root-writable file or block device; PID1 will follow it and truncate/write the fixed probe payload during boot. This can corrupt critical files or partitions and can cause persistent device availability/integrity loss before the operator gets a shell.

## Codex Cloud Detail

Runtime SD probes follow symlinks as root
Link: https://chatgpt.com/codex/cloud/security/findings/1e3d3c36abf88191868b4bb217332756
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: c60950b
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:30:16
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
A security bug was introduced by the new runtime root initialization path. The commit adds automatic SD runtime probing with predictable filenames and symlink-following root writes.
The new v97 runtime initialization promotes the SD workspace to a runtime root and, during boot, writes `.runtime-rw-test` files in the `tmp`, `state`, and `run` subdirectories. Those paths are attacker-controllable if an attacker can prepare or replace the SD card contents. The code accepts pre-existing paths as directories via `ensure_dir()` and then opens the predictable probe filename with `O_CREAT | O_TRUNC` but without `O_NOFOLLOW` or `lstat`/directory ownership checks. A crafted SD filesystem can therefore place a symlink such as `/mnt/sdext/a90/state/.runtime-rw-test` pointing to another root-writable file or block device; PID1 will follow it and truncate/write the fixed probe payload during boot. This can corrupt critical files or partitions and can cause persistent device availability/integrity loss before the operator gets a shell.

# Validation
## Rubric
- [x] Confirm the commit introduced v97 runtime-root code and fixed SD runtime/probe path constants.
- [x] Confirm boot automatically calls a90_runtime_init() after storage probing and before operator intervention.
- [x] Confirm a90_runtime_init() selects /mnt/sdext/a90 when storage status indicates mounted, expected, writable SD.
- [x] Confirm runtime directory/probe handling lacks symlink defenses: ensure_dir() accepts EEXIST without lstat/S_ISDIR, and runtime_write_probe() opens a predictable .runtime-rw-test with O_CREAT|O_TRUNC and no O_NOFOLLOW.
- [x] Dynamically reproduce that a symlink at an SD-controlled probe path causes a separate root-owned victim file to be truncated/written with the fixed probe payload.
## Report
Validated. I first inspected the changed runtime path and built a small debug harness that calls the real a90_runtime_init() from stage3/linux_init/a90_runtime.c with storage status fields set to the SD-success condition. Direct crash attempt: the PoC does not crash, because this is a file-integrity logic bug, but it reliably corrupts the symlink target. Valgrind was attempted but is not installed; an ASan build ran without memory findings, as expected, while still reproducing the overwrite. Debugger validation used non-interactive LLDB because gdb is unavailable. Evidence: stage3/linux_init/a90_config.h:37-51 defines A90_RUNTIME_SD_ROOT=/mnt/sdext/a90 and fixed A90_RUNTIME_RW_TEST_NAME=.runtime-rw-test. stage3/linux_init/v97/90_main.inc.c:77-83 calls a90_runtime_init() automatically after storage probing. stage3/linux_init/a90_runtime.c:119-134 selects SD root when storage reports mounted/expected/rw. stage3/linux_init/a90_runtime.c:48-66 calls ensure_dir() on runtime dirs, and stage3/linux_init/a90_util.c:22-26 treats mkdir EEXIST as success without lstat/S_ISDIR validation. stage3/linux_init/a90_runtime.c:69-98 constructs dir/.runtime-rw-test and opens it with O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC, with no O_NOFOLLOW, then writes a90-runtime-ok and unlinks the pathname. stage3/linux_init/a90_runtime.c:180-182 runs this probe for tmp, state, and run. The PoC created /mnt/sdext/a90/state/.runtime-rw-test -> /tmp/a90_victim_state, where the victim was mode 0600 and initially contained SECRET_ROOT_ONLY_CONFIG_SHOULD_NOT_CHANGE. Running /workspace/validation_work/run_poc.sh produced: victim changed from 54 bytes to 15 bytes with content a90-runtime-ok, and the probe symlink was unlinked. LLDB stopped at a90_runtime.c:75 with dir=/mnt/sdext/a90/state and path=/mnt/sdext/a90/state/.runtime-rw-test immediately before the vulnerable open(); after continuing, /tmp/a90_victim_state was truncated/replaced with a90-runtime-ok. This confirms that a prepared SD runtime tree can make PID1/root follow a predictable final symlink and overwrite/truncate another root-writable target during boot.

# Evidence
stage3/linux_init/a90_config.h (L37 to 51)
  Note: Defines the SD workspace as the runtime root and uses a fixed `.runtime-rw-test` probe filename, making the target path predictable on attacker-preparable storage.
```
#define SD_WORKSPACE_DIR "/mnt/sdext/a90"
#define SD_EXPECTED_UUID "c6c81408-f453-11e7-b42a-23a2c89f58bc"
#define SD_ID_FILE SD_WORKSPACE_DIR "/.a90-native-id"
#define SD_BOOT_RW_TEST_FILE SD_WORKSPACE_DIR "/tmp/.boot-rw-test"
#define SD_NATIVE_LOG_PATH SD_WORKSPACE_DIR "/logs/native-init.log"
#define A90_RUNTIME_SD_ROOT SD_WORKSPACE_DIR
#define A90_RUNTIME_CACHE_ROOT "/cache/a90-runtime"
#define A90_RUNTIME_BIN_DIR "bin"
#define A90_RUNTIME_ETC_DIR "etc"
#define A90_RUNTIME_LOGS_DIR "logs"
#define A90_RUNTIME_TMP_DIR "tmp"
#define A90_RUNTIME_STATE_DIR "state"
#define A90_RUNTIME_PKG_DIR "pkg"
#define A90_RUNTIME_RUN_DIR "run"
#define A90_RUNTIME_RW_TEST_NAME ".runtime-rw-test"
```

stage3/linux_init/a90_runtime.c (L119 to 135)
  Note: Selects the SD workspace as the runtime root whenever storage reports the SD card mounted, expected, and writable.
```
int a90_runtime_init(const struct a90_storage_status *storage) {
    bool use_sd = storage != NULL &&
                  !storage->fallback &&
                  storage->sd_mounted &&
                  storage->sd_expected &&
                  storage->sd_rw_ok;
    int saved_errno = 0;

    memset(&runtime_state, 0, sizeof(runtime_state));
    runtime_state.initialized = true;
    runtime_state.fallback = !use_sd;
    snprintf(runtime_state.backend,
             sizeof(runtime_state.backend),
             "%s",
             use_sd ? "sd" : "cache");
    runtime_fill_paths(use_sd ? A90_RUNTIME_SD_ROOT : A90_RUNTIME_CACHE_ROOT);
```

stage3/linux_init/a90_runtime.c (L180 to 189)
  Note: Runs the unsafe write probe in three runtime directories, increasing the number of attacker-controlled symlink targets reached during boot.
```
    if (runtime_write_probe(runtime_state.tmp) < 0 ||
        runtime_write_probe(runtime_state.state) < 0 ||
        runtime_write_probe(runtime_state.run) < 0) {
        saved_errno = errno;
        if (use_sd) {
            runtime_set_failure("sd runtime rw probe failed", saved_errno);
            if (runtime_ensure_dirs() < 0 ||
                runtime_write_probe(runtime_state.tmp) < 0 ||
                runtime_write_probe(runtime_state.state) < 0 ||
                runtime_write_probe(runtime_state.run) < 0) {
```

stage3/linux_init/a90_runtime.c (L48 to 66)
  Note: Ensures runtime subdirectories but does not verify that pre-existing paths are real directories rather than symlinks or other objects.
```
static int runtime_ensure_dirs(void) {
    const char *dirs[] = {
        runtime_state.root,
        runtime_state.bin,
        runtime_state.etc,
        runtime_state.logs,
        runtime_state.tmp,
        runtime_state.state,
        runtime_state.pkg,
        runtime_state.run,
    };
    size_t index;

    for (index = 0; index < sizeof(dirs) / sizeof(dirs[0]); ++index) {
        if (ensure_dir(dirs[index], 0755) < 0) {
            return -1;
        }
    }
    return 0;
```

stage3/linux_init/a90_runtime.c (L69 to 98)
  Note: Builds the predictable probe path and opens it with `O_CREAT | O_TRUNC` without `O_NOFOLLOW`, so a final symlink is followed and the target is truncated/written as root.
```
static int runtime_write_probe(const char *dir) {
    char path[PATH_MAX];
    int fd;
    const char payload[] = "a90-runtime-ok\n";

    runtime_join_path(path, sizeof(path), dir, A90_RUNTIME_RW_TEST_NAME);
    fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (fd < 0) {
        return -1;
    }
    if (write_all_checked(fd, payload, strlen(payload)) < 0 ||
        fsync(fd) < 0) {
        int saved_errno = errno;

        close(fd);
        unlink(path);
        errno = saved_errno;
        return -1;
    }
    if (close(fd) < 0) {
        int saved_errno = errno;

        unlink(path);
        errno = saved_errno;
        return -1;
    }
    if (unlink(path) < 0) {
        return -1;
    }
    return 0;
```

stage3/linux_init/a90_util.c (L22 to 26)
  Note: The helper used by the new runtime directory setup treats any `EEXIST` as success without `lstat()`/`S_ISDIR` validation.
```
int ensure_dir(const char *path, mode_t mode) {
    if (mkdir(path, mode) == 0 || errno == EEXIST) {
        return 0;
    }
    return -1;
```

stage3/linux_init/v97/90_main.inc.c (L77 to 85)
  Note: Calls `a90_runtime_init()` automatically during boot immediately after storage probing, so the symlink-following writes occur before operator intervention.
```
    a90_storage_probe_boot(&storage_hooks, NULL);
    {
        struct a90_storage_status storage_status;
        int runtime_rc;

        if (a90_storage_get_status(&storage_status) == 0) {
            runtime_rc = a90_runtime_init(&storage_status);
        } else {
            runtime_rc = a90_runtime_init(NULL);
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The original medium severity is appropriate. Static evidence and executable validation support that the bug is real: a predictable probe file under attacker-preparable SD storage is opened by PID1/root with O_TRUNC and no O_NOFOLLOW after weak EEXIST directory handling. The attack is in scope because it affects the main v97 native init runtime. Impact is high for single-device integrity/availability because root can corrupt files or device nodes, but likelihood is reduced by physical/control-equivalent SD preparation, expected-UUID requirements, and the absence of direct arbitrary code execution, credential exposure, or remote reachability. Probability × impact therefore supports medium rather than high or critical.
## Likelihood
low - Exploitation is straightforward after SD-card control, but the required attacker position is constrained: the attacker must physically or operationally prepare/replace removable media with the expected UUID and have the device boot from that state. There is no internet or network exposure.
## Impact
high - PID1/root can be induced to truncate and write a fixed 15-byte payload to an attacker-selected symlink target that root can open. This can corrupt root-owned configuration, runtime state, helper binaries, or accessible block devices, causing meaningful integrity and availability damage. The payload is fixed and no direct arbitrary command execution or secret read is shown.
## Assumptions
- The v97 native init image is flashed and runs as PID 1/root on the target device.
- An attacker can prepare, replace, or otherwise control the ext4 SD card contents before boot.
- The crafted SD card can use the expected UUID c6c81408-f453-11e7-b42a-23a2c89f58bc.
- The target path chosen by the attacker exists, or can be created through symlink-following open semantics, and is writable by PID1/root at boot time.
- physical or control-equivalent access to prepare the SD filesystem
- device boots with the crafted SD card present
- SD block is discovered as mmcblk0p1
- SD UUID matches the hard-coded expected UUID
- SD mounts read-write and passes storage probing
## Path
Prepared SD card
  -> boot storage probe mounts /mnt/sdext RW
  -> a90_runtime_init uses /mnt/sdext/a90
  -> ensure_dir accepts existing attacker paths
  -> open(dir/.runtime-rw-test, O_TRUNC) follows symlink
  -> PID1/root corrupts target
## Path evidence
- `stage3/linux_init/a90_config.h:35-51` - Defines the SD mount/workspace paths and the fixed A90_RUNTIME_RW_TEST_NAME .runtime-rw-test used for predictable probe paths.
- `stage3/linux_init/v97/90_main.inc.c:77-85` - Calls a90_storage_probe_boot() and then a90_runtime_init() automatically during v97 boot.
- `stage3/linux_init/a90_storage.c:387-475` - Boot storage probing verifies the hard-coded SD UUID, mounts the SD filesystem read-write, ensures the workspace, performs an RW test, and sets sd_rw_ok before runtime initialization uses it.
- `stage3/linux_init/a90_runtime.c:119-135` - Selects the SD workspace as the runtime root whenever storage reports non-fallback, mounted, expected, and writable SD state.
- `stage3/linux_init/a90_runtime.c:48-66` - Ensures runtime directories under the selected root but delegates safety to ensure_dir() without symlink or ownership checks.
- `stage3/linux_init/a90_util.c:22-26` - ensure_dir() accepts any mkdir EEXIST result as success and does not lstat() or verify S_ISDIR.
- `stage3/linux_init/a90_runtime.c:69-98` - Builds dir/.runtime-rw-test and opens it with O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC but without O_NOFOLLOW, then writes a fixed payload.
- `stage3/linux_init/a90_runtime.c:180-189` - Runs the unsafe runtime write probe in tmp, state, and run, providing multiple attacker-preparable symlink locations.
## Narrative
The finding is valid and reachable in the v97 boot path. The code defines /mnt/sdext/a90 as the SD runtime root and uses a fixed .runtime-rw-test filename. During boot, storage probing mounts the expected SD card read-write and a90_runtime_init() selects the SD runtime root when sd_mounted, sd_expected, and sd_rw_ok are true. runtime_ensure_dirs() calls ensure_dir(), which treats mkdir EEXIST as success without proving the existing object is a safe directory. runtime_write_probe() then opens tmp/state/run/.runtime-rw-test with O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC and no O_NOFOLLOW, so a final symlink prepared on the SD filesystem is followed by PID1/root. Prior validation demonstrated the target file being truncated and replaced with the fixed payload. Severity remains medium: impact can be high for integrity/availability on a single device, but exploitation requires physical or equivalent SD-card control and does not directly provide arbitrary code execution or confidentiality loss.
## Controls
- Hard-coded SD UUID check before SD runtime selection
- SD card must mount read-write and pass an RW probe
- Fallback to cache/tmp on storage probe failure
- No authentication for physical removable-media preparation
- No lstat/fstatat ownership or type validation for pre-existing runtime paths
- No O_NOFOLLOW on privileged probe file open
## Blindspots
- Static-only review cannot confirm the exact target-device kernel symlink protections, mount options, and device-node availability at the precise boot moment.
- Repository artifacts do not prove how often operators deploy v97 with an inserted writable SD card.
- The review did not enumerate all possible high-value symlink targets on the live device filesystem.
- No cloud, CI, or external deployment manifests are present for broader fleet exposure assessment.
