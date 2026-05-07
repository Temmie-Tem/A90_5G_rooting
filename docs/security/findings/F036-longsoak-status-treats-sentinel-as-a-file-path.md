# F036. Longsoak status treats '-' sentinel as a file path

## Metadata

| field | value |
|---|---|
| finding_id | `c3087cc4db288191bc97dc60b5f442c1` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c3087cc4db288191bc97dc60b5f442c1 |
| severity | `low` |
| status | `planned-v153` |
| detected_at | `2026-05-07T19:33:34.577889Z` |
| committed_at | `2026-05-08 03:59:09 +0900` |
| commit_hash | `3c1dc516a2c9bf791cbce8fad08fa38c2ee008a1` |
| relevant_paths | `stage3/linux_init/a90_longsoak.c` <br> `stage3/linux_init/v147/60_shell_basic_commands.inc.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-07T20-00-44.982Z.csv` |

## CSV Description

`a90_longsoak_get_status()` initializes `out->path` to the display sentinel `"-"` when no recorder has been started, then still calls `longsoak_scan_file(out)`. `longsoak_scan_file()` only checks for an empty string, so it attempts `open("-", O_RDONLY)` in the current working directory. A local file, FIFO, or special file named `-` can corrupt status data or block the PID1 status path.

## Local Initial Assessment

- Valid class: display sentinel is reused as a path.
- Likely fix: keep internal path empty when no recorder exists, or make `longsoak_scan_file()` reject `"-"` and non-absolute paths.
- Related group: robustness/availability in longsoak status.

## Local Remediation

- Planned for v153 Longsoak Security Hardening.
- Treat `-` as display-only; reject empty, sentinel, and non-absolute paths before scan/tail/export file opens.

## Codex Cloud Detail

Longsoak status treats '-' sentinel as a file path
Link: https://chatgpt.com/codex/cloud/security/findings/c3087cc4db288191bc97dc60b5f442c1?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: low (attack path: low)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 3c1dc51
Author: shs02140@gmail.com
Created: 2026. 5. 8. 오전 4:33:34
Assignee: Unassigned
Signals: Validated, Attack-path

# Summary
An introduced robustness bug was found. The new longsoak status API should not scan the display placeholder path. It should either keep an internal empty path until longsoak_path is set, or have longsoak_scan_file() check the real longsoak_path state rather than the printable sentinel.
The commit adds a90_longsoak_get_status()/a90_longsoak_summary() and wires the summary into status and bootstatus. a90_longsoak_get_status() initializes out->path to the display sentinel "-" when no longsoak recorder has been started, but then calls longsoak_scan_file(out) regardless. longsoak_scan_file() only checks whether status->path[0] is NUL, so it attempts open("-", O_RDONLY) in the process current working directory. This can cause incorrect status data from an unrelated file named "-" and can hang the PID1 shell/status path if that relative path is a FIFO or other blocking special file. In the project threat model this is mainly a robustness/availability issue because creating or selecting such a file generally already requires trusted operator/root-shell control.

# Validation
## Rubric
- [x] Confirm the commit introduced/contains a no-recorder status path that sets the printable sentinel '-' before any real longsoak_path is set.
- [x] Confirm longsoak_scan_file() treats any non-empty status->path as a real filesystem path and opens it.
- [x] Dynamically reproduce incorrect status parsing from an unrelated regular file named '-' in the process current directory.
- [x] Dynamically reproduce availability impact by showing a FIFO named '-' causes the status call to block until killed by timeout.
- [x] Attempt crash/Valgrind/ASan/debugger validation before relying on code understanding: no crash expected; Valgrind unavailable; ASan reproduced behavior without memory diagnostics; lldb confirmed the open("-") call chain.
## Report
Validated the finding against commit 3c1dc516a2c9bf791cbce8fad08fa38c2ee008a1. The relevant code path is present: stage3/linux_init/a90_longsoak.c:153-167 initializes out->path to the printable sentinel "-" when longsoak_path is unset, then unconditionally calls longsoak_scan_file(out). stage3/linux_init/a90_longsoak.c:115-118 only skips scanning if status->path[0] is NUL, so "-" is treated as a real relative filesystem path and passed to open(status->path, O_RDONLY | O_CLOEXEC). The new summary is reachable from routine commands: stage3/linux_init/v147/60_shell_basic_commands.inc.c:159 calls a90_longsoak_summary() in status, and line 506 calls it in bootstatus.

I built a small debug harness that includes the real a90_longsoak.c with minimal stubs for unrelated init services. Baseline with no file named '-' produced: STATUS path=- samples=0 last=- seq=0 age=0ms session=-. With a regular cwd file named '-' containing fake JSONL, the same no-recorder status path produced: STATUS path=- samples=1 last=done seq=8 age=789ms session=- and SUMMARY running=no pid=-1 interval=0s samples=1 last=done seq=8 age=789ms session=-. This demonstrates incorrect status data sourced from an unrelated cwd file named '-'.

Direct availability reproduction with a FIFO named '-' showed the blocking behavior: `timeout 2s ../longsoak_poc/longsoak_status_poc` exited rc=124 with no output, consistent with blocking in open("-", O_RDONLY) waiting for a FIFO writer.

Valgrind was attempted but is not installed in the container (rc=127). An ASan build reproduced the regular-file status confusion and FIFO timeout with no memory-safety diagnostics, as expected for this robustness/availability bug.

Debugger validation used lldb on the debug harness. Breakpoint at a90_longsoak.c:118 stopped at `fd = open(status->path, O_RDONLY | O_CLOEXEC);`; `frame variable status->path` showed `(char[4096]) status->path = "-"...`. Backtrace showed the chain: longsoak_scan_file at a90_longsoak.c:118 <- a90_longsoak_get_status at a90_longsoak.c:167 <- main. This confirms the unintended open of the display sentinel.

# Evidence
stage3/linux_init/a90_longsoak.c (L110 to 123)
  Note: longsoak_scan_file() treats any non-empty status->path as a real filesystem path, so the '-' sentinel is opened relative to the current working directory.
```
static void longsoak_scan_file(struct a90_longsoak_status *status) {
    int fd;
    FILE *file;
    char line[768];

    if (status == NULL || status->path[0] == '\0') {
        return;
    }
    fd = open(status->path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return;
    }
    file = fdopen(fd, "r");
    if (file == NULL) {
```

stage3/linux_init/a90_longsoak.c (L149 to 168)
  Note: a90_longsoak_get_status() initializes out->path to the printable sentinel '-' when longsoak_path is empty, but then always calls longsoak_scan_file(out).
```
int a90_longsoak_get_status(struct a90_longsoak_status *out) {
    if (out == NULL) {
        return -EINVAL;
    }
    memset(out, 0, sizeof(*out));
    out->pid = -1;
    snprintf(out->session, sizeof(out->session), "-");
    snprintf(out->path, sizeof(out->path), "-");
    snprintf(out->last_type, sizeof(out->last_type), "-");
    out->running = longsoak_is_running();
    out->pid = a90_service_pid(A90_SERVICE_LONGSOAK);
    out->interval_sec = longsoak_interval_sec;
    if (longsoak_session[0] != '\0') {
        snprintf(out->session, sizeof(out->session), "%s", longsoak_session);
    }
    if (longsoak_path[0] != '\0') {
        snprintf(out->path, sizeof(out->path), "%s", longsoak_path);
    }
    longsoak_scan_file(out);
    return 0;
```

stage3/linux_init/v147/60_shell_basic_commands.inc.c (L139 to 172)
  Note: The new summary is invoked from the general status command, making the unintended '-' open reachable through routine status checks.
```
static void cmd_status(void) {
    struct a90_metrics_snapshot snapshot;
    char boot_summary[64];
    char selftest_summary[96];
    char pid1guard_summary[96];
    char helper_summary[128];
    char userland_summary[128];
    char exposure_summary[192];
    char longsoak_summary[192];
    struct a90_runtime_status runtime_status;
    struct a90_kms_info kms_info;
    struct a90_exposure_snapshot exposure;

    a90_metrics_read_snapshot(&snapshot);
    a90_timeline_boot_summary(boot_summary, sizeof(boot_summary));
    a90_selftest_summary(selftest_summary, sizeof(selftest_summary));
    refresh_pid1_guard();
    a90_pid1_guard_summary(pid1guard_summary, sizeof(pid1guard_summary));
    a90_helper_summary(helper_summary, sizeof(helper_summary));
    a90_userland_summary(userland_summary, sizeof(userland_summary));
    a90_longsoak_summary(longsoak_summary, sizeof(longsoak_summary));
    a90_runtime_get_status(&runtime_status);
    (void)a90_exposure_collect(&exposure);
    a90_exposure_summary(&exposure, exposure_summary, sizeof(exposure_summary));

    a90_console_printf("init: %s\r\n", INIT_BANNER);
    a90_console_printf("creator: %s\r\n", INIT_CREATOR);
    a90_console_printf("boot: %s\r\n", boot_summary);
    a90_console_printf("selftest: %s\r\n", selftest_summary);
    a90_console_printf("pid1guard: %s\r\n", pid1guard_summary);
    a90_console_printf("helpers: %s\r\n", helper_summary);
    a90_console_printf("userland: %s\r\n", userland_summary);
    a90_console_printf("exposure: %s\r\n", exposure_summary);
    a90_console_printf("longsoak: %s\r\n", longsoak_summary);
```

stage3/linux_init/v147/60_shell_basic_commands.inc.c (L488 to 516)
  Note: The new summary is also invoked from bootstatus, extending the same unintended file access to another routine status command.
```
static int cmd_bootstatus(void) {
    char summary[64];
    char selftest_summary[96];
    char pid1guard_summary[96];
    char helper_summary[128];
    char userland_summary[128];
    char exposure_summary[192];
    char longsoak_summary[192];
    struct a90_runtime_status runtime_status;
    struct a90_exposure_snapshot exposure;
    size_t count = a90_timeline_count();

    a90_timeline_boot_summary(summary, sizeof(summary));
    a90_selftest_summary(selftest_summary, sizeof(selftest_summary));
    refresh_pid1_guard();
    a90_pid1_guard_summary(pid1guard_summary, sizeof(pid1guard_summary));
    a90_helper_summary(helper_summary, sizeof(helper_summary));
    a90_userland_summary(userland_summary, sizeof(userland_summary));
    a90_longsoak_summary(longsoak_summary, sizeof(longsoak_summary));
    a90_runtime_get_status(&runtime_status);
    (void)a90_exposure_collect(&exposure);
    a90_exposure_summary(&exposure, exposure_summary, sizeof(exposure_summary));
    a90_console_printf("boot: %s\r\n", summary);
    a90_console_printf("selftest: %s\r\n", selftest_summary);
    a90_console_printf("pid1guard: %s\r\n", pid1guard_summary);
    a90_console_printf("helpers: %s\r\n", helper_summary);
    a90_console_printf("userland: %s\r\n", userland_summary);
    a90_console_printf("exposure: %s\r\n", exposure_summary);
    a90_console_printf("longsoak: %s\r\n", longsoak_summary);
```

# Attack-path analysis
Final: low | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The original low severity is appropriate. Static evidence confirms the code path and validation evidence confirms regular-file status confusion and FIFO blocking, so this is not a false positive. It is also in scope because it lives in the stage3/linux_init PID1 runtime and is reached by registered status/bootstatus commands. The severity does not rise above low because realistic exploitation requires already-trusted/root-equivalent device control or unusual CWD influence, and the impact is limited to local availability/status integrity rather than a security boundary bypass.
## Likelihood
low - The bug is easy to trigger once a suitable cwd file/FIFO named '-' exists, and status/bootstatus are routine commands. For an untrusted attacker in the stated threat model, however, creating or selecting that cwd object requires physical/control-channel/root-equivalent access or an unusual preexisting filesystem condition.
## Impact
low - The proven effects are misleading longsoak status values or a local hang in the status/bootstatus path if '-' is a FIFO. There is no demonstrated code execution, privilege escalation, secret disclosure, or cross-boundary access. An actor able to set up the exploit generally already has root-equivalent device control and can cause stronger effects through intended commands.
## Assumptions
- Analysis is limited to repository artifacts in /workspace/A90_5G_rooting; no device, cloud, or network APIs were queried.
- The project threat model is a lab device workflow where the native init shell/control channel is intended for a trusted operator with root-level device control.
- A realistic untrusted attacker would need physical/control-channel access or prior ability to influence PID1 current working directory contents to exploit this specific bug.
- longsoak_path has not been set by starting the longsoak recorder
- PID1/current working directory contains an attacker-influenced regular file or FIFO named '-'
- attacker can invoke the native init status or bootstatus command, typically via the trusted serial shell/control path
## Path
control-channel actor / prior CWD influence
  -> file or FIFO named '-' exists
  -> status or bootstatus
  -> a90_longsoak_get_status(): path='-'
  -> longsoak_scan_file(): open('-')
  -> fake status data or local status-path hang
## Path evidence
- `stage3/linux_init/a90_longsoak.c:24-26` - longsoak_path is static process state and is initially empty until the longsoak recorder is started.
- `stage3/linux_init/a90_longsoak.c:115-118` - longsoak_scan_file() only skips empty paths and then opens status->path as a filesystem path.
- `stage3/linux_init/a90_longsoak.c:153-167` - a90_longsoak_get_status() writes '-' into out->path when longsoak_path is unset and unconditionally scans it.
- `stage3/linux_init/v147/60_shell_basic_commands.inc.c:139-172` - The general status command calls a90_longsoak_summary(), making the unintended open reachable through normal status usage.
- `stage3/linux_init/v147/60_shell_basic_commands.inc.c:488-516` - bootstatus also calls a90_longsoak_summary(), providing a second routine reachability path.
- `stage3/linux_init/v147/80_shell_dispatch.inc.c:37-40` - The dispatcher maps the status command to cmd_status().
- `stage3/linux_init/v147/80_shell_dispatch.inc.c:81-85` - The dispatcher maps bootstatus to cmd_bootstatus().
- `stage3/linux_init/v147/80_shell_dispatch.inc.c:872-885` - status and bootstatus are registered as core shell commands.
## Narrative
The finding is real and reachable in the PID1 runtime: a90_longsoak_get_status() initializes out->path to '-' and then calls longsoak_scan_file(), whose only guard is that status->path is non-empty before open(status->path). status and bootstatus both call a90_longsoak_summary(), so routine status checks reach the bug. The validation evidence demonstrated fake status data from a cwd file named '-' and a timeout when '-' was a FIFO. Severity remains low because exploitation requires unusual filesystem/CWD influence or already-trusted root/control-channel access, and the proven impact is local status confusion or a hang, not privilege escalation, code execution, sensitive data disclosure, or cross-boundary compromise.
## Controls
- Default project model assumes a single trusted operator with physically controlled USB access.
- The serial TCP bridge is documented as localhost-bound by default, limiting remote exposure when defaults are used.
- The affected code parses status/log fields only; it does not execute file contents.
- Normal longsoak log paths are built from the runtime log directory after recorder start, but this control is bypassed when no recorder has started because '-' is used as an internal path sentinel.
## Blindspots
- Static analysis cannot confirm the exact PID1 current working directory or writable paths on a real flashed device.
- The validation harness used the real longsoak code but was not a full native-init boot session.
- Repository-only analysis cannot measure operational exposure from an operator binding serial bridges or network services beyond defaults.
