# F010. Service command bypasses dangerous-command gating

## Metadata

| field | value |
|---|---|
| finding_id | `c671edef4b888191ae9c45de4f3bcdf1` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c671edef4b888191ae9c45de4f3bcdf1 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-04T10:30:43.686335Z` |
| committed_at | `2026-05-03 23:50:41 +0900` |
| commit_hash | `3e6f0223bb528c3a141732f40fc9a8e28228bcd8` |
| relevant_paths | `stage3/linux_init/a90_service.c | stage3/linux_init/v101/80_shell_dispatch.inc.c | stage3/linux_init/a90_controller.c | stage3/linux_init/a90_tcpctl.c` |
| has_patch | `false` |

## CSV Description

v101 adds a generic `service` command that dispatches lifecycle operations for autohud, tcpctl/netservice, adbd, and rshell. The service metadata correctly labels tcpctl, adbd, and rshell as dangerous/raw-control services, and the existing direct `netservice` and `rshell` commands are registered with CMD_DANGEROUS. However, the new umbrella `service` command is registered with CMD_NONE. The controller's active-menu safety gate only blocks dangerous operations when the command table flags include CMD_DANGEROUS, so `service start tcpctl`, `service enable tcpctl`, `service start rshell`, and `service enable rshell` are treated as non-dangerous. This bypasses the intended dangerous-command gating and also misreports the operation as non-dangerous in command protocol framing. The impact is limited because an attacker still needs access to the existing PID1 shell/control channel, but the bug creates a lower-friction path to activate services that expose root-control network surfaces, including tcpctl, which listens on INADDR_ANY and supports root `run` commands.

## Codex Cloud Detail

Service command bypasses dangerous-command gating
Link: https://chatgpt.com/codex/cloud/security/findings/c671edef4b888191ae9c45de4f3bcdf1
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 3e6f022
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:30:43
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: the new `service` command should either be marked CMD_DANGEROUS as a whole, or the dispatcher should apply subcommand/service-specific policy before performing mutating lifecycle operations. Safe `list`/`status` can remain separately exposed only if the command framework supports per-subcommand flags.
v101 adds a generic `service` command that dispatches lifecycle operations for autohud, tcpctl/netservice, adbd, and rshell. The service metadata correctly labels tcpctl, adbd, and rshell as dangerous/raw-control services, and the existing direct `netservice` and `rshell` commands are registered with CMD_DANGEROUS. However, the new umbrella `service` command is registered with CMD_NONE. The controller's active-menu safety gate only blocks dangerous operations when the command table flags include CMD_DANGEROUS, so `service start tcpctl`, `service enable tcpctl`, `service start rshell`, and `service enable rshell` are treated as non-dangerous. This bypasses the intended dangerous-command gating and also misreports the operation as non-dangerous in command protocol framing. The impact is limited because an attacker still needs access to the existing PID1 shell/control channel, but the bug creates a lower-friction path to activate services that expose root-control network surfaces, including tcpctl, which listens on INADDR_ANY and supports root `run` commands.

# Validation
## Rubric
- [x] Confirm the relevant v101 services are explicitly marked dangerous/raw-control in service metadata.
- [x] Confirm the new umbrella `service` dispatcher reaches mutating lifecycle operations for tcpctl/netservice and rshell.
- [x] Confirm the actual command table assigns CMD_DANGEROUS to direct netservice/rshell but CMD_NONE to umbrella service.
- [x] Confirm the active-menu safety gate and protocol framing rely only on argv[0] plus command_table flags, with no service/subcommand policy.
- [x] Dynamically reproduce the policy difference under active-menu conditions and, where possible, trace it in a debugger; document crash/ASan/valgrind attempts and limitations.
## Report
Validated the finding as a control-plane policy bypass, not a memory corruption crash. I built a minimal debug harness linked against the real stage3/linux_init/a90_controller.c and modeled the actual v101 command_table flags from stage3/linux_init/v101/80_shell_dispatch.inc.c:816-818. Direct run output showed that with auto-menu active and power page inactive, direct dangerous commands are blocked: `netservice` and `rshell` with flags=0x4 return `A90_CONTROLLER_BUSY_DANGEROUS`, while umbrella `service start tcpctl`, `service enable tcpctl`, `service start rshell`, and `service enable rshell` with flags=0x0 return `A90_CONTROLLER_BUSY_NONE`. LLDB confirmed the real gate call for the bypass case: `a90_controller_command_busy_reason(name="service", flags=0, menu_active=true, power_page_active=false)` at a90_controller.c:55, then after step-out the return variable was `A90_CONTROLLER_BUSY_NONE`. Code evidence: dangerous service metadata is present for tcpctl/adbd/rshell in a90_service.c:44-73; `service_start_one` and `service_enable_one` invoke `a90_netservice_start()`, `a90_netservice_set_enabled(true)`, `rshell_start_service(true)`, and `rshell_set_enabled(true)` in v101/80_shell_dispatch.inc.c:569-614; direct `netservice`/`rshell` are CMD_DANGEROUS but umbrella `service` is CMD_NONE at v101/80_shell_dispatch.inc.c:816-818; the dispatcher passes only argv[0] and command->flags to the busy gate at v101/80_shell_dispatch.inc.c:892-895 and protocol framing uses the same command->flags at lines 919-956; the controller only blocks dangerous active-menu commands when `(flags & CMD_DANGEROUS) != 0` at a90_controller.c:61-68. I attempted crash/ASan-style validation by compiling with `-O0 -g -fsanitize=address,undefined`; no crash or sanitizer finding is expected for this logic bug, and the sanitizer run reproduced the same unsafe allow result. Valgrind was not available (`valgrind not found`), gdb was not available, but lldb was available and used. For impact, I also compiled standalone a90_tcpctl.c and confirmed its TCP protocol accepts a `run /bin/echo tcpctl-run-poc` command; a90_tcpctl.c:517 binds to INADDR_ANY and a90_tcpctl.c:284-307 implements the absolute-path `run` operation.

# Evidence
stage3/linux_init/a90_controller.c (L51 to 68)
  Note: The active-menu safety gate relies on the command table's CMD_DANGEROUS flag; CMD_NONE commands bypass this dangerous-command block.
```
enum a90_controller_busy_reason a90_controller_command_busy_reason(const char *name,
                                                                   unsigned int flags,
                                                                   bool menu_active,
                                                                   bool power_page_active) {
    if (name == NULL || !menu_active) {
        return A90_CONTROLLER_BUSY_NONE;
    }
    if (command_is_menu_control(name)) {
        return A90_CONTROLLER_BUSY_NONE;
    }
    if (!power_page_active) {
        if ((flags & CMD_DANGEROUS) != 0) {
            return A90_CONTROLLER_BUSY_DANGEROUS;
        }
        if (command_waits_for_input(name)) {
            return A90_CONTROLLER_BUSY_AUTO_MENU;
        }
        return A90_CONTROLLER_BUSY_NONE;
```

stage3/linux_init/a90_service.c (L44 to 73)
  Note: Service metadata marks tcpctl, adbd, and rshell as dangerous/raw-control services.
```
    {
        A90_SERVICE_TCPCTL,
        "tcpctl",
        "USB NCM tcp control service",
        A90_SERVICE_KIND_NETWORK,
        A90_SERVICE_FLAG_BOOT_OPTIONAL |
            A90_SERVICE_FLAG_RAW_CONTROL |
            A90_SERVICE_FLAG_REQUIRES_NCM |
            A90_SERVICE_FLAG_DANGEROUS,
        NETSERVICE_FLAG_PATH,
    },
    {
        A90_SERVICE_ADBD,
        "adbd",
        "experimental Android adbd placeholder",
        A90_SERVICE_KIND_ANDROID,
        A90_SERVICE_FLAG_RAW_CONTROL |
            A90_SERVICE_FLAG_DANGEROUS,
        NULL,
    },
    {
        A90_SERVICE_RSHELL,
        "rshell",
        "token TCP remote shell over USB NCM",
        A90_SERVICE_KIND_REMOTE,
        A90_SERVICE_FLAG_BOOT_OPTIONAL |
            A90_SERVICE_FLAG_RAW_CONTROL |
            A90_SERVICE_FLAG_REQUIRES_NCM |
            A90_SERVICE_FLAG_DANGEROUS,
        A90_RSHELL_FLAG_NAME,
```

stage3/linux_init/a90_tcpctl.c (L284 to 307)
  Note: tcpctl's protocol includes a root `run` operation for absolute paths, showing why starting tcpctl is a dangerous lifecycle action.
```
static int command_run(int client_fd, char **argv, int argc)
{
    static char *const envp[] = {
        "PATH=/cache:/cache/bin:/bin:/system/bin",
        "HOME=/",
        "TERM=vt100",
        "LD_LIBRARY_PATH=/cache/adb/lib",
        NULL
    };
    int pipefd[2];
    int devnull;
    pid_t pid;
    int status = 0;
    int child_done = 0;
    int pipe_open = 1;
    size_t forwarded = 0;
    int truncated = 0;
    long deadline = monotonic_millis() + RUN_TIMEOUT_MS;

    if (argc < 2) {
        return send_text(client_fd, "ERR usage: run <absolute-path> [args...]\n");
    }
    if (argv[1][0] != '/') {
        return send_text(client_fd, "ERR run path must be absolute\n");
```

stage3/linux_init/a90_tcpctl.c (L517 to 526)
  Note: tcpctl binds to INADDR_ANY when started, increasing the impact of incorrectly allowing service start/enable through a non-dangerous command path.
```
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "bind: %s\n", strerror(errno));
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, 4) < 0) {
```

stage3/linux_init/v101/80_shell_dispatch.inc.c (L569 to 614)
  Note: The new service dispatcher starts and enables tcpctl/netservice and rshell from the generic service command.
```
static int service_start_one(enum a90_service_id service) {
    switch (service) {
    case A90_SERVICE_HUD:
        return start_auto_hud(BOOT_HUD_REFRESH_SECONDS, true);
    case A90_SERVICE_TCPCTL:
        return a90_netservice_start();
    case A90_SERVICE_ADBD:
        return cmd_startadbd();
    case A90_SERVICE_RSHELL:
        return rshell_start_service(true);
    default:
        return -EINVAL;
    }
}

static int service_stop_one(enum a90_service_id service) {
    switch (service) {
    case A90_SERVICE_HUD:
        return cmd_stophud();
    case A90_SERVICE_TCPCTL:
        return a90_netservice_stop();
    case A90_SERVICE_ADBD:
        return cmd_stopadbd();
    case A90_SERVICE_RSHELL:
        return rshell_stop_service();
    default:
        return -EINVAL;
    }
}

static int service_enable_one(enum a90_service_id service) {
    int rc;

    switch (service) {
    case A90_SERVICE_TCPCTL:
        rc = a90_netservice_set_enabled(true);
        if (rc < 0) {
            return rc;
        }
        return a90_netservice_start();
    case A90_SERVICE_RSHELL:
        rc = rshell_set_enabled(true);
        if (rc < 0) {
            return rc;
        }
        return rshell_start_service(true);
```

stage3/linux_init/v101/80_shell_dispatch.inc.c (L816 to 818)
  Note: Existing direct netservice and rshell commands are CMD_DANGEROUS, but the new generic service command is registered as CMD_NONE.
```
    { "netservice", handle_netservice, "netservice [status|start|stop|enable|disable]", CMD_DANGEROUS },
    { "rshell", handle_rshell, "rshell [status|start|stop|enable|disable|token [show]|rotate-token [value]]", CMD_DANGEROUS },
    { "service", handle_service, "service [list|status|start|stop|enable|disable] [name]", CMD_NONE },
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Keep Medium. The code evidence validates the policy bypass: dangerous services are tagged as dangerous, direct netservice/rshell commands are CMD_DANGEROUS, service is CMD_NONE, and the controller only checks CMD_DANGEROUS in command->flags. The impact is real because service start/enable can bring up tcpctl, which binds INADDR_ANY:2325 and supports root execve-based run. However, it should not be High or Critical because the attacker must already reach the local/USB PID1 control channel, the default bridge is localhost, and the project intentionally exposes a root lab control shell. The issue meaningfully weakens an intended safety gate and can expand exposure to a local network surface, but it is not a standalone remote compromise path.
## Likelihood
low - Exploitation is straightforward once the PID1 shell/control channel is reachable, but that channel is normally physical USB or localhost-bridged, not public internet. The bypass is relevant primarily during active-menu states where dangerous commands would otherwise be blocked.
## Impact
medium - The bypass can activate dangerous raw-control services, including tcpctl, which exposes an unauthenticated local-network/USB-NCM root command service. The impact is constrained because the attacker already needs access to the root PID1 control channel and the affected target is a single lab device/runtime.
## Assumptions
- The v101 native init runtime is flashed/deployed on the target device.
- The attacker can send commands to the existing PID1 shell/control channel via USB ACM serial or a reachable serial TCP bridge.
- The active menu is in the state where the controller's dangerous-command gate is intended to block direct netservice/rshell operations: menu_active=true and power_page_active=false.
- tcpctl/rshell helper prerequisites are present when the service start/enable operation is invoked.
- access to the existing PID1 shell/control channel
- service command reaches v101 dispatcher
- active-menu dangerous-command gate is relied on as a safety control
- tcpctl/rshell prerequisites available for service startup
## Path
PID1 shell/control channel -> service(CMD_NONE) -> busy gate allows -> service_start/enable(tcpctl|rshell) -> tcpctl/rshell raw-control service -> INADDR_ANY:2325 root run
## Path evidence
- `stage3/linux_init/a90_service.c:44-73` - Service metadata classifies tcpctl, adbd, and rshell as RAW_CONTROL and DANGEROUS services.
- `stage3/linux_init/v101/80_shell_dispatch.inc.c:569-614` - The service dispatcher starts tcpctl/adbd/rshell and enables tcpctl/rshell through the generic service command path.
- `stage3/linux_init/v101/80_shell_dispatch.inc.c:816-818` - Direct netservice and rshell commands are CMD_DANGEROUS, but the generic service command is CMD_NONE.
- `stage3/linux_init/v101/80_shell_dispatch.inc.c:892-895` - The dispatcher invokes the busy gate with argv[0] and command->flags only, so subcommand/service metadata is not considered.
- `stage3/linux_init/v101/80_shell_dispatch.inc.c:919-956` - Protocol begin/end framing and logging use command->flags, causing dangerous service lifecycle operations through service to be framed as CMD_NONE.
- `stage3/linux_init/a90_controller.c:51-68` - The active-menu controller gate blocks dangerous operations only when the provided flags include CMD_DANGEROUS.
- `stage3/linux_init/a90_config.h:28-31` - Netservice configuration shows NCM interface settings and tcpctl port 2325.
- `stage3/linux_init/a90_netservice.c:149-157` - Netservice spawns the tcpctl helper in listen mode using the configured TCP port.
- `stage3/linux_init/a90_tcpctl.c:284-333` - tcpctl implements the run operation and executes absolute paths via execve.
- `stage3/linux_init/a90_tcpctl.c:517-526` - tcpctl binds its listening socket to INADDR_ANY, exposing it on all device interfaces when started.
- `scripts/revalidation/serial_tcp_bridge.py:16-18` - The host serial bridge defaults to 127.0.0.1:54321, supporting local/USB rather than public-internet default exposure.
## Narrative
The finding is real and reachable in the in-scope PID1 runtime. Service metadata marks tcpctl, adbd, and rshell dangerous/raw-control, and the direct netservice and rshell commands are CMD_DANGEROUS. However, the new generic service command is registered as CMD_NONE while its start/enable paths call a90_netservice_start(), a90_netservice_set_enabled(true), rshell_start_service(true), and rshell_set_enabled(true). The dispatcher passes only command->flags to a90_controller_command_busy_reason, and that controller blocks dangerous commands only when CMD_DANGEROUS is present. Therefore service start tcpctl and service enable rshell bypass the intended dangerous-command gate and are logged/framed as non-dangerous. Impact is meaningful because tcpctl binds INADDR_ANY on port 2325 and supports root execve-based run commands, but severity remains Medium rather than High/Critical because exploitation first requires access to the existing local/USB PID1 control channel and affects a single lab device/control plane rather than an internet-facing fleet.
## Controls
- CMD_DANGEROUS command-table flag
- a90_controller_command_busy_reason active-menu dangerous-command gate
- A90_SERVICE_FLAG_DANGEROUS service metadata
- default serial_tcp_bridge localhost binding
- netservice/tcpctl opt-in helper startup path
- tcpctl absolute-path requirement, timeout, and output cap
## Blindspots
- Static-only review did not verify the full chain on a physical A90 device with NCM enabled.
- Actual deployment state of v101, helper binaries under /cache/bin, and service feature flags cannot be confirmed from repository artifacts alone.
- Real network exposure depends on operator bridge binding, USB/NCM topology, and host firewalling.
- rshell token behavior was not fully traced here; tcpctl provides the clearest demonstrated root run impact.
- Other root shell commands are also powerful and some are not marked CMD_DANGEROUS, which reduces the incremental security delta of this specific bypass.
