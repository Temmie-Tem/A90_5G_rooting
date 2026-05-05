# F013. v79 SD probe enables symlink-based root file clobber

## Metadata

| field | value |
|---|---|
| finding_id | `8bc0e3443b248191b4ca5bc71fef0ab9` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/8bc0e3443b248191b4ca5bc71fef0ab9 |
| severity | `medium` |
| status | `mitigated-v124` |
| detected_at | `2026-04-28T17:44:45.169915Z` |
| committed_at | `2026-04-29 01:28:54 +0900` |
| commit_hash | `11bc9a01dcdb38a4dd593c704b32059295893839` |
| relevant_paths | `stage3/linux_init/init_v79.c` |
| has_patch | `true` |

## Local Remediation

- v124 mitigates the current shared runtime/storage probe class with no-follow writes; v79 remains historical source only.
- Report: `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md`

## CSV Description

In v79, PID1 now mounts SD and writes probe/identity/log files under /mnt/sdext/a90 during boot. These writes use open(... O_CREAT/O_TRUNC or O_APPEND ...) without O_NOFOLLOW and without validating path components via lstat. Because ensure_dir() treats EEXIST as success, pre-created symlinks in the SD workspace are accepted. The SD trust check is also weak: it relies on a static expected UUID and auto-creates the identity marker if missing (TOFU on untrusted media). An attacker who can provide a crafted SD with the expected UUID can cause root writes to symlink targets outside the SD mount (e.g., /cache/* or proc/sys nodes), causing integrity/availability impact; the moved log path to SD also increases plaintext command/output exposure on removable media.

## Codex Cloud Detail

v79 SD probe enables symlink-based root file clobber
Link: https://chatgpt.com/codex/cloud/security/findings/8bc0e3443b248191b4ca5bc71fef0ab9
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 11bc9a0
Author: shs02140@gmail.com
Created: 2026. 4. 29. 오전 2:44:45
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced security bug: unsafe boot-time writes/log redirection to attacker-controlled SD filesystem with symlink-following behavior and weak SD authenticity check.
In v79, PID1 now mounts SD and writes probe/identity/log files under /mnt/sdext/a90 during boot. These writes use open(... O_CREAT/O_TRUNC or O_APPEND ...) without O_NOFOLLOW and without validating path components via lstat. Because ensure_dir() treats EEXIST as success, pre-created symlinks in the SD workspace are accepted. The SD trust check is also weak: it relies on a static expected UUID and auto-creates the identity marker if missing (TOFU on untrusted media). An attacker who can provide a crafted SD with the expected UUID can cause root writes to symlink targets outside the SD mount (e.g., /cache/* or proc/sys nodes), causing integrity/availability impact; the moved log path to SD also increases plaintext command/output exposure on removable media.

# Validation
## Rubric
- [x] Confirm vulnerable primitives exist in changed code (open with O_TRUNC/O_APPEND without O_NOFOLLOW/lstat; ensure_dir EEXIST acceptance).
- [x] Demonstrate SD boot RW probe can clobber a symlink target outside intended workspace.
- [x] Demonstrate identity marker TOFU creation and symlink-following write behavior.
- [x] Demonstrate log-path redirection via symlinked workspace component accepted by ensure_dir.
- [x] Attempt compiled-stack validation sequence: crash attempt (no crash), valgrind/asan (valgrind unavailable, asan run), debugger trace proving execution chain.
## Report
I validated the finding as a real integrity/security issue (not a memory crash bug) in commit 11bc9a0 by compiling and executing code paths from init_v79.c.

What I checked in code (direct citations):
- Symlink-unsafe directory acceptance: ensure_dir() treats EEXIST as success without validating path type (stage3/linux_init/init_v79.c:200-203).
- Symlink-unsafe file write primitive: write_text_file_sync() uses open(path, O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC, 0644) with no O_NOFOLLOW/lstat checks (init_v79.c:9045-9047).
- Boot probe writes attacker-reachable fixed SD path: sd_write_read_probe() writes/reads/unlinks SD_BOOT_RW_TEST_FILE (init_v79.c:9115-9128).
- Identity TOFU behavior: ensure_sd_identity_marker() auto-creates marker on ENOENT (init_v79.c:9100-9106).
- Weak trust decision: SD is accepted via static UUID string comparison only (init_v79.c:9224-9232; constant at 65).
- Log redirection to SD + repeated open without symlink protection: select_native_log_path()/native_logf() open with O_CREAT|O_APPEND (init_v79.c:285-290, 341-344), and boot_storage_use_sd() switches logging to SD_NATIVE_LOG_PATH (init_v79.c:9184-9188).
- Boot-time reachability in PID1 path: boot_storage_probe() called from main (init_v79.c:11258).

Dynamic reproduction:
- Built init_v79.c debug object with static symbols exposed and linked PoC harness that directly invokes vulnerable functions from the real source.
- PoC output (/workspace/validation_artifacts/work/poc_harness.log):
  - [probe] rc=0 ... target_after='boot-rw-test 0.8.10 v79 ...'  => symlink target overwritten via sd_write_read_probe()/write_text_file_sync.
  - [id] rc=0 ... id_target_after='c6c81408-f453-11e7-b42a-23a2c89f58bc' => identity marker auto-created through symlinked path.
  - [ensure_dir] rc=0 errno=17 (symlink accepted) => EEXIST symlink accepted as directory success.
  - [log] ... outside_log='[...] poc: symlinked log write' => SD log path writes redirected outside via symlink.
- Debugger evidence (/workspace/validation_artifacts/work/lldb_trace.log): breakpoint at write_text_file_sync hit with path '/mnt/sdext/a90/tmp/.boot-rw-test', backtrace shows main -> sd_write_read_probe -> write_text_file_sync at init_v79.c:9046.

Method attempts per instruction:
- Crash attempt on built init binary in isolated mount namespace: timed out (exit 124), no crash (expected; issue is integrity clobber, not memory corruption).
- Valgrind attempt: unavailable in container (command not found).
- ASan attempt: executed; no memory errors, PoC behavior reproduced (consistent with non-memory bug).

Conclusion: finding is valid. The commit introduced boot-time root writes to SD workspace paths that follow symlinks and can be redirected, with weak SD authenticity (static UUID + TOFU marker creation).

# Evidence
stage3/linux_init/init_v79.c (L11258 to 11258)
  Note: boot_storage_probe() runs automatically at boot in PID1 context, making the issue pre-auth/early-boot reachable.
```
    boot_storage_probe();
```

stage3/linux_init/init_v79.c (L200 to 203)
  Note: ensure_dir() accepts EEXIST without checking if existing path is a directory, allowing symlink-based path substitution.
```
static int ensure_dir(const char *path, mode_t mode) {
    if (mkdir(path, mode) == 0 || errno == EEXIST) {
        return 0;
    }
```

stage3/linux_init/init_v79.c (L285 to 290)
  Note: select_native_log_path() opens target path with O_CREAT|O_APPEND and no O_NOFOLLOW/lstat validation.
```
static int select_native_log_path(const char *path) {
    int fd;

    rotate_native_log_if_needed(path);
    fd = open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0) {
```

stage3/linux_init/init_v79.c (L341 to 344)
  Note: native_logf() repeatedly opens the selected log path (potentially symlinked) as root.
```
    fd = open(native_log_path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0 && strcmp(native_log_path, NATIVE_LOG_FALLBACK) != 0) {
        native_log_select(NATIVE_LOG_FALLBACK);
        fd = open(native_log_path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
```

stage3/linux_init/init_v79.c (L65 to 68)
  Note: Introduces fixed expected UUID and SD-based identity/probe/log file locations on removable media.
```
#define SD_EXPECTED_UUID "c6c81408-f453-11e7-b42a-23a2c89f58bc"
#define SD_ID_FILE SD_WORKSPACE_DIR "/.a90-native-id"
#define SD_BOOT_RW_TEST_FILE SD_WORKSPACE_DIR "/tmp/.boot-rw-test"
#define SD_NATIVE_LOG_PATH SD_WORKSPACE_DIR "/logs/native-init.log"
```

stage3/linux_init/init_v79.c (L9045 to 9047)
  Note: write_text_file_sync() performs O_CREAT|O_TRUNC writes without symlink protections.
```
static int write_text_file_sync(const char *path, const char *value) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
```

stage3/linux_init/init_v79.c (L9100 to 9106)
  Note: Identity marker is auto-created when missing (TOFU), so attacker media with expected UUID can become trusted.
```
    saved_errno = errno;
    if (saved_errno != ENOENT) {
        errno = saved_errno;
        return -1;
    }
    if (write_text_file_sync(SD_ID_FILE, uuid) < 0) {
        return -1;
```

stage3/linux_init/init_v79.c (L9115 to 9128)
  Note: Boot RW probe writes and reads a fixed SD path under root privileges, enabling symlink-target file clobber.
```
    snprintf(payload,
             sizeof(payload),
             "boot-rw-test %s %s %ld",
             INIT_VERSION,
             INIT_BUILD,
             monotonic_millis());
    if (write_text_file_sync(SD_BOOT_RW_TEST_FILE, payload) < 0) {
        return -1;
    }
    sync();
    if (read_trimmed_text_file(SD_BOOT_RW_TEST_FILE, readback, sizeof(readback)) < 0) {
        return -1;
    }
    unlink(SD_BOOT_RW_TEST_FILE);
```

stage3/linux_init/init_v79.c (L9184 to 9188)
  Note: On successful probe, log path is switched to SD and timeline/log output is written there.
```
    if (select_native_log_path(SD_NATIVE_LOG_PATH) < 0 && cache_mount_ready) {
        native_log_select(NATIVE_LOG_PRIMARY);
    }
    timeline_replay_to_log("sd-storage");
    native_logf("storage", "sd main root=%s uuid=%s", boot_storage.root, boot_storage.sd_uuid);
```

stage3/linux_init/init_v79.c (L9224 to 9232)
  Note: SD trust decision is based on static UUID match only (not cryptographic authenticity).
```
    if (strcmp(boot_storage.sd_uuid, SD_EXPECTED_UUID) != 0) {
        boot_storage.sd_expected = false;
        boot_splash_set_line(2, "[ SD     ] WARN UUID MISMATCH");
        boot_auto_frame();
        boot_storage_use_cache("sd uuid mismatch", -ESTALE, ESTALE);
        return;
    }
    boot_storage.sd_expected = true;
    boot_splash_set_line(2, "[ SD     ] UUID OK");
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept at medium. The vulnerability is real, in the latest documented runtime, and has root-level integrity/availability impact through symlink-following writes in PID1. The validation evidence also demonstrates the vulnerable primitives. It does not warrant high/critical in this context because the attacker needs physical/removable-media access, the SD must be present at boot with the expected UUID, and the write contents are constrained to probe/UUID/log data rather than fully attacker-controlled executable payloads. Probability × impact therefore supports medium severity.
## Likelihood
low - Exploitation is straightforward once an attacker can provide the SD card: the expected UUID is hardcoded in the repository and ext4 symlinks can be pre-created. However, the path is not network-exposed and requires physical/removable-media access plus a reboot into v79.
## Impact
high - The vulnerable code executes as PID1/root and can truncate or append to attacker-selected symlink targets outside the intended SD workspace. This can corrupt root-owned files, break boot/runtime behavior, tamper with persistent state, or expose privileged logs on removable media. Content is partly fixed and not a fully controlled arbitrary write, limiting escalation certainty.
## Assumptions
- The v79 boot image/source is actually flashed and used on the target A90 device, as indicated by the repository README and v79 report.
- A realistic attacker can physically insert or replace the SD card before boot, or can otherwise supply the removable ext4 media used as /dev/block/mmcblk0p1.
- The attacker can prepare an ext4 filesystem with the repository-disclosed expected UUID and symlinks in the /a90 workspace.
- The vulnerable init process runs as PID1/root and has normal early-boot filesystem write privileges.
- Physical/removable-media access to supply or replace the SD card
- Device booting the v79 native init image
- SD card formatted as ext4 with the static expected UUID
- Crafted symlinks or symlinked path components under /mnt/sdext/a90
## Path
crafted SD -> UUID OK/TOFU -> PID1 boot probe -> symlinked /mnt/sdext/a90 paths -> root open(O_TRUNC/O_APPEND) -> file clobber/log exposure
## Path evidence
- `README.md:17-22` - Documents v79 as the latest verified build, source, and boot image, supporting in-scope deployment relevance.
- `stage3/linux_init/init_v79.c:61-68` - Defines the SD device, mount point, workspace, static expected UUID, and fixed identity/probe/log paths.
- `stage3/linux_init/init_v79.c:200-203` - ensure_dir() accepts EEXIST without validating that the existing object is a directory and not a symlink.
- `stage3/linux_init/init_v79.c:285-290` - select_native_log_path() opens the log path with O_CREAT|O_APPEND but no O_NOFOLLOW or symlink validation.
- `stage3/linux_init/init_v79.c:341-344` - native_logf() repeatedly opens the selected log path without symlink protections.
- `stage3/linux_init/init_v79.c:9045-9047` - write_text_file_sync() uses O_CREAT|O_TRUNC without O_NOFOLLOW, creating a root file-clobber primitive.
- `stage3/linux_init/init_v79.c:9065-9085` - SD workspace creation relies on ensure_dir() for attacker-controlled SD paths.
- `stage3/linux_init/init_v79.c:9100-9106` - Missing identity marker is auto-created, making the trust model TOFU on removable media.
- `stage3/linux_init/init_v79.c:9115-9128` - Boot read/write probe writes, syncs, reads, and unlinks a fixed SD path under root privileges.
- `stage3/linux_init/init_v79.c:9184-9188` - Successful SD probe redirects native log output to the SD workspace.
- `stage3/linux_init/init_v79.c:9224-9232` - The SD trust decision is only a static UUID string comparison.
- `stage3/linux_init/init_v79.c:9247-9254` - The boot path mounts the attacker-supplied SD ext4 filesystem read/write.
- `stage3/linux_init/init_v79.c:9269-9282` - After mounting, the boot path invokes identity marker creation and the SD write/read probe.
- `stage3/linux_init/init_v79.c:11256-11259` - boot_storage_probe() is called automatically during the v79 main boot path.
## Narrative
The finding is real and reachable in the repository's main runtime path. v79 is documented as the latest verified native init build, and boot_storage_probe() is called during main boot. The code mounts /dev/block/mmcblk0p1 as ext4, accepts it if a hardcoded UUID matches, initializes a missing identity marker, and then writes probe/id/log files under /mnt/sdext/a90. The write and append sinks use open() without O_NOFOLLOW or prior lstat/fstatat validation, and ensure_dir() treats EEXIST as success without checking that the object is actually a directory. A crafted SD card can therefore pre-place symlinks under the workspace so PID1/root writes affect targets outside the SD mount. The impact is meaningful root-level integrity/availability damage and log exposure, but the attack requires physical/removable-media access and a boot event, so medium severity is appropriate rather than high or critical.
## Controls
- SD fallback to /cache when block device is absent, UUID read fails, UUID mismatches, mount fails, workspace creation fails, identity marker fails, or probe fails
- Static expected UUID gate
- Physical/removable-media access required
- No cryptographic media authentication
- No symlink validation or O_NOFOLLOW on root write sinks
## Blindspots
- Static review did not test on a physical Galaxy A90 device in this stage.
- Exact set of practically clobberable target files depends on the live boot mount namespace, kernel behavior, SELinux state, and filesystem permissions.
- Repository docs indicate v79 is the latest verified image, but this stage did not independently inspect a deployed device.
- The validation PoC demonstrates the primitive, but real-world exploitability into persistence or code execution would require target-specific file choices and payload constraints.
