# F025. World-readable fallback log leaks command activity to local users

## Metadata

| field | value |
|---|---|
| finding_id | `e7bb5e8149d081919c1598daf7c489f3` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/e7bb5e8149d081919c1598daf7c489f3 |
| severity | `low` |
| status | `new` |
| detected_at | `2026-04-28T09:21:03.859298Z` |
| committed_at | `2026-04-25 02:10:19 +0900` |
| commit_hash | `b363df8eb6ddabb59fca9dca3c1ae5c988f2fea0` |
| relevant_paths | `stage3/linux_init/init_v41.c` |
| has_patch | `false` |

## CSV Description

The new v41 logging layer writes boot/command logs to a fallback file at /tmp/native-init.log when /cache logging is unavailable. /tmp is mounted as mode 1777, and log files are created/opened with mode 0644. This makes the fallback log readable by any local user/process. Since the shell loop now logs command execution metadata (command name, rc, errno, duration), local actors can observe operator activity and system state transitions. This is an information disclosure issue introduced by the commit.

## Codex Cloud Detail

World-readable fallback log leaks command activity to local users
Link: https://chatgpt.com/codex/cloud/security/findings/e7bb5e8149d081919c1598daf7c489f3?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: low (attack path: low)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: b363df8
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:21:03
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: insecure log storage permissions for fallback logging path. The commit adds a new logging subsystem and command logging, but does not restrict file permissions for sensitive operational logs when using /tmp fallback.
The new v41 logging layer writes boot/command logs to a fallback file at /tmp/native-init.log when /cache logging is unavailable. /tmp is mounted as mode 1777, and log files are created/opened with mode 0644. This makes the fallback log readable by any local user/process. Since the shell loop now logs command execution metadata (command name, rc, errno, duration), local actors can observe operator activity and system state transitions. This is an information disclosure issue introduced by the commit.

# Validation
## Rubric
- [x] Confirm fallback logging path is `/tmp/native-init.log` and selected during boot startup (before cache success) (`init_v41.c:35-37, 4118-4138`).
- [x] Confirm file creation/write uses permissive mode `0644` in both path-selection and write paths (`init_v41.c:187`, `init_v41.c:239-243`).
- [x] Confirm `/tmp` is globally accessible context (`tmpfs mode=1777`) (`init_v41.c:2664`) and runtime `/tmp` is 1777.
- [x] Confirm logged content includes sensitive operational metadata (boot state + command telemetry) (`init_v41.c:4068-4094`, `4119-4138`).
- [x] Demonstrate practical disclosure: unprivileged user (`nobody`) can read `/tmp/native-init.log` created by init process (runtime evidence).
## Report
Rubric-driven validation completed on commit b363df8eb6ddabb59fca9dca3c1ae5c988f2fea0.

1) Crash/asan/valgrind/debugger attempts (required pre-checks):
- Built debug binary: `gcc -O0 -g -Wall -Wextra -o .validation/init_v41_dbg stage3/linux_init/init_v41.c`.
- Crash attempt: `timeout 5s .validation/init_v41_dbg` -> `EXIT:124` (no crash; process blocks in boot flow).
- ASan build/run also timed out (no memory crash observed).
- Valgrind unavailable: `bash: command not found: valgrind`.
- Debugger attempt (non-interactive): `lldb -b -o 'target create ...' -o 'process launch --stop-at-entry' -o bt -o quit` succeeded, stopped at entry (`signal SIGSTOP`), confirming executable launch but no crash path (this is an info-disclosure issue, not memory corruption).

2) Vulnerability reproduction (runtime evidence):
- Running init briefly created fallback log in /tmp.
- `/tmp` permissions: `1777 drwxrwxrwt /tmp`.
- Fallback log permissions: `644 root:root /tmp/native-init.log`.
- Log content includes operational boot metadata, e.g.:
  - `[...ms] boot: A90 Linux init v41 start`
  - `[...ms] boot: cache mount failed errno=2 error=No such file or directory log=/tmp/native-init.log`
- Unprivileged read confirmed:
  - `runuser -u nobody -- head -n 3 /tmp/native-init.log` successfully prints log lines.

3) Source confirmation (file:line):
- Fallback path defaults to `/tmp/native-init.log`: `stage3/linux_init/init_v41.c:35-37,47`.
- Log file create/open uses mode `0644` in selection path: `init_v41.c:183-195` (open at line 187).
- Re-open/write path also uses `0644`, with fallback retry: `init_v41.c:239-243`.
- `/tmp` mounted as tmpfs mode `1777`: `init_v41.c:2661-2664`.
- Boot starts by selecting fallback log before cache mount result: `init_v41.c:4118-4138`.
- Command logging records command metadata (`name`, `rc`, `errno`, `duration`, `flags`): `init_v41.c:4068-4094`.

4) Introduced by this commit:
- Parent commit does not contain `stage3/linux_init/init_v41.c` (new file added in b363df8...). The insecure logging behavior is therefore introduced with v41 logging subsystem.

Conclusion: finding is valid. Fallback log is world-readable (0644) in a world-accessible /tmp location, and contains sensitive operational metadata, enabling local information disclosure.

# Evidence
stage3/linux_init/init_v41.c (L187 to 195)
  Note: Creates/opens log file with mode 0644 in select_native_log_path, making logs broadly readable.
```
    fd = open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0) {
        return -1;
    }
    close(fd);

    snprintf(native_log_path, sizeof(native_log_path), "%s", path);
    native_log_ready = true;
    return 0;
```

stage3/linux_init/init_v41.c (L239 to 243)
  Note: Repeated log writes also open with mode 0644; fallback path is reused when primary fails.
```
    fd = open(native_log_path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0 && strcmp(native_log_path, NATIVE_LOG_FALLBACK) != 0) {
        native_log_select(NATIVE_LOG_FALLBACK);
        fd = open(native_log_path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    }
```

stage3/linux_init/init_v41.c (L2655 to 2664)
  Note: /tmp is mounted with mode 1777, so a 0644 fallback log there is readable by local users.
```
    ensure_dir("/tmp", 0755);
    ensure_dir("/cache", 0755);
    ensure_dir("/config", 0755);
    ensure_dir("/mnt", 0755);
    ensure_dir("/dev/block", 0755);

    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, "mode=0755");
    mount("tmpfs", "/tmp", "tmpfs", 0, "mode=1777");
```

stage3/linux_init/init_v41.c (L35 to 47)
  Note: Introduces persistent logging paths and defaults to the fallback /tmp/native-init.log path.
```
#define NATIVE_LOG_PRIMARY "/cache/native-init.log"
#define NATIVE_LOG_FALLBACK "/tmp/native-init.log"
#define NATIVE_LOG_MAX_BYTES (256 * 1024)

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif

static int console_fd = -1;
static pid_t adbd_pid = -1;
static pid_t hud_pid = -1;
static bool native_log_ready = false;
static char native_log_path[PATH_MAX] = NATIVE_LOG_FALLBACK;
```

stage3/linux_init/init_v41.c (L4068 to 4094)
  Note: New command logging records command metadata into the log, increasing sensitivity of leaked contents.
```
        native_logf("cmd", "start name=%s argc=%d flags=0x%x",
                    argv[0], argc, command->flags);

        if ((command->flags & CMD_DISPLAY) != 0) {
            stop_auto_hud(false);
        }

        errno = 0;
        started_ms = monotonic_millis();
        result = command->handler(argv, argc);
        duration_ms = monotonic_millis() - started_ms;
        if (duration_ms < 0) {
            duration_ms = 0;
        }

        if (result < 0) {
            result_errno = -result;
        } else {
            result_errno = 0;
        }
        save_last_result(argv[0], result, result_errno, duration_ms, command->flags);
        native_logf("cmd", "end name=%s rc=%d errno=%d duration=%ldms flags=0x%x",
                    argv[0],
                    result,
                    result_errno,
                    duration_ms,
                    command->flags);
```

stage3/linux_init/init_v41.c (L4119 to 4138)
  Note: Boot sequence selects fallback logging first and continues using it when cache mount fails.
```
    native_log_select(NATIVE_LOG_FALLBACK);
    native_logf("boot", "%s start", INIT_BANNER);
    native_logf("boot", "base mounts ready");
    klogf("<6>A90v41: base mounts ready\n");
    prepare_early_display_environment();
    native_logf("boot", "early display/input nodes prepared");
    klogf("<6>A90v41: early display/input nodes prepared\n");

    if (mount_cache() == 0) {
        native_log_select(NATIVE_LOG_PRIMARY);
        native_logf("boot", "%s start", INIT_BANNER);
        native_logf("boot", "base mounts ready");
        native_logf("boot", "early display/input nodes prepared");
        native_logf("boot", "cache mounted log=%s", native_log_current_path());
        mark_step("1_cache_ok_v41\n");
        klogf("<6>A90v41: cache mounted\n");
    } else {
        int saved_errno = errno;
        native_logf("boot", "cache mount failed errno=%d error=%s log=%s",
                    saved_errno, strerror(saved_errno), native_log_current_path());
```

# Attack-path analysis
Final: low | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
No change from original severity. The bug is real and reachable in active runtime code: root PID1 writes sensitive telemetry to a world-readable file in /tmp (0644 on 1777 tmpfs). However, attacker precondition is local foothold, and the impact is confined to confidentiality of operational metadata rather than credential theft, privilege escalation, or remote compromise. Probability and impact together fit low.
## Likelihood
low - Exploitation is trivial once a local foothold exists, but requires local on-device process/user access and is not internet-exposed; in default single-operator lab model this is less likely than remote attack classes.
## Impact
low - Leaks operational metadata (boot phases, command names, return/error/timing) to lower-privileged local actors; does not directly grant code execution, integrity modification, or availability loss.
## Assumptions
- v41 was an actively deployed runtime at this commit (README marks init_v41 as latest source/image).
- At least one non-root local process/user may exist on-device during operation (or be introduced in shared-lab usage).
- No additional mandatory access control policy is applied that blocks read access to world-readable files under /tmp.
- Ability to execute or control any local non-root process/user on the device
- Fallback logging path /tmp/native-init.log is selected (always at early boot, and retained if /cache mount fails)
## Path
N1 init_v41 boot
  -> N2 root creates /tmp/native-init.log (0644)
  -> N3 writes boot/cmd telemetry
  -> N4 local unprivileged read => information disclosure
## Path evidence
- `README.md:17-21` - Shows v41/init_v41.c was current active runtime and identifies control channel context.
- `stage3/linux_init/init_v41.c:35-37` - Defines primary and fallback log paths, including /tmp/native-init.log.
- `stage3/linux_init/init_v41.c:187-195` - select_native_log_path creates/opens log file with mode 0644.
- `stage3/linux_init/init_v41.c:239-243` - native_logf re-opens log with mode 0644 and retries fallback path.
- `stage3/linux_init/init_v41.c:2661-2664` - /tmp mounted as tmpfs mode=1777, enabling broad local readability of 0644 files.
- `stage3/linux_init/init_v41.c:4068-4094` - Command execution metadata written to log increases sensitivity of disclosed data.
- `stage3/linux_init/init_v41.c:4119-4138` - Boot flow selects fallback logging first and keeps it if cache mount fails.
## Narrative
The commit introduces v41 logging where PID1 writes to /tmp/native-init.log as fallback and opens the file with mode 0644. /tmp is mounted with mode 1777, so any local user/process can read the file. Logged content includes boot state and command execution metadata (name/rc/errno/duration), creating a real local information disclosure path. This is in-scope runtime code but impact is limited to local confidentiality leakage, supporting low severity.
## Controls
- Primary log location preference is /cache with fallback behavior
- Log file rotation limit (256 KiB)
- No effective confidentiality control on log file permissions (0644)
## Blindspots
- Static-only review cannot confirm actual production process/user model on device (whether non-root principals routinely exist).
- No runtime SELinux/AppArmor policy artifacts were evaluated; such policy could further constrain file reads.
- Current assessment targets commit-era v41 behavior and may differ from later init versions.
