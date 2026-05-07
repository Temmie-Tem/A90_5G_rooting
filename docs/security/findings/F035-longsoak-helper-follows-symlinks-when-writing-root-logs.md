# F035. Longsoak helper follows symlinks when writing root logs

## Metadata

| field | value |
|---|---|
| finding_id | `deda7ea8fddc819199ff9c177b193dac` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/deda7ea8fddc819199ff9c177b193dac |
| severity | `medium` |
| status | `planned-v153` |
| detected_at | `2026-05-07T19:32:21.020967Z` |
| committed_at | `2026-05-08 03:51:56 +0900` |
| commit_hash | `54a9077cc7bc789069f064586af5aeb79745b1ca` |
| relevant_paths | `stage3/linux_init/a90_longsoak.c` <br> `stage3/linux_init/helpers/a90_longsoak.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-07T20-00-44.982Z.csv` |

## CSV Description

`/bin/a90_longsoak` is spawned by PID1/root and receives a recorder path under the runtime log directory. The helper defines `O_NOFOLLOW` but opens output with `fopen(path, "a")`, then calls `chmod(path, 0600)`. Both follow symlinks. A malicious persistent/log filesystem or attacker-controlled log directory can redirect root appends and permission changes to another file or device node.

## Local Initial Assessment

- Valid class: privileged helper follows symlinks for a persistent runtime path.
- Likely fix: use `open(..., O_NOFOLLOW | O_CREAT | O_APPEND | O_CLOEXEC, 0600)`, validate with `fstat()` as regular file, then `fdopen()` and `fchmod()` the opened fd.
- Related group: writable runtime trust and helper file writes.

## Local Remediation

- Planned for v153 Longsoak Security Hardening.
- Replace helper `fopen(path, "a")` and path-based `chmod()` with no-follow `open()`, `fstat()` regular-file validation, `fdopen()`, and `fchmod()`.

## Codex Cloud Detail

Longsoak helper follows symlinks when writing root logs
Link: https://chatgpt.com/codex/cloud/security/findings/deda7ea8fddc819199ff9c177b193dac?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 54a9077
Author: shs02140@gmail.com
Created: 2026. 5. 8. 오전 4:32:21
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: the new longsoak helper performs privileged append and chmod operations on a path without symlink protection.
v146 introduces /bin/a90_longsoak as a helper spawned by PID1/root. PID1 constructs the recorder path under the runtime log directory, commonly /mnt/sdext/a90/logs or /cache/a90-runtime/logs, and passes it to the helper. The helper defines O_NOFOLLOW but does not use it for the output file; instead it calls fopen(path, "a") followed by chmod(path, 0600). Both operations follow symlinks. A malicious persistent/log filesystem, or an attacker with the ability to write in that log directory before or during longsoak startup, can redirect the root helper’s appends and permission change to another file or device node. The generated filename includes monotonic time, so exploitation may require a race or symlink spraying, but the operation is still unsafe for a privileged recorder handling paths in persistent storage. The output should be opened with open(..., O_NOFOLLOW | O_CREAT | O_APPEND | O_CLOEXEC, 0600), validated as a regular file with fstat, converted with fdopen, and permissions changed with fchmod on the opened fd.

# Validation
## Rubric
- [x] Confirm the introduced longsoak path is constructed under a runtime/persistent log directory and passed to the helper as a pathname. Evidence: stage3/linux_init/a90_longsoak.c:48-60 and :72-118.
- [x] Confirm the helper lacks symlink-safe open semantics for the recorder output despite defining O_NOFOLLOW. Evidence: stage3/linux_init/helpers/a90_longsoak.c:16-18 and :321.
- [x] Confirm a path-based chmod is performed after opening, rather than fchmod on a verified fd. Evidence: stage3/linux_init/helpers/a90_longsoak.c:326.
- [x] Dynamically reproduce redirected root/helper writes through a symlink in the log directory. Evidence: poc_evidence.txt shows JSONL appended to the symlink target.
- [x] Dynamically reproduce redirected permission change through the same symlink. Evidence: poc_evidence.txt shows victim mode changed from 0644 to 0600; LLDB trace confirms execution reached chmod(path, 0600) with a non-null FILE *.
## Report
Validated the finding at commit 54a9077cc7bc789069f064586af5aeb79745b1ca. Code review showed PID1 constructs the longsoak recorder path under the runtime log directory using snprintf("%s/longsoak-%s.jsonl", log_dir, session) at stage3/linux_init/a90_longsoak.c:48-60, then passes that path as argv[1] to /bin/a90_longsoak at stage3/linux_init/a90_longsoak.c:72-118. The helper defines O_NOFOLLOW at stage3/linux_init/helpers/a90_longsoak.c:16-18 but does not use it for the output path. Instead, stage3/linux_init/helpers/a90_longsoak.c:321 opens the attacker-controlled pathname with fopen(path, "a"), and line 326 calls chmod(path, 0600); both APIs follow symlinks. I compiled the real helper with gcc -O0 -g and reproduced the issue with a writable logs directory containing a symlink planted by user nobody to a root-owned 0644 victim file. Captured PoC output: BEFORE victim=root:root 644 regular file /tmp/a90_longsoak_poc/run/root_victim.txt; BEFORE link=nobody:nogroup 777 symbolic link '/tmp/a90_longsoak_poc/run/logs/longsoak-v146-attacker.jsonl' -> '../root_victim.txt'; after running the helper, AFTER victim=root:root 600 regular file, and the victim content contained appended JSONL records such as {"type":"start","session":"v146-attacker",...}. This proves both redirected append and redirected chmod through the symlink. Direct crash testing was not applicable because this is a file-redirection logic flaw; the helper ran until timeout sent SIGTERM. ASan/UBSan build also produced no memory-safety report, as expected, but reproduced target_mode=600 and appended_lines=5. Valgrind was attempted but unavailable in the container (bash: command not found: valgrind). A non-interactive LLDB trace stopped at stage3/linux_init/helpers/a90_longsoak.c:326 after fopen had returned a non-null FILE * for the symlink path, with frame variables showing path=/workspace/validation_artifacts/a90-longsoak-symlink/lldb_run2/logs/longsoak-v146-debug2.jsonl, file=non-null, session=v146-debug2, interval_sec=1. Therefore the suspected symlink-following vulnerability is valid.

# Evidence
stage3/linux_init/a90_longsoak.c (L48 to 60)
  Note: PID1 builds the longsoak output filename under the runtime log directory and later passes this path to the root helper.
```
static void longsoak_build_session(char *out, size_t out_size) {
    snprintf(out, out_size, "%s-%ld", INIT_BUILD, monotonic_millis());
}

static int longsoak_build_path(const char *session, char *out, size_t out_size) {
    const char *log_dir = a90_runtime_log_dir();
    int written;

    if (log_dir == NULL || log_dir[0] == '\0') {
        log_dir = NATIVE_LOG_FALLBACK_DIR;
        (void)ensure_dir(log_dir, 0700);
    }
    written = snprintf(out, out_size, "%s/longsoak-%s.jsonl", log_dir, session);
```

stage3/linux_init/helpers/a90_longsoak.c (L16 to 18)
  Note: The helper defines O_NOFOLLOW, indicating symlink-safe opening was considered, but the flag is not used for the output file.
```
#ifndef O_NOFOLLOW
#define O_NOFOLLOW 0
#endif
```

stage3/linux_init/helpers/a90_longsoak.c (L321 to 327)
  Note: The root helper opens the recorder path with fopen("a") and then chmods the path; both follow symlinks, enabling redirected appends/chmod if the log filename is a symlink.
```
    file = fopen(path, "a");
    if (file == NULL) {
        fprintf(stderr, "a90_longsoak: open %s: %s\n", path, strerror(errno));
        return 1;
    }
    chmod(path, 0600);
    write_event(file, session, "start", seq, interval_sec);
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept at Medium. The code evidence and validation prove a real root symlink-following issue: a90_longsoak.c builds and passes a runtime log path to /bin/a90_longsoak, and helpers/a90_longsoak.c uses fopen(path, "a") and chmod(path, 0600) instead of O_NOFOLLOW/fstat/fchmod. The impact can be high for a single rooted device because arbitrary target append/chmod can corrupt files or affect availability. However, likelihood is low-to-moderate because there is no public network path, the runtime logs directory is intended to be 0700, longsoak must be started, and the generated filename includes monotonic time requiring prediction, symlink spraying, or a race. These constraints prevent escalation to High/Critical but the privileged boundary crossing warrants Medium rather than ignore/low.
## Likelihood
low - Exploitation is not remotely exposed and requires local/persistent-storage write access plus predicting/spraying/racing a monotonic-time filename or controlling the log directory contents before longsoak starts. The 0700 runtime logs directory reduces ordinary unprivileged reachability.
## Impact
high - If exploited, a root-run helper can append JSONL records to an attacker-selected symlink target and change that target's mode to 0600. This can corrupt root-owned files, alter permissions, or damage device/runtime availability, though the written content is constrained by the helper's log format.
## Assumptions
- The native init binary is deployed as device PID1/root as described by the repository context.
- The longsoak helper is installed at /bin/a90_longsoak and is launched by the native init runtime.
- An attacker can either pre-populate a trusted persistent runtime/log filesystem, or can race/write in the selected log directory before the helper opens the generated recorder path.
- The generated monotonic-time filename makes reliable exploitation harder unless the attacker can spray candidate symlinks or race after path construction.
- local or physical ability to modify the persistent runtime/log storage, or active write access to the selected runtime logs directory
- longsoak must be started through the native init shell/service command path
- attacker must predict, spray, or race the longsoak filename containing monotonic time
- chosen symlink target must be meaningful for root append and chmod effects
## Path
Attacker storage write
  -> symlink longsoak-v146-<time>.jsonl
  -> PID1 starts /bin/a90_longsoak with that path
  -> helper fopen("a") and chmod(path,0600)
  -> root append/chmod on target
## Path evidence
- `stage3/linux_init/a90_longsoak.c:48-60` - PID1 constructs the session and recorder path as <runtime_log_dir>/longsoak-<session>.jsonl.
- `stage3/linux_init/a90_longsoak.c:72-118` - The constructed path is passed as argv[1] to A90_LONGSOAK_HELPER and spawned through a90_run_spawn.
- `stage3/linux_init/helpers/a90_longsoak.c:16-18` - O_NOFOLLOW is defined but not applied to the recorder output open.
- `stage3/linux_init/helpers/a90_longsoak.c:321-326` - The helper opens the path with fopen("a") and then chmods the pathname; both follow symlinks.
- `stage3/linux_init/a90_run.c:104-124` - The spawn path forks and execve's the helper without dropping privileges.
- `stage3/linux_init/a90_runtime.c:74-79` - Runtime directories include a logs directory intended to be mode 0700, which limits but does not eliminate pre-populated/race-based symlink risk on persistent storage.
- `stage3/linux_init/a90_runtime.c:160-164` - Runtime root is selected from SD or cache storage, placing the longsoak path on persistent storage when available.
- `stage3/linux_init/v146/80_shell_dispatch.inc.c:946-947` - The longsoak command is exposed through the native init command dispatcher.
## Narrative
The finding is real and in scope. PID1 builds a recorder path under the runtime log directory and passes it to /bin/a90_longsoak. The helper defines O_NOFOLLOW but does not use it for the output file; it calls fopen(path, "a") followed by chmod(path, 0600). Those operations follow symlinks, and prior validation reproduced both root append and chmod redirection through a planted symlink. Severity remains Medium: the impact is privileged file corruption/permission change on a rooted device, but exploitation requires local/persistent-storage write capability plus filename prediction/spraying or a race and a longsoak start event.
## Controls
- No public network ingress or load balancer is associated with the longsoak helper.
- Longsoak requires an explicit shell/service start rather than automatic remote exposure.
- Runtime logs directory is chmoded to 0700 during initialization.
- SD runtime use requires expected UUID and read/write probes.
- There is no symlink-safe output open or fd-based chmod control in the helper.
## Blindspots
- Static review cannot confirm actual deployed filesystem ownership, mount options, or whether external device hardening blocks symlink creation in the selected log directory.
- Repository artifacts do not fully show the final boot image packaging/install process for /bin/a90_longsoak.
- No cloud/IaC exposure exists in the checkout, so assessment is limited to local device runtime attack paths.
- Real-world exploitability depends on whether attackers can physically or logically modify the SD/cache runtime storage before longsoak starts.
