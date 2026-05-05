# F023. Auto-menu busy-gate bypass allows risky root commands

## Metadata

| field | value |
|---|---|
| finding_id | `c0f22223f1e481918095b4eac43ab7c8` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c0f22223f1e481918095b4eac43ab7c8 |
| severity | `low` |
| status | `new` |
| detected_at | `2026-04-28T04:26:13.144926Z` |
| committed_at | `2026-04-27 01:40:17 +0900` |
| commit_hash | `dc853fe0a0d30006821f4aec1b304e8e2614c90e` |
| relevant_paths | `stage3/linux_init/init_v72.c | stage3/linux_init/init_v70.c` |
| has_patch | `false` |

## CSV Description

In `init_v72.c`, `command_allowed_during_auto_menu()` was changed from a strict allowlist (v70) to a policy that allows any command unless it is explicitly `CMD_DANGEROUS` or a small input-control subset. However, several high-impact commands (`run`, `runandroid`, `writefile`, `mountfs`, `mknod*`, etc.) are still not marked `CMD_DANGEROUS`. As a result, during non-power auto-menu states an attacker with command-channel access can still execute privileged filesystem/process actions that were previously blocked by the busy gate. This is a security regression of an existing mitigation (menu-active command suppression), not a new auth model.

## Codex Cloud Detail

Auto-menu busy-gate bypass allows risky root commands
Link: https://chatgpt.com/codex/cloud/security/findings/c0f22223f1e481918095b4eac43ab7c8?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: low (attack path: low)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: dc853fe
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 1:26:13
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: busy-gate policy regression. v70 used a strict whitelist during auto-menu; v72 switched to a broad allow-by-default model keyed on `CMD_DANGEROUS`, but command flagging is incomplete for sensitive operations.
In `init_v72.c`, `command_allowed_during_auto_menu()` was changed from a strict allowlist (v70) to a policy that allows any command unless it is explicitly `CMD_DANGEROUS` or a small input-control subset. However, several high-impact commands (`run`, `runandroid`, `writefile`, `mountfs`, `mknod*`, etc.) are still not marked `CMD_DANGEROUS`. As a result, during non-power auto-menu states an attacker with command-channel access can still execute privileged filesystem/process actions that were previously blocked by the busy gate. This is a security regression of an existing mitigation (menu-active command suppression), not a new auth model.

# Validation
## Rubric
- [x] Confirm v72 gate semantics in source: non-power auto-menu allows all commands except CMD_DANGEROUS + small explicit deny subset (`init_v72.c:9393-9406`).
- [x] Confirm sensitive commands are not flagged CMD_DANGEROUS (`init_v72.c:9349-9358`) and perform privileged actions (`cmd_writefile`/`cmd_run`/`cmd_runandroid`/`handle_mountfs` at `init_v72.c:8127-8163, 8229-8321, 9188-9205`).
- [x] Confirm shell busy enforcement relies on `command_allowed_during_auto_menu()` (`init_v72.c:9479-9490`).
- [x] Compare with v70 strict whitelist baseline (`init_v70.c:8773-8791`) and reproduce behavior difference with PoC binaries (`v72_output.txt` vs `v70_output.txt`).
- [x] Attempt compiled-stack runtime methods before final conclusion: crash attempt (no crash), ASan run (clean), debugger trace (LLDB breakpoint/backtrace captured), valgrind unavailable.
## Report
I validated the regression with targeted dynamic checks plus source correlation.

1) Policy change in v72 is allow-by-default during non-power auto-menu: `command_allowed_during_auto_menu()` returns true for all commands except `CMD_DANGEROUS` and a small hardcoded set (`screenmenu/menu/blindmenu/waitkey/readinput/waitgesture`) at `stage3/linux_init/init_v72.c:9393-9406`.

2) Sensitive commands are not tagged dangerous in v72 command table: `mknodc`, `mknodb`, `mountfs`, `writefile` are `CMD_NONE`; `run`, `runandroid` are `CMD_BLOCKING` (not `CMD_DANGEROUS`) at `init_v72.c:9349-9358`.

3) Busy-gate enforcement in shell loop depends on this function: `if (auto_menu_is_active() && !command_allowed_during_auto_menu(command)) ... continue;` at `init_v72.c:9479-9490`. So any command that returns allowed bypasses busy suppression.

4) Baseline v70 is strict whitelist only (`return true` for a small fixed list, else false) at `stage3/linux_init/init_v70.c:8773-8791`.

5) Reproduction PoC (built from checked-out sources):
- Built `/workspace/validation_artifacts/busy_gate_regression/poc_v72_gate` (includes `init_v72.c` and directly calls `find_command` + `command_allowed_during_auto_menu` with auto-menu state file set to `1\n`).
- Output (`v72_output.txt`) shows non-power state allows sensitive commands:
  - `cmd=run flags=0x2 allowed=true`
  - `cmd=runandroid flags=0x2 allowed=true`
  - `cmd=writefile flags=0x0 allowed=true`
  - `cmd=mountfs flags=0x0 allowed=true`
  - `cmd=mknodc flags=0x0 allowed=true`
  while `screenmenu` and `netservice` are denied.
- Built `/workspace/validation_artifacts/busy_gate_regression/poc_v70_gate` against `init_v70.c` baseline; output (`v70_output.txt`) shows same commands denied (`allowed=false`).

6) Required compiled-stack attempts:
- Crash attempt on debug build of full v72 init (`gcc -O0 -g ... init_v72.c`, then `timeout 5 /tmp/init_v72_dbg`) did not crash; process timed out due hardware-specific boot path.
- Valgrind unavailable (`valgrind: command not found`).
- Debugger attempt succeeded: LLDB breakpoint at `command_allowed_during_auto_menu` hit at `init_v72.c:9391`; backtrace shows `main -> check_cmd -> command_allowed_during_auto_menu` (`lldb_v72.txt`).

Conclusion: finding is valid. v72 introduced a busy-gate policy regression: in non-power auto-menu state, high-impact commands not marked `CMD_DANGEROUS` are now allowed, unlike v70.

# Evidence
stage3/linux_init/init_v70.c (L8773 to 8791)
  Note: Previous behavior used a strict whitelist while auto menu was active, showing the regression introduced in v72.
```
    if (strcmp(name, "help") == 0 ||
        strcmp(name, "version") == 0 ||
        strcmp(name, "status") == 0 ||
        strcmp(name, "bootstatus") == 0 ||
        strcmp(name, "timeline") == 0 ||
        strcmp(name, "last") == 0 ||
        strcmp(name, "logpath") == 0 ||
        strcmp(name, "logcat") == 0 ||
        strcmp(name, "inputlayout") == 0 ||
        strcmp(name, "inputmonitor") == 0 ||
        strcmp(name, "uname") == 0 ||
        strcmp(name, "pwd") == 0 ||
        strcmp(name, "mounts") == 0 ||
        strcmp(name, "reattach") == 0 ||
        strcmp(name, "stophud") == 0) {
        return true;
    }

    return false;
```

stage3/linux_init/init_v72.c (L9349 to 9358)
  Note: Sensitive commands are not marked CMD_DANGEROUS (e.g., mknod*, mountfs, writefile, run, runandroid), so they pass the new gate.
```
    { "mkdir", handle_mkdir, "mkdir <dir>", CMD_NONE },
    { "mknodc", handle_mknodc, "mknodc <path> <major> <minor>", CMD_NONE },
    { "mknodb", handle_mknodb, "mknodb <path> <major> <minor>", CMD_NONE },
    { "mountfs", handle_mountfs, "mountfs <src> <dst> <type> [ro]", CMD_NONE },
    { "umount", handle_umount, "umount <path>", CMD_NONE },
    { "echo", handle_echo, "echo <text>", CMD_NONE },
    { "writefile", handle_writefile, "writefile <path> <value...>", CMD_NONE },
    { "cpustress", handle_cpustress, "cpustress [sec] [workers]", CMD_BLOCKING },
    { "run", handle_run, "run <path> [args...]", CMD_BLOCKING },
    { "runandroid", handle_runandroid, "runandroid <path> [args...]", CMD_BLOCKING },
```

stage3/linux_init/init_v72.c (L9393 to 9406)
  Note: Core policy change: when power page is not active, all commands are allowed except CMD_DANGEROUS and a few menu/input commands.
```
    if (!auto_menu_power_is_active()) {
        if ((command->flags & CMD_DANGEROUS) != 0) {
            return false;
        }
        if (strcmp(name, "screenmenu") == 0 ||
            strcmp(name, "menu") == 0 ||
            strcmp(name, "blindmenu") == 0 ||
            strcmp(name, "waitkey") == 0 ||
            strcmp(name, "readinput") == 0 ||
            strcmp(name, "waitgesture") == 0) {
            return false;
        }
        return true;
    }
```

stage3/linux_init/init_v72.c (L9479 to 9490)
  Note: Shell loop enforcement relies entirely on command_allowed_during_auto_menu(), so the broadened allow logic is directly exploitable.
```
        if (auto_menu_is_active() && !command_allowed_during_auto_menu(command)) {
            if (auto_menu_power_is_active()) {
                cprintf("[busy] power menu active; send hide/q before commands\r\n");
            } else if ((command->flags & CMD_DANGEROUS) != 0) {
                cprintf("[busy] auto menu active; hide/q before dangerous command\r\n");
            } else {
                cprintf("[busy] auto menu active; command waits for input/menu control\r\n");
            }
            save_last_result(argv[0], -EBUSY, EBUSY, 0, command->flags);
            native_logf("cmd", "busy menu-active name=%s flags=0x%x",
                        argv[0], command->flags);
            continue;
```

# Attack-path analysis
Final: low | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The finding is valid and in-scope, with strong code+PoC evidence. However, the exploited precondition (attacker can already write commands to the native-init shell channel) is a high bar and already close to full control in this lab-oriented design. The regression weakens an existing safety gate (menu-busy suppression) rather than introducing new remote auth bypass or privilege boundary break. Therefore medium is slightly overstated for practical risk delta; low better matches probability × incremental impact in this threat model.
## Likelihood
medium - Reachability is plausible in this project model (USB host/local bridge access), and PoC confirms behavior; however it requires specific runtime state and pre-existing shell-channel access.
## Impact
low - If an attacker can reach the shell input path during non-power auto-menu, they can execute privileged file/process actions that should be blocked by busy gating. Integrity/availability impact on the device is meaningful, but incremental security delta is limited because attacker already needs command-channel access.
## Assumptions
- The deployed runtime corresponds to v72 as documented in README/docs.
- Attacker can send command text to the native-init shell channel (direct USB ACM host access or local access to the host bridge endpoint).
- Auto-menu is active in non-power state (AUTO_MENU_STATE_PATH indicates active but not power).
- Access to native-init command channel (/dev/ttyGS0 via USB ACM, often bridged to 127.0.0.1:54321)
- auto_menu_is_active() true while auto_menu_power_is_active() false
- Target running init_v72 behavior
## Path
[attacker input]
  -> [USB ACM / localhost bridge]
  -> [shell_loop busy gate]
  -> [v72 non-power allow-by-default]
  -> [run/writefile/mountfs/mknod as PID1 root]
## Path evidence
- `stage3/linux_init/init_v72.c:9349-9358` - Sensitive commands are not tagged CMD_DANGEROUS (run/runandroid/writefile/mountfs/mknod*).
- `stage3/linux_init/init_v72.c:9393-9406` - Non-power auto-menu path allows all commands except CMD_DANGEROUS and a small explicit deny subset.
- `stage3/linux_init/init_v72.c:9479-9490` - shell_loop enforcement relies on command_allowed_during_auto_menu(); allowed commands execute.
- `stage3/linux_init/init_v72.c:8127-8157` - writefile performs direct open/write to attacker-specified path.
- `stage3/linux_init/init_v72.c:8229-8306` - run/runandroid spawn child and execve arbitrary provided path.
- `stage3/linux_init/init_v70.c:8773-8791` - Previous strict allowlist denied non-listed commands during auto-menu, showing regression.
- `scripts/revalidation/serial_tcp_bridge.py:17` - Bridge default host is 127.0.0.1 (relevant to exposure/likelihood).
- `scripts/revalidation/serial_tcp_bridge.py:345-346` - Bridge exposes configurable TCP listener for shell channel.
- `README.md:17-25` - v72 is documented as latest verified runtime and control channel uses serial bridge.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_dc853fe0a0d30006821f4aec1b304e8e2614c90e/extracted/busy_gate_regression/v72_output.txt:1-18` - Executable PoC shows run/runandroid/writefile/mountfs/mknodc are allowed in state=1.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_dc853fe0a0d30006821f4aec1b304e8e2614c90e/extracted/busy_gate_regression/v70_output.txt:1-18` - Executable PoC baseline shows same commands denied in v70.
## Narrative
The bug is real and reproducible: v72 changed auto-menu gating to allow-by-default for non-power menu states, while high-impact commands remain non-dangerous in flags and therefore pass the gate. Static code and executable PoC outputs show run/writefile/mountfs/mknod are allowed in v72 but denied in v70. This is in-scope because init_v72 is the documented active runtime. Severity is reduced to low because exploitation requires prior command-channel access that already provides broad device control outside menu-busy windows; the regression weakens a safety control rather than introducing a new authentication bypass.
## Controls
- Auto-menu busy gate exists and blocks some commands
- CMD_DANGEROUS flag intended to classify risky operations
- Power-page mode uses stricter allowlist behavior
- Serial bridge defaults to localhost binding
- Netservice is opt-in via /cache/native-init-netservice flag
## Blindspots
- Static-only assessment; no live device state frequency data for auto-menu active/non-power windows.
- Cannot validate host/network deployment practices (e.g., whether bridge is ever bound beyond localhost in real usage).
- No fleet telemetry to estimate real-world exploit prevalence.
