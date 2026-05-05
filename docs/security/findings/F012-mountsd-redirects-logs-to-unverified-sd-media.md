# F012. mountsd redirects logs to unverified SD media

## Metadata

| field | value |
|---|---|
| finding_id | `cded187dd8348191b117aea958fb7f57` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/cded187dd8348191b117aea958fb7f57 |
| severity | `medium` |
| status | `mitigated-v124` |
| detected_at | `2026-05-02T19:55:55.957098Z` |
| committed_at | `2026-05-03 00:01:12 +0900` |
| commit_hash | `b23f0d98ccee1ec713a7d44d90243a0c0801e622` |
| relevant_paths | `stage3/linux_init/a90_config.h | stage3/linux_init/a90_storage.c | stage3/linux_init/a90_log.c` |
| has_patch | `true` |

## Local Remediation

- v124 gates mountsd rw/init log redirection on expected SD UUID, identity marker, and RW probe; native log files are opened no-follow with 0600 mode.
- Report: `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md`

## CSV Description

The boot storage probe treats the SD card as trusted only after reading its UUID and comparing it to SD_EXPECTED_UUID; otherwise it falls back to /cache or /tmp. This commit adds a90_log_set_path(SD_NATIVE_LOG_PATH) to the interactive mountsd rw/init path, but that command path mounts mmcblk0p1 and redirects logging for any writable SD mount without checking the UUID or identity marker. An attacker who can provide or swap removable SD media can cause subsequent PID1 logs, command names, run paths, and child stdio routed to log append mode to be written to attacker-controlled storage once an operator runs mountsd rw or mountsd init. Because a90_log_set_path opens the path with normal open(O_CREAT|O_APPEND) and no O_NOFOLLOW/type validation, attacker-controlled ext4 contents can also use symlinks or special files to redirect root writes or hang logging/command handling. This is not remote code execution, but it weakens the storage trust/fallback boundary introduced for v93.

## Codex Cloud Detail

mountsd redirects logs to unverified SD media
Link: https://chatgpt.com/codex/cloud/security/findings/cded187dd8348191b117aea958fb7f57
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: b23f0d9
Author: shs02140@gmail.com
Created: 2026. 5. 3. 오전 4:55:55
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Security bug introduced. The parent version did not change the log path from the mountsd command; this commit added log redirection after writable SD mounts without carrying over the boot-time SD UUID validation.
The boot storage probe treats the SD card as trusted only after reading its UUID and comparing it to SD_EXPECTED_UUID; otherwise it falls back to /cache or /tmp. This commit adds a90_log_set_path(SD_NATIVE_LOG_PATH) to the interactive mountsd rw/init path, but that command path mounts mmcblk0p1 and redirects logging for any writable SD mount without checking the UUID or identity marker. An attacker who can provide or swap removable SD media can cause subsequent PID1 logs, command names, run paths, and child stdio routed to log append mode to be written to attacker-controlled storage once an operator runs mountsd rw or mountsd init. Because a90_log_set_path opens the path with normal open(O_CREAT|O_APPEND) and no O_NOFOLLOW/type validation, attacker-controlled ext4 contents can also use symlinks or special files to redirect root writes or hang logging/command handling. This is not remote code execution, but it weakens the storage trust/fallback boundary introduced for v93.

# Validation
## Rubric
- [x] Identify the intended SD trust boundary: `SD_EXPECTED_UUID` in config and boot probe UUID mismatch fallback in `a90_storage_probe_boot`.
- [x] Verify the suspected commit introduced writable `mountsd` log redirection by comparing the commit diff and confirming the new `a90_log_set_path(SD_NATIVE_LOG_PATH)` calls.
- [x] Dynamically exercise the real `a90_storage_cmd_mountsd` path with minimal hardware stubs and prove `mountsd rw` changes the log path without performing an additional UUID read.
- [x] Demonstrate impact by making attacker-controlled SD contents provide a symlinked logs directory and showing root log appends are written through that symlink.
- [x] Attempt compiled validation paths: direct PoC run succeeded; ASan/UBSan run succeeded with no crash expected; valgrind/gdb were unavailable; LLDB trace confirmed the vulnerable call chain.
## Report
Validated the finding as a logic/trust-boundary bug. Relevant source evidence: `stage3/linux_init/a90_config.h:34-41` defines the trusted SD UUID and `SD_NATIVE_LOG_PATH`; `stage3/linux_init/a90_storage.c:402-415` shows the boot probe reads the ext4 UUID and falls back on mismatch; `stage3/linux_init/a90_storage.c:627-650` shows `mountsd rw/init` mounts `mmcblk0p1` and calls `a90_log_set_path(SD_NATIVE_LOG_PATH)` without a UUID or identity-marker check; `stage3/linux_init/a90_log.c:38-50` opens the selected path with `O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC` and no `O_NOFOLLOW`/file-type validation. `git show` confirmed this commit added exactly the two `a90_log_set_path(SD_NATIVE_LOG_PATH)` calls in `a90_storage_cmd_mountsd`. I built a bounded C harness that compiles the real `a90_storage.c`, `a90_log.c`, and `a90_util.c`, stubbing only hardware boundaries (`mount`, `umount`, `mknod`, and `/sys/class/block/mmcblk0p1/dev`). The harness first exercises the boot probe with a fake mismatched UUID and gets fallback: `BOOT_PROBE rc=-116 fallback=yes expected=no warning='sd uuid mismatch; fallback /tmp' uuid='deadbeef-0011-2233-4455-66778899aabb' pread_count=1`. It then simulates attacker-controlled SD contents where `/mnt/sdext/a90/logs` is a symlink to `/tmp/a90_attacker_sink` and calls the actual `a90_storage_cmd_mountsd(["mountsd","rw"],2)`. Output shows `MOUNTSD_RW rc=0 log_path=/mnt/sdext/a90/logs/native-init.log ... uuid_preads_delta=0`, proving the command path redirected logging after a writable SD mount without another UUID read. A subsequent `a90_logf` created/appended `/tmp/a90_attacker_sink/native-init.log`, confirming symlink-following attacker-controlled log writes. ASan/UBSan run succeeded with the same output and no memory crash, as expected for this logic bug. Valgrind and gdb were not installed; LLDB was available and used non-interactively. The LLDB trace stopped at `a90_storage.c:640` with `flags = 0`, `mode = "rw"`, then stepped into `a90_log_set_path(path="/mnt/sdext/a90/logs/native-init.log")`, confirming the call chain from the interactive `mountsd rw` path.

# Evidence
stage3/linux_init/a90_config.h (L34 to 41)
  Note: Defines the SD device, mount point, expected UUID, and SD log path; the expected UUID is the trust policy that mountsd log redirection does not enforce.
```
#define SD_BLOCK_NAME "mmcblk0p1"
#define SD_MOUNT_POINT "/mnt/sdext"
#define SD_FS_TYPE "ext4"
#define SD_WORKSPACE_DIR "/mnt/sdext/a90"
#define SD_EXPECTED_UUID "c6c81408-f453-11e7-b42a-23a2c89f58bc"
#define SD_ID_FILE SD_WORKSPACE_DIR "/.a90-native-id"
#define SD_BOOT_RW_TEST_FILE SD_WORKSPACE_DIR "/tmp/.boot-rw-test"
#define SD_NATIVE_LOG_PATH SD_WORKSPACE_DIR "/logs/native-init.log"
```

stage3/linux_init/a90_log.c (L38 to 50)
  Note: a90_log_set_path opens and creates/appends to the requested path without O_NOFOLLOW or file-type checks, then makes it the active log target.
```
int a90_log_set_path(const char *path) {
    int fd;

    a90_log_rotate_if_needed(path);
    fd = open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0) {
        return -1;
    }
    close(fd);

    snprintf(log_path, sizeof(log_path), "%s", path);
    log_ready = true;
    return 0;
```

stage3/linux_init/a90_storage.c (L402 to 415)
  Note: Boot-time SD probing reads the ext4 UUID and falls back if it does not match SD_EXPECTED_UUID, showing the intended validation boundary.
```
    if (read_ext4_uuid(node_path, storage_state.sd_uuid, sizeof(storage_state.sd_uuid)) < 0) {
        int saved_errno = errno;

        storage_hook_line(hooks, ctx, 2, "[ SD     ] WARN UUID READ FAIL");
        storage_hook_frame(hooks, ctx);
        storage_use_cache(hooks, ctx, "sd uuid read failed", -saved_errno, saved_errno);
        return -saved_errno;
    }
    if (strcmp(storage_state.sd_uuid, SD_EXPECTED_UUID) != 0) {
        storage_state.sd_expected = false;
        storage_hook_line(hooks, ctx, 2, "[ SD     ] WARN UUID MISMATCH");
        storage_hook_frame(hooks, ctx);
        storage_use_cache(hooks, ctx, "sd uuid mismatch", -ESTALE, ESTALE);
        return -ESTALE;
```

stage3/linux_init/a90_storage.c (L627 to 650)
  Note: The introduced calls set the active log path to the SD workspace after any writable mountsd rw/init mount, with no UUID or identity-marker validation.
```
    if (mount(node_path, SD_MOUNT_POINT, SD_FS_TYPE, flags, NULL) < 0) {
        int saved_errno = errno;

        a90_console_printf("mountsd: mount %s on %s as %s: %s\r\n",
                node_path,
                SD_MOUNT_POINT,
                SD_FS_TYPE,
                strerror(saved_errno));
        return -saved_errno;
    }
    storage_state.sd_present = true;
    storage_state.sd_mounted = true;
    if ((flags & MS_RDONLY) == 0) {
        (void)a90_log_set_path(SD_NATIVE_LOG_PATH);
    }
    a90_console_printf("mountsd: %s ready (%s)\r\n",
            SD_MOUNT_POINT,
            flags & MS_RDONLY ? "ro" : "rw");
    if (strcmp(mode, "init") == 0) {
        rc = ensure_sd_workspace();
        if (rc < 0) {
            return rc;
        }
        (void)a90_log_set_path(SD_NATIVE_LOG_PATH);
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept as medium. Static evidence and validation show the bug is real and reachable in the documented latest v93 PID1 runtime: `mountsd` is registered in the shell dispatch, the handler mounts SD and calls `a90_log_set_path(SD_NATIVE_LOG_PATH)` for writable modes, and the log setter follows attacker-controlled filesystem objects with normal create/append semantics. The issue is not high or critical because the attack is non-remote, requires control of removable SD media and operator interaction, and the demonstrated impact is log disclosure plus limited root append/DoS rather than direct code execution, authentication bypass, or broad compromise. It is not low/ignore because the code explicitly intended to trust SD only after UUID/identity validation at boot, and the command path bypasses that boundary in an in-scope privileged runtime.
## Likelihood
low - Exploitation is plausible in the lab/device threat model but requires physical or supply-chain control of removable SD media plus operator interaction to run `mountsd rw` or `mountsd init`; there is no public network exposure for this path.
## Impact
medium - The main proven impact is confidentiality loss of native-init logs to attacker-controlled removable media and limited integrity/availability impact from root append opens through attacker-controlled symlinks or special-file targets. It does not directly grant RCE or broad remote compromise, but it weakens an explicit storage trust boundary in a privileged PID1 runtime.
## Assumptions
- The relevant deployed/runtime build is the documented latest verified v93 native init image/source.
- The attacker can provide, pre-stage, or swap removable SD media, but does not already have serial shell/root command access.
- The operator or automation later runs the normal interactive command `mountsd rw` or `mountsd init`.
- physical or supply-chain control of removable SD media contents
- device running the v93 native init runtime
- operator interaction or automation invoking `mountsd rw` or `mountsd init`
- subsequent PID1 logging or child stdio routed to the active native-init log
## Path
Attacker SD media -> operator `mountsd rw/init` -> unvalidated SD log path -> root PID1 append logging -> log disclosure / limited integrity or availability impact
## Path evidence
- `README.md:18-30` - Documents v93 as the latest verified source/image and states that logging uses SD when normal, otherwise `/cache`.
- `README.md:89-93` - Documents the runtime as a custom static `/init` PID 1 with a serial shell.
- `stage3/linux_init/a90_config.h:34-41` - Defines the SD block name, mount point, expected UUID, identity file, and SD native log path.
- `stage3/linux_init/a90_storage.c:402-415` - Boot-time SD probe reads the ext4 UUID and falls back when it does not match `SD_EXPECTED_UUID`.
- `stage3/linux_init/a90_storage.c:455-478` - Boot-time trusted SD selection also verifies the identity marker and write/read probe before using SD.
- `stage3/linux_init/a90_storage.c:571-626` - `mountsd` command mode parsing and mount setup do not perform a UUID or identity-marker check before writable mounting.
- `stage3/linux_init/a90_storage.c:627-650` - `mountsd rw/init` redirects active logging to the SD path after any writable mount, without the boot-time trust checks.
- `stage3/linux_init/a90_log.c:38-50` - The log setter opens the selected path with `O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC` and no `O_NOFOLLOW`, `lstat`, or regular-file validation.
- `stage3/linux_init/v93/80_shell_dispatch.inc.c:137-138` - The v93 shell handler calls `a90_storage_cmd_mountsd`.
- `stage3/linux_init/v93/80_shell_dispatch.inc.c:488-499` - The `mountsd [status|ro|rw|off|init]` command is registered in the normal v93 shell command table.
- `stage3/linux_init/v93/90_main.inc.c:116-178` - The runtime attaches the serial console and enters the interactive shell loop, making registered commands reachable in normal use.
## Narrative
This is a real in-scope security issue in the v93 native-init runtime. The boot-time SD path enforces a trust boundary by comparing the ext4 UUID to `SD_EXPECTED_UUID` and falling back on mismatch, but the interactive `mountsd rw/init` path mounts the SD device and redirects PID1 logging to `SD_NATIVE_LOG_PATH` without repeating that validation. The log setter then opens the path with normal append/create flags and no no-follow or file-type checks. Exploitation is constrained because it requires attacker control of removable SD contents plus operator interaction, and it does not directly provide remote code execution. The demonstrated impact is nevertheless security-relevant: logs can be redirected to attacker-controlled storage and root append writes can be steered through symlinks/special files, weakening the intended SD trust/fallback boundary.
## Controls
- Boot-time SD probe checks `SD_EXPECTED_UUID` and falls back to cache/tmp on UUID mismatch.
- Boot-time trusted SD path verifies an identity marker and write/read probe before selecting SD storage.
- `mountsd` mode parsing limits accepted modes to `status`, `ro`, `rw`, `off`, and `init`.
- The affected command is reachable through the device's serial/operator shell, not a public internet ingress.
- No authentication or authorization check is present specifically before `mountsd rw/init` log redirection.
- No `O_NOFOLLOW`, `lstat`, `fstat` regular-file check, or safe-directory open control protects the selected log path.
## Blindspots
- Static review did not execute on actual Samsung A90 hardware in this stage; runtime behavior relies partly on provided validation evidence.
- The exact sensitivity of logged commands/output depends on operator workflow and what child stdio is routed into native-init logs.
- The practical extent of symlink-based integrity impact depends on mounted filesystem permissions, existing target paths, and follow-on boot/service behavior.
- No cloud/IaC or external deployment manifests exist for this runtime, so exposure assessment is limited to repository code and documentation.
