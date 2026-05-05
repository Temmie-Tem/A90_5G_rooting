# F029. Input event name path traversal in probing helpers

## Metadata

| field | value |
|---|---|
| finding_id | `370b1e0b2e8881919ffb09e26d91688c` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/370b1e0b2e8881919ffb09e26d91688c |
| severity | `informational` |
| status | `mitigated-v126` |
| detected_at | `2026-04-27T22:51:47.172791Z` |
| committed_at | `2026-04-24 00:31:08 +0900` |
| commit_hash | `5259fd7d5b06b1fd3c0d4a7b3d82f5f4656eb5a7` |
| relevant_paths | `stage3/linux_init/init_v10.c` |
| has_patch | `true` |

## CSV Description

The commit introduces input helper logic (`inputinfo`, `readinput`, later reused by `inputcaps`) that treats any argument starting with `event` as valid. It does not enforce a strict `event[0-9]+` format and allows `/` and `..` segments. That unchecked value is interpolated into `/sys/class/input/%s/...` and `/dev/input/%s` paths. As a result, an attacker with access to this shell can traverse paths under `/sys` and cause `mknod()` at unintended locations under `/dev` (given suitable directory setup), bypassing the intended event-node-only scope.

## Local Remediation

- Batch 6 enforces strict `event[0-9]+` validation in latest v126 input commands and retained v10 input helpers.

## Codex Cloud Detail

Input event name path traversal in probing helpers
Link: https://chatgpt.com/codex/cloud/security/findings/370b1e0b2e8881919ffb09e26d91688c?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 5259fd7
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오전 7:51:47
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Bug introduced: insufficient validation of event names in the newly added input probing helpers causes path traversal and overly broad privileged file/device operations.
The commit introduces input helper logic (`inputinfo`, `readinput`, later reused by `inputcaps`) that treats any argument starting with `event` as valid. It does not enforce a strict `event[0-9]+` format and allows `/` and `..` segments. That unchecked value is interpolated into `/sys/class/input/%s/...` and `/dev/input/%s` paths. As a result, an attacker with access to this shell can traverse paths under `/sys` and cause `mknod()` at unintended locations under `/dev` (given suitable directory setup), bypassing the intended event-node-only scope.

# Validation
## Rubric
- [x] Confirm commit-added validation logic allows non-`event[0-9]+` names (`init_v10.c:142-155`).
- [x] Confirm tainted argument reaches privileged path sinks (`/sys/class/input/%s/dev`, `/dev/input/%s`, `mknod`) (`init_v10.c:164-190`, `233-242`, `264-294`, `1144-1148`).
- [x] Attempt direct crash with malformed payload on debug build (no crash observed).
- [x] Attempt valgrind/ASan before code-only conclusion (valgrind unavailable; ASan run completed without memory findings).
- [x] Use debugger-backed dynamic PoC to prove traversal effect and unintended node creation outside `/dev/input`.
## Report
I validated the finding against `stage3/linux_init/init_v10.c` in commit `5259fd7d5b06b1fd3c0d4a7b3d82f5f4656eb5a7`.

Key code evidence:
- `normalize_event_name()` only checks `strncmp(arg, "event", 5)` and then copies raw input (`init_v10.c:142-155`), so values like `event/../../owned` are accepted.
- That value is embedded into `/sys/class/input/%s/dev` and `/dev/input/%s`, then passed to `mknod()` (`init_v10.c:164-190`).
- User-controlled shell args flow into this path via `cmd_inputinfo` and `cmd_readinput` (`init_v10.c:233-242`, `264-294`), exposed in command dispatcher (`init_v10.c:1144-1148`).

Dynamic validation steps:
1) Crash attempt (debug build):
- Built PoC harness including real vulnerable functions.
- Ran with traversal payload: `./poc_harness 'event/../../tmp/x'`.
- Result: no crash; function failed with ENOENT (expected for missing sysfs path).

2) Valgrind/ASan attempt:
- `valgrind` not available in container (`command not found`).
- Built ASan binary and ran same payload; no memory errors/crash.

3) Debugger + exploit reproduction:
- Built `poc_harness_chroot` (calls original functions after `chroot` to controlled fake root).
- Created fake tree where only `/sys/class/owned/dev` exists (not `/sys/class/input/event/dev`) and `/dev/input/event` directory exists.
- Ran payload `event/../../owned`.
- Output:
  - `normalized=event/../../owned`
  - `resolved=/dev/input/event/../../owned`
- Verified created node: `/tmp/pocroot_compare/dev/owned` (outside intended `/dev/input/event*` scope).
- LLDB breakpoint at `init_v10.c:189` (the `mknod` call) showed:
  - `event_name = "event/../../owned"`
  - `dev_info_path = "/sys/class/input/event/../../owned/dev"`
  - `out = "/dev/input/event/../../owned"`
  - backtrace `main -> get_input_event_path -> mknod`.

Conclusion: the suspected path traversal / over-broad privileged file operation is reproducible and valid.

# Evidence
stage3/linux_init/init_v10.c (L142 to 155)
  Note: Validation only checks for `event` prefix and otherwise prepends `event`; it does not reject path separators or `..` traversal components.
```
static int normalize_event_name(const char *arg, char *out, size_t out_size) {
    if (strncmp(arg, "event", 5) == 0) {
        if (snprintf(out, out_size, "%s", arg) >= (int)out_size) {
            errno = ENAMETOOLONG;
            return -1;
        }
        return 0;
    }

    if (snprintf(out, out_size, "event%s", arg) >= (int)out_size) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
```

stage3/linux_init/init_v10.c (L164 to 190)
  Note: Unsanitized `event_name` is embedded into sysfs and /dev paths, then used to read device numbers and call `mknod()`, enabling unintended path resolution.
```
    if (snprintf(dev_info_path, sizeof(dev_info_path),
                 "/sys/class/input/%s/dev", event_name) >= (int)sizeof(dev_info_path)) {
        errno = ENAMETOOLONG;
        return -1;
    }

    if (read_text_file(dev_info_path, dev_info, sizeof(dev_info)) < 0) {
        return -1;
    }
    trim_newline(dev_info);

    if (sscanf(dev_info, "%u:%u", &major_num, &minor_num) != 2) {
        errno = EINVAL;
        return -1;
    }

    if (ensure_dir("/dev/input", 0755) < 0) {
        return -1;
    }

    if (snprintf(out, out_size, "/dev/input/%s", event_name) >= (int)out_size) {
        errno = ENAMETOOLONG;
        return -1;
    }

    if (mknod(out, S_IFCHR | 0600, makedev(major_num, minor_num)) < 0 && errno != EEXIST) {
        return -1;
```

stage3/linux_init/init_v10.c (L233 to 242)
  Note: `inputinfo` directly feeds user-supplied argument through weak normalization into path-building logic.
```
static void cmd_inputinfo(char **argv, int argc) {
    if (argc >= 2) {
        char event_name[32];

        if (normalize_event_name(argv[1], event_name, sizeof(event_name)) < 0) {
            cprintf("inputinfo: invalid event name\r\n");
            return;
        }
        print_input_event_info(event_name);
        return;
```

stage3/linux_init/init_v10.c (L276 to 294)
  Note: `readinput` uses the same weak normalization and then opens the resolved path, making traversal-triggered node creation/use reachable.
```
    if (normalize_event_name(argv[1], event_name, sizeof(event_name)) < 0) {
        cprintf("readinput: invalid event name\r\n");
        return;
    }

    if (argc >= 3 && sscanf(argv[2], "%d", &count) != 1) {
        cprintf("readinput: invalid count\r\n");
        return;
    }
    if (count <= 0) {
        count = 1;
    }

    if (get_input_event_path(event_name, dev_path, sizeof(dev_path)) < 0) {
        cprintf("readinput: %s: %s\r\n", event_name, strerror(errno));
        return;
    }

    fd = open(dev_path, O_RDONLY);
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Probability × impact re-rating: the code defect is valid and reachable, but it does not materially increase attacker capability beyond the existing shell trust boundary. The shell is intentionally exposed over USB ACM and provides run/writefile/mknodb primitives already (including in pre-v10 lineage), so this traversal is largely redundant in exploitation value. No public ingress, no cross-tenant boundary, and no meaningful privilege-escalation delta were evidenced.
## Likelihood
medium - Triggering the buggy helper is easy once shell access exists, but obtaining that access requires local/physical debug conditions and custom boot workflow.
## Impact
ignore - Although traversal exists, attacker must already control a highly privileged debug shell that already permits arbitrary command execution and broad file/device operations; incremental compromise is negligible.
## Assumptions
- stage3/linux_init/init_v13.c represents the currently used native-init shell lineage (v10-v13) in this repo.
- Attacker model is a non-owner actor; pure owner self-debug actions are not treated as security compromise.
- Device must be booted into custom native init image with USB ACM shell enabled
- Attacker must have physical USB serial access (or access to a local host bridge)
- Attacker can already send arbitrary shell commands to shell_loop()
## Path
[USB ACM/localhost client] -> [shell_loop] -> [normalize_event_name] -> [get_input_event_path + mknod] -> [/dev/input/... traversal]
## Path evidence
- `stage3/linux_init/init_v13.c:142-155` - normalize_event_name only checks 'event' prefix and permits traversal characters/segments.
- `stage3/linux_init/init_v13.c:164-190` - Unsanitized event_name is embedded into /sys and /dev paths and used in mknod().
- `stage3/linux_init/init_v13.c:233-241` - cmd_inputinfo takes user argument through weak normalization into sink path flow.
- `stage3/linux_init/init_v13.c:339-365` - cmd_readinput similarly routes user-controlled event name to get_input_event_path.
- `stage3/linux_init/init_v13.c:1325-1329` - USB ACM serial console is attached and shell_loop starts without authentication gates.
- `stage3/linux_init/init_v13.c:657-678` - Help shows high-privilege commands already exposed (mknodb, writefile, run, runandroid).
- `stage3/linux_init/init_v13.c:932-944` - writefile opens attacker-supplied path directly.
- `stage3/linux_init/init_v13.c:981-986` - run command executes attacker-specified binary via execve().
- `stage3/linux_init/init_v9.c:389-407` - Pre-commit shell already documented dangerous primitives, reducing incremental security delta.
- `docs/reports/ADB_FROM_LINUX_INIT_LOG_2026-04-23.md:261-272` - Docs confirm USB ACM mini-shell path and host serial interaction method.
- `scripts/revalidation/serial_tcp_bridge.py:17-19` - Optional bridge defaults to localhost 127.0.0.1:54321 (not public exposure by default).
## Narrative
The path-traversal bug is real in code: weak event-name normalization (init_v13.c 142-155) reaches path construction and mknod sinks (164-190) via user-controlled shell args in input helpers (233-241, 339-365). Reachability is also real because USB ACM shell is started directly (1325-1329) and docs show host access via ttyACM0. But security impact is minimal in this project context: the same shell already exposes broad privileged primitives (run/execve, writefile arbitrary path, mknodb) and did so even before this commit line (v9 help/dispatcher). Therefore this is primarily a correctness/safety bug inside an already fully-privileged debug shell, not a meaningful additional security boundary break.
## Controls
- Physical USB access required for primary shell ingress
- Optional bridge defaults to localhost binding
- No internet-facing listener in repository artifacts by default
## Blindspots
- Static-only review cannot prove which exact init_v*.c is shipped in every flashed artifact at runtime.
- No device runtime verification in this stage beyond provided validation summary.
- Threat model is implicit (research workspace), not a formal attacker model document.
