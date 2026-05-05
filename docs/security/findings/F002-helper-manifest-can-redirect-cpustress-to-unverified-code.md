# F002. Helper manifest can redirect cpustress to unverified code

## Metadata

| field | value |
|---|---|
| finding_id | `61bf8ce0f45481918f8afef5505b3d5e` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/61bf8ce0f45481918f8afef5505b3d5e |
| severity | `high` |
| status | `new` |
| detected_at | `2026-05-04T10:30:04.837442Z` |
| committed_at | `2026-05-03 06:09:56 +0900` |
| commit_hash | `f3498d5bfd05bce4103b8b5aff9e6ff043fb5d2d` |
| relevant_paths | `stage3/linux_init/a90_helper.c | stage3/linux_init/v98/60_shell_basic_commands.inc.c | stage3/linux_init/a90_run.c` |
| has_patch | `false` |

## CSV Description

v98 adds a helper manifest under the runtime package directory and changes the shell cpustress command to execute the helper path returned by a90_helper_preferred_path(). Manifest entries can overwrite the default a90_cpustress path. During finalization, any regular executable at the manifest path becomes the preferred helper before mode, size, or SHA validation is enforced. SHA-256 values are explicitly marked as unchecked and only produce a warning. As a result, an attacker who can plant or modify the runtime helper package on the SD/cache runtime root can cause a later operator-initiated cpustress command to execute an arbitrary binary as PID1/root. The fallback ramdisk helper should be used unless the runtime helper has been authenticated, or warnings/failures should prevent preferred selection and execution.

## Codex Cloud Detail

Helper manifest can redirect cpustress to unverified code
Link: https://chatgpt.com/codex/cloud/security/findings/61bf8ce0f45481918f8afef5505b3d5e
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: f3498d5
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:30:04
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced: a new trust-on-first-use helper manifest is used to select executable helper paths, but the integrity fields in the manifest are not enforced before execution.
v98 adds a helper manifest under the runtime package directory and changes the shell cpustress command to execute the helper path returned by a90_helper_preferred_path(). Manifest entries can overwrite the default a90_cpustress path. During finalization, any regular executable at the manifest path becomes the preferred helper before mode, size, or SHA validation is enforced. SHA-256 values are explicitly marked as unchecked and only produce a warning. As a result, an attacker who can plant or modify the runtime helper package on the SD/cache runtime root can cause a later operator-initiated cpustress command to execute an arbitrary binary as PID1/root. The fallback ramdisk helper should be used unless the runtime helper has been authenticated, or warnings/failures should prevent preferred selection and execution.

# Validation
## Rubric
- [x] Confirm manifest location/runtime package is loaded by helper scan.
- [x] Confirm manifest parsing can overwrite the default a90_cpustress helper path.
- [x] Confirm helper finalization selects a regular executable as preferred before enforcing mode/size/sha integrity.
- [x] Confirm warnings/unchecked hash do not prevent a90_helper_preferred_path from returning the manifest path.
- [x] Confirm the returned preferred path flows into a90_run_spawn/execve and executes attacker-controlled code.
## Report
Validated the finding. The relevant code path is present: stage3/linux_init/a90_helper.c:171-203 parses manifest lines and overwrites the helper entry path and expected_sha256; a90_helper.c:240-253 marks any regular executable manifest path as preferred before enforcing integrity; a90_helper.c:292-296 only warns that sha256 is unchecked; a90_helper.c:372-378 returns preferred even with warnings; stage3/linux_init/v98/60_shell_basic_commands.inc.c:191-237 uses a90_helper_preferred_path("a90_cpustress", CPUSTRESS_HELPER); stage3/linux_init/a90_run.c:115-119 passes config->argv[0] directly to execve. I built a bounded harness using the real a90_helper.c, a90_run.c, and a90_util.c with minimal runtime/console/log stubs. The harness plants /tmp/a90-runtime-poc-direct/pkg/helpers.manifest containing an a90_cpustress entry pointing to /tmp/a90-runtime-poc-direct/evil_cpustress with bogus sha256 ffff..., then calls a90_helper_scan(), a90_helper_preferred_path(), and a90_run_spawn(). Direct reproduction output showed: entry.path=/tmp/a90-runtime-poc-direct/evil_cpustress; entry.preferred=/tmp/a90-runtime-poc-direct/evil_cpustress; entry.executable=yes; entry.hash_checked=no; entry.hash_match=no; entry.actual_sha256=unchecked; entry.warning=sha256 present but device-side hash unchecked; preferred_returned=/tmp/a90-runtime-poc-direct/evil_cpustress; spawn_rc=0; child exit=42; marker=executed as uid=0 argv=1,1. The actual evil helper sha256 was 002f15ea98794fd713aa5577ceab8775582a49c20ffbb476e534bbafca93922e, proving it did not match the manifest ffff... value. Crash attempt: direct execution did not crash, as expected for this semantic arbitrary-exec bug, but it reproduced attacker-controlled execution. Valgrind was attempted but not installed. An ASan-instrumented build also reproduced the same execution flow. Debugger validation with lldb set breakpoints at a90_helper_preferred_path and a90_run_spawn; lldb showed a90_helper_preferred_path(name="a90_cpustress", fallback="/bin/a90_cpustress") and later config->argv[0] = "/tmp/a90-runtime-poc-lldb/evil_cpustress" inside a90_run_spawn before execution, followed by marker=executed as uid=0 argv=1,1. This confirms the suspected trust-on-first-use manifest bypass and arbitrary helper execution path.

# Evidence
stage3/linux_init/a90_helper.c (L171 to 203)
  Note: Manifest parsing accepts a caller-controlled path and expected SHA-256, then overwrites the helper entry path with the manifest value.
```
    fields = sscanf(cursor,
                    "%63s %4095s %63s %15s %64s %31s %31s",
                    name,
                    path,
                    role,
                    required,
                    sha,
                    mode_text,
                    size_text);
    if (fields < 2) {
        return;
    }

    entry = helper_find_mutable(name);
    if (entry == NULL) {
        entry = helper_add(name, fields >= 3 ? role : "manifest", NULL);
    }
    if (entry == NULL) {
        return;
    }

    snprintf(entry->path, sizeof(entry->path), "%s", path);
    if (fields >= 3 && role[0] != '\0') {
        snprintf(entry->role, sizeof(entry->role), "%s", role);
    }
    if (fields >= 4) {
        entry->required = strcmp(required, "yes") == 0 ||
                          strcmp(required, "required") == 0 ||
                          strcmp(required, "1") == 0;
    }
    if (fields >= 5 && strcmp(sha, "-") != 0 && strcmp(sha, "none") != 0) {
        snprintf(entry->expected_sha256, sizeof(entry->expected_sha256), "%s", sha);
    }
```

stage3/linux_init/a90_helper.c (L240 to 253)
  Note: A manifest helper becomes preferred solely because it is a regular executable; no hash validation is required before selection.
```
    entry->present = helper_stat_regular(entry->path, &mode, &size);
    entry->actual_mode = entry->present ? mode : 0;
    entry->actual_size = entry->present ? size : 0;
    entry->executable = entry->present && ((mode & 0111) != 0);
    entry->fallback_present = helper_is_executable(entry->fallback);
    entry->hash_checked = false;
    entry->hash_match = entry->expected_sha256[0] == '\0';
    snprintf(entry->actual_sha256,
             sizeof(entry->actual_sha256),
             "%s",
             entry->expected_sha256[0] != '\0' ? "unchecked" : "-");

    if (entry->executable) {
        snprintf(entry->preferred, sizeof(entry->preferred), "%s", entry->path);
```

stage3/linux_init/a90_helper.c (L292 to 296)
  Note: Declared SHA-256 values are explicitly not checked and only produce a warning.
```
    if (entry->manifest_entry && entry->expected_sha256[0] != '\0') {
        snprintf(entry->warning,
                 sizeof(entry->warning),
                 "sha256 present but device-side hash unchecked");
        ++helper_warn_count;
```

stage3/linux_init/a90_helper.c (L372 to 378)
  Note: The preferred path is returned to callers even if the helper entry has warnings or an unchecked hash.
```
const char *a90_helper_preferred_path(const char *name, const char *fallback) {
    static char selected[PATH_MAX];
    struct a90_helper_entry entry;

    if (a90_helper_find(name, &entry) == 0 && entry.preferred[0] != '\0') {
        snprintf(selected, sizeof(selected), "%s", entry.preferred);
        return selected;
```

stage3/linux_init/a90_run.c (L115 to 119)
  Note: The selected helper path is passed directly to execve, so a malicious preferred path becomes root code execution.
```
        apply_stdio(config);
        execve(config->argv[0], config->argv, envp);
        dprintf(STDERR_FILENO, "%s: execve(%s): %s\n",
                tag, config->argv[0], strerror(errno));
        _exit(127);
```

stage3/linux_init/v98/60_shell_basic_commands.inc.c (L191 to 237)
  Note: cpustress now executes the helper API's preferred path instead of the fixed ramdisk helper.
```
static int cmd_cpustress(char **argv, int argc) {
    long seconds = 10;
    long workers_long = 4;
    char seconds_arg[16];
    char workers_arg[16];
    const char *helper_path = a90_helper_preferred_path("a90_cpustress", CPUSTRESS_HELPER);
    char *const child_argv[] = {
        (char *)helper_path,
        seconds_arg,
        workers_arg,
        NULL
    };
    struct a90_run_config config = {
        .tag = "cpustress",
        .argv = child_argv,
        .stdio_mode = A90_RUN_STDIO_CONSOLE,
        .setsid = true,
        .ignore_hup_pipe = true,
        .kill_process_group = true,
        .cancelable = true,
        .stop_timeout_ms = 2000,
    };
    struct a90_run_result result;
    pid_t pid;
    int rc;

    if (argc > 1) {
        seconds = strtol(argv[1], NULL, 10);
    }
    if (argc > 2) {
        workers_long = strtol(argv[2], NULL, 10);
    }
    if (argc > 3 || seconds < 1 || seconds > 120 || workers_long < 1 || workers_long > 16) {
        a90_console_printf("usage: cpustress [sec 1-120] [workers 1-16]\r\n");
        return -EINVAL;
    }

    snprintf(seconds_arg, sizeof(seconds_arg), "%ld", seconds);
    snprintf(workers_arg, sizeof(workers_arg), "%ld", workers_long);
    config.timeout_ms = (int)(seconds * 1000L + 3000L);

    a90_console_printf("cpustress: helper=%s workers=%ld sec=%ld, q/Ctrl-C cancels\r\n",
            helper_path,
            workers_long,
            seconds);

    rc = a90_run_spawn(&config, &pid);
```

Proposed patch:
diff --git a/stage3/linux_init/a90_helper.c b/stage3/linux_init/a90_helper.c
index 68ead90148621d38ea3b3d95132769406b51aa4a..d488a1aa1fb7909fd53e508594926d720eb73a50 100644
--- a/stage3/linux_init/a90_helper.c
+++ b/stage3/linux_init/a90_helper.c
@@ -229,94 +229,95 @@ static void helper_load_manifest(void) {
             *newline = '\0';
         }
         helper_apply_manifest_line(line);
     }
     fclose(fp);
 }

 static void helper_finalize_entry(struct a90_helper_entry *entry) {
     unsigned int mode = 0;
     long long size = 0;
     bool mode_bad = false;
     bool size_bad = false;

     entry->present = helper_stat_regular(entry->path, &mode, &size);
     entry->actual_mode = entry->present ? mode : 0;
     entry->actual_size = entry->present ? size : 0;
     entry->executable = entry->present && ((mode & 0111) != 0);
     entry->fallback_present = helper_is_executable(entry->fallback);
     entry->hash_checked = false;
     entry->hash_match = entry->expected_sha256[0] == '\0';
     snprintf(entry->actual_sha256,
              sizeof(entry->actual_sha256),
              "%s",
              entry->expected_sha256[0] != '\0' ? "unchecked" : "-");

-    if (entry->executable) {
+    if (entry->executable &&
+        (!entry->manifest_entry || entry->expected_sha256[0] == '\0')) {
         snprintf(entry->preferred, sizeof(entry->preferred), "%s", entry->path);
     } else if (entry->fallback_present) {
         snprintf(entry->preferred, sizeof(entry->preferred), "%s", entry->fallback);
     } else {
         entry->preferred[0] = '\0';
     }

     if (entry->present && entry->expected_mode != 0 &&
         entry->actual_mode != entry->expected_mode) {
         mode_bad = true;
     }
     if (entry->present && entry->expected_size > 0 &&
         entry->actual_size != entry->expected_size) {
         size_bad = true;
     }

     if (entry->required && !entry->executable) {
         snprintf(entry->warning, sizeof(entry->warning), "required helper missing or not executable");
         ++helper_fail_count;
         return;
     }
     if (mode_bad) {
         snprintf(entry->warning,
                  sizeof(entry->warning),
                  "mode mismatch expected=%04o actual=%04o",
                  entry->expected_mode,
                  entry->actual_mode);
         ++helper_warn_count;
         return;
     }
     if (size_bad) {
         snprintf(entry->warning,
                  sizeof(entry->warning),
                  "size mismatch expected=%lld actual=%lld",
                  entry->expected_size,
                  entry->actual_size);
         ++helper_warn_count;
         return;
     }
     if (entry->manifest_entry && entry->expected_sha256[0] != '\0') {
         snprintf(entry->warning,
                  sizeof(entry->warning),
-                 "sha256 present but device-side hash unchecked");
+                 "sha256 present but unchecked; using fallback helper");
         ++helper_warn_count;
     }
 }

 int a90_helper_scan(void) {
     int index;

     memset(helper_entries, 0, sizeof(helper_entries));
     helper_count = 0;
     helper_warn_count = 0;
     helper_fail_count = 0;
     helper_scanned = true;
     helper_add_defaults();
     helper_set_manifest_path();
     helper_load_manifest();

     for (index = 0; index < helper_count; ++index) {
         helper_finalize_entry(&helper_entries[index]);
     }

     snprintf(helper_summary_text,
              sizeof(helper_summary_text),
              "helpers: entries=%d warn=%d fail=%d manifest=%s path=%s",
              helper_count,
              helper_warn_count,

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept as high. Static evidence and executable validation confirm that manifest-controlled input reaches execve through normal cpustress use, and the validation showed a bogus-hash helper executing as uid 0. The affected component is in-scope PID1 runtime code, and the runtime SD/cache helper package is an explicit trust boundary in the project threat model. The issue is not critical because it is not public/remote by itself and needs local artifact-write capability plus operator interaction, but the resulting root/PID1-context arbitrary code execution justifies high severity.
## Likelihood
medium - The vulnerable path is part of normal v98 boot/helper inventory and cpustress operation, but exploitation is not remotely reachable by default. It requires the attacker to influence SD/cache runtime package contents and requires a later cpustress invocation or equivalent automation.
## Impact
high - Successful exploitation executes an attacker-selected binary from the runtime helper package as a child of PID1 with device root privileges, allowing full device integrity, confidentiality, and availability compromise in the native-init environment.
## Assumptions
- The v98 native init image is an in-scope runtime artifact that may be flashed and used as PID1 on the device.
- An attacker can supply or modify the selected runtime helper package on the SD/cache runtime root before boot/helper scan, or can cause a rescan/reboot after modifying it.
- The attacker can place a regular executable at the manifest-selected path, or can point the manifest to an attacker-controlled executable already present on writable runtime storage.
- A trusted operator or automation later invokes the normal cpustress shell command.
- The native init process and spawned helpers run with device root/PID1 privileges.
- Ability to write or supply helpers.manifest under the selected runtime pkg directory
- Ability to make the manifest path reference a regular executable
- Manifest is loaded during boot/helper scan, or a later rescan/reboot occurs
- Operator or automation invokes cpustress
## Path
Attacker runtime files
  -> helpers.manifest: a90_cpustress /attacker/path ... sha256
  -> a90_helper_scan: preferred=/attacker/path despite sha=unchecked
  -> operator: cpustress
  -> a90_run_spawn/execve(/attacker/path)
  -> root code execution on device
## Path evidence
- `stage3/linux_init/a90_runtime.c:119-124` - Runtime root selection can use the SD-backed runtime when mounted, expected, and writable.
- `stage3/linux_init/v98/90_main.inc.c:82-93` - v98 initializes the runtime root during PID1 boot and reports SD/cache runtime readiness.
- `stage3/linux_init/a90_helper.c:171-203` - Manifest parsing accepts name, path, role, required flag, and SHA-256, then overwrites the helper entry path with the manifest value.
- `stage3/linux_init/a90_helper.c:240-253` - Finalization marks a manifest path as present/executable and immediately chooses it as preferred before any cryptographic verification.
- `stage3/linux_init/a90_helper.c:292-296` - Declared SHA-256 values are not checked; they only produce a warning that the hash is unchecked.
- `stage3/linux_init/a90_helper.c:372-379` - Callers receive the preferred path without checking whether the helper has warnings or an unchecked hash.
- `stage3/linux_init/v98/60_shell_basic_commands.inc.c:191-237` - The normal cpustress command resolves a90_cpustress through a90_helper_preferred_path and passes it into the run configuration.
- `stage3/linux_init/a90_run.c:115-119` - The selected helper path is passed directly to execve as config->argv[0].
- `docs/reports/NATIVE_INIT_V98_HELPER_DEPLOY_2026-05-03.md:39-47` - Project documentation confirms the manifest policy and states that device-side SHA-256 is intentionally not implemented in v98.
## Narrative
The finding is real and reachable in the v98 PID1 runtime. The helper manifest parser accepts a manifest-supplied path and SHA-256, but finalization sets any regular executable at that path as preferred while explicitly leaving hash_checked=false and reporting SHA as unchecked. a90_helper_preferred_path returns that preferred value without considering the warning. The normal cpustress shell command uses that API, and a90_run_spawn directly execve()s config->argv[0]. The validation evidence also demonstrated an attacker-controlled helper with a bogus SHA running as uid 0. This is not remotely exposed by itself and requires runtime-package write capability plus operator invocation, so it is not critical, but root code execution from an unverified helper package is still high impact in the project’s stated artifact-boundary threat model.
## Controls
- No public ingress or load balancer is involved for this issue.
- Runtime helper deployment is optional and missing manifest is allowed.
- Ramdisk fallback exists but is bypassed whenever the manifest path is a regular executable.
- Mode and size mismatches create warnings, but preferred selection happens before those warnings block execution.
- SHA-256 is reported as unchecked and is not an execution gate.
- Operator action is required to invoke cpustress unless automation does so.
## Blindspots
- Static review cannot prove how often operators deploy helpers from untrusted SD/cache package sources in real environments.
- Static review cannot verify actual filesystem ownership and mount options for /mnt/sdext/a90 or /cache/a90-runtime on target devices.
- If an attacker must already have root shell access to write the runtime package in a specific deployment, the practical severity would be lower for that deployment.
- The validation harness demonstrated the semantic execution path, but not on physical hardware from removable storage.
