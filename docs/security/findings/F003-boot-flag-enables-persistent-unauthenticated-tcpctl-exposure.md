# F003. Boot flag enables persistent unauthenticated tcpctl exposure

## Metadata

| field | value |
|---|---|
| finding_id | `8d331492602c8191a8a283e8314f697f` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/8d331492602c8191a8a283e8314f697f |
| severity | `high` |
| status | `new` |
| detected_at | `2026-04-28T06:48:12.615301Z` |
| committed_at | `2026-04-26 01:28:53 +0900` |
| commit_hash | `224223a78960cc6f9f86edf7991545a4c196dd63` |
| relevant_paths | `stage3/linux_init/init_v60.c | stage3/linux_init/a90_tcpctl.c` |
| has_patch | `false` |

## CSV Description

This commit adds boot-time netservice autostart logic in init_v60 that trusts a writable flag file (`/cache/native-init-netservice`) and executable helpers in `/cache/bin`. If the flag is present, PID1 launches `/cache/bin/a90_usbnet` and `/cache/bin/a90_tcpctl listen ...` automatically during boot. Because `a90_tcpctl` listens on `INADDR_ANY` and exposes an unauthenticated `run <absolute-path>` command, any attacker who can set the flag (or replace helpers) can make root command service reappear on every reboot. This is a persistence and attack-surface expansion introduced by v60 boot policy.

## Codex Cloud Detail

Boot flag enables persistent unauthenticated tcpctl exposure
Link: https://chatgpt.com/codex/cloud/security/findings/8d331492602c8191a8a283e8314f697f
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 224223a
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 3:48:12
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced security bug: persistent boot-time activation of unauthenticated tcpctl via writable /cache policy state and helper path trust. Prior behavior required manual start; v60 makes exposure survive reboot when flag is present.
This commit adds boot-time netservice autostart logic in init_v60 that trusts a writable flag file (`/cache/native-init-netservice`) and executable helpers in `/cache/bin`. If the flag is present, PID1 launches `/cache/bin/a90_usbnet` and `/cache/bin/a90_tcpctl listen ...` automatically during boot. Because `a90_tcpctl` listens on `INADDR_ANY` and exposes an unauthenticated `run <absolute-path>` command, any attacker who can set the flag (or replace helpers) can make root command service reappear on every reboot. This is a persistence and attack-surface expansion introduced by v60 boot policy.

# Validation
## Rubric
- [x] Confirm commit introduces v60 boot-time netservice policy using `/cache/native-init-netservice`.
- [x] Confirm boot path auto-starts netservice when flag is set, not just manual invocation.
- [x] Confirm helpers are executed from mutable `/cache/bin/*` paths.
- [x] Confirm tcpctl listener is network-reachable (`INADDR_ANY`) and `run` command is unauthenticated + executes absolute paths.
- [x] Perform required validation sequence attempts: crash attempt, valgrind/ASan attempt, debugger trace, then code correlation.
## Report
Validated on checked-out commit 224223a78960cc6f9f86edf7991545a4c196dd63.

What I verified in code:
- v60 introduces persistent policy state and helper trust in writable /cache paths: `NETSERVICE_FLAG_PATH` and helper binaries under `/cache/bin` (`stage3/linux_init/init_v60.c:43-47`).
- Boot policy is controlled only by reading `/cache/native-init-netservice` and matching text values (`stage3/linux_init/init_v60.c:4822-4834`).
- If enabled, PID1 path auto-starts netservice at boot (`if (netservice_enabled_flag()) ... netservice_start();`) (`stage3/linux_init/init_v60.c:5848-5853`).
- netservice_start executes `/cache/bin/a90_usbnet`, `/cache/bin/toybox ifconfig`, then spawns `/cache/bin/a90_tcpctl listen ...` (`stage3/linux_init/init_v60.c:4951-4978`, `4878-4917`).
- `a90_tcpctl` exposes `run` with no auth gate (`stage3/linux_init/a90_tcpctl.c:466-468`), accepts arbitrary absolute path and calls `execve(argv[1], ...)` (`a90_tcpctl.c:284-307`, `333`), and binds to `INADDR_ANY` (`a90_tcpctl.c:517-521`).

Dynamic validation performed:
1) Crash attempt (no crash): sent 6000-byte command to debug build.
   - Server log: `tcpctl: served=1 stop=0`, exit 0 (`crash_attempt.log`).
2) Valgrind attempt: unavailable in container (`valgrind_attempt.log`: `bash: command not found: valgrind`).
   - Fallback ASan run succeeded without memory errors; command execution worked (`asan_client.log` showed `[pid ...] ASAN_OK [exit 0] OK`).
3) Debugger trace (lldb, non-interactive) hit `command_run` breakpoint and showed full chain:
   - `main -> command_listen -> handle_client -> command_run` with `argv[0]="run"`, `argv[1]="/bin/echo"` (`lldb_command_run.log`).
   - Corresponding client got command output without authentication (`lldb_client.log`).
4) Direct unauth command PoC:
   - Client sent `run /usr/bin/id` and received `uid=0(root) gid=0(root)` (`unauth_run_id_client.log`).

Prior behavior comparison:
- `init_v59.c` contains no `netservice`/`tcpctl` references (`v59_no_netservice.log`), supporting that v60 introduced this boot-time exposure path.

Conclusion: finding is valid. v60 adds boot-time persistent autostart controlled by writable `/cache` flag and executes helper binaries from `/cache/bin`; once enabled/seeded, unauthenticated tcpctl `run <absolute-path>` is reachable persistently after reboot.

# Evidence
stage3/linux_init/a90_tcpctl.c (L284 to 307)
  Note: run command accepts arbitrary absolute executable path from client (no authentication layer).
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

stage3/linux_init/a90_tcpctl.c (L466 to 468)
  Note: Unauthenticated client command dispatcher exposes the run command.
```
    if (strcmp(argv[0], "run") == 0) {
        return command_run(client_fd, argv, argc);
    }
```

stage3/linux_init/a90_tcpctl.c (L517 to 521)
  Note: tcpctl listener binds to INADDR_ANY, increasing reachability once autostarted.
```
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "bind: %s\n", strerror(errno));
```

stage3/linux_init/init_v60.c (L43 to 47)
  Note: Defines writable /cache flag and helper execution paths used for boot-time netservice policy.
```
#define NETSERVICE_FLAG_PATH "/cache/native-init-netservice"
#define NETSERVICE_LOG_PATH "/cache/native-init-netservice.log"
#define NETSERVICE_USB_HELPER "/cache/bin/a90_usbnet"
#define NETSERVICE_TCPCTL_HELPER "/cache/bin/a90_tcpctl"
#define NETSERVICE_TOYBOX "/cache/bin/toybox"
```

stage3/linux_init/init_v60.c (L4822 to 4834)
  Note: Boot policy decision is based solely on readable flag file content in /cache.
```
static bool netservice_enabled_flag(void) {
    char state[64];

    if (read_trimmed_text_file(NETSERVICE_FLAG_PATH, state, sizeof(state)) < 0) {
        return false;
    }

    return strcmp(state, "1") == 0 ||
           strcmp(state, "on") == 0 ||
           strcmp(state, "enable") == 0 ||
           strcmp(state, "enabled") == 0 ||
           strcmp(state, "ncm") == 0 ||
           strcmp(state, "tcpctl") == 0;
```

stage3/linux_init/init_v60.c (L4951 to 4978)
  Note: On start, PID1 executes /cache helpers and spawns tcpctl, trusting mutable persistent storage.
```
    native_logf("netservice", "start requested");
    if (access(NETSERVICE_USB_HELPER, X_OK) < 0 ||
        access(NETSERVICE_TCPCTL_HELPER, X_OK) < 0 ||
        access(NETSERVICE_TOYBOX, X_OK) < 0) {
        int saved_errno = errno;
        native_logf("netservice", "required helper missing errno=%d error=%s",
                    saved_errno, strerror(saved_errno));
        return -ENOENT;
    }

    rc = netservice_run_wait(usbnet_argv, "a90_usbnet ncm", 15000);
    reattach_console("netservice-ncm", false);
    if (rc < 0) {
        return rc;
    }

    rc = netservice_wait_for_ifname(NETSERVICE_IFNAME, 5000);
    if (rc < 0) {
        return rc;
    }

    rc = netservice_run_wait(ifconfig_argv, "ifconfig ncm0", 5000);
    if (rc < 0) {
        return rc;
    }

    rc = netservice_spawn_tcpctl();
    if (rc < 0) {
```

stage3/linux_init/init_v60.c (L5848 to 5853)
  Note: Boot path auto-starts netservice when flag is set, making service exposure persistent across reboots.
```
        if (netservice_enabled_flag()) {
            int net_rc;

            cprintf("# Netservice: enabled, starting NCM/tcpctl.\r\n");
            net_rc = netservice_start();
            if (net_rc == 0) {
```

Proposed patch:
diff --git a/stage3/linux_init/init_v60.c b/stage3/linux_init/init_v60.c
index bb76543c94bb7ab7f3e00036e1aefe915f28383d..f12f06784da10214a9950504bd78c20f439faea0 100644
--- a/stage3/linux_init/init_v60.c
+++ b/stage3/linux_init/init_v60.c
@@ -5823,78 +5823,46 @@ int main(void) {
     if (attach_console() == 0) {
         mark_step("4_console_attached_v60\n");
         native_logf("boot", "console attached");
         timeline_record(0, 0, "console", "serial console attached");
         drain_console_input(250, 1500);
         cprintf("\r\n# %s\r\n", INIT_BANNER);
         cprintf("# USB ACM serial console ready.\r\n");
         if (start_auto_hud(BOOT_HUD_REFRESH_SECONDS, false) == 0) {
             native_logf("boot", "autohud started refresh=%d", BOOT_HUD_REFRESH_SECONDS);
             timeline_record(0, 0, "autohud", "started refresh=%d", BOOT_HUD_REFRESH_SECONDS);
             cprintf("# Boot display: TEST %ds -> autohud %ds.\r\n",
                     BOOT_TEST_SECONDS,
                     BOOT_HUD_REFRESH_SECONDS);
         } else {
             int saved_errno = errno;

             native_logf("boot", "autohud start failed errno=%d error=%s",
                         saved_errno, strerror(saved_errno));
             timeline_record(-saved_errno,
                             saved_errno,
                             "autohud",
                             "start failed: %s",
                             strerror(saved_errno));
             cprintf("# Boot display: autohud start failed.\r\n");
         }
-        if (netservice_enabled_flag()) {
-            int net_rc;
-
-            cprintf("# Netservice: enabled, starting NCM/tcpctl.\r\n");
-            net_rc = netservice_start();
-            if (net_rc == 0) {
-                mark_step("5_netservice_ok_v60\n");
-                cprintf("# Netservice: NCM %s %s, tcpctl port %s.\r\n",
-                        NETSERVICE_IFNAME,
-                        NETSERVICE_DEVICE_IP,
-                        NETSERVICE_TCP_PORT);
-                klogf("<6>A90v60: netservice started\n");
-            } else {
-                int net_errno = -net_rc;
-
-                if (net_errno < 0) {
-                    net_errno = EIO;
-                }
-                cprintf("# Netservice: start failed rc=%d errno=%d (%s).\r\n",
-                        net_rc,
-                        net_errno,
-                        strerror(net_errno));
-                native_logf("boot", "netservice failed rc=%d errno=%d error=%s",
-                            net_rc, net_errno, strerror(net_errno));
-                timeline_record(net_rc,
-                                net_errno,
-                                "netservice",
-                                "start failed: %s",
-                                strerror(net_errno));
-                klogf("<6>A90v60: netservice failed (%d)\n", net_errno);
-            }
-        } else {
-            native_logf("boot", "netservice disabled flag=%s", NETSERVICE_FLAG_PATH);
-        }
+        native_logf("boot", "netservice autostart disabled");
+        cprintf("# Netservice: disabled at boot (start manually via menu command).\r\n");
         native_logf("boot", "entering shell");
         timeline_record(0, 0, "shell", "interactive shell ready");
         shell_loop();
     } else {
         int saved_errno = errno;
         native_logf("boot", "console attach failed errno=%d error=%s",
                     saved_errno, strerror(saved_errno));
         timeline_record(-saved_errno,
                         saved_errno,
                         "console",
                         "attach failed: %s",
                         strerror(saved_errno));
         klogf("<6>A90v60: console attach failed (%d)\n", saved_errno);
     }

     while (1) {
         sleep(60);
     }
 }

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept at high: impact is clearly major (root command execution + persistence) and code path is directly evidenced. Not raised to critical because default exposure is internal/USB-local and typically needs prior foothold or physical/adjacent access to seed the flag/helper state.
## Likelihood
medium - Exploitation requires plausible but non-trivial preconditions (ability to set flag/modify helpers or one-time command foothold, plus local USB-NCM reachability). It is not internet-exposed by default.
## Impact
high - If reached, attacker can execute arbitrary binaries as root via unauthenticated tcpctl `run`; v60 adds persistence by re-exposing this channel after reboot when flag/helpers are present.
## Assumptions
- Target device is running init_v60 from this commit.
- Attacker can gain one-time ability to set /cache/native-init-netservice or run `netservice enable` via existing control channels.
- USB NCM path (192.168.7.0/24) is reachable from an attached/adjacent host.
- Write access to /cache/native-init-netservice and/or /cache/bin helpers, or one-time shell command execution to run `netservice enable`
- Device reboot (or netservice start) to activate listener
- Network reachability to tcpctl endpoint (default 192.168.7.2:2325 over USB NCM)
## Path
[N1 /cache flag+helpers] -> [N2 boot check] -> [N3 PID1 autostart] -> [N4 0.0.0.0:2325] -> [N5 unauth run => root exec]
## Path evidence
- `stage3/linux_init/init_v60.c:43-47` - Defines persistent flag and helper executables in writable `/cache` paths.
- `stage3/linux_init/init_v60.c:4822-4834` - Boot enablement decision is solely based on readable text flag content.
- `stage3/linux_init/init_v60.c:4851-4853` - Flag file is created in `/cache` (0644), reinforcing persistence mechanism.
- `stage3/linux_init/init_v60.c:4895-4916` - PID1 child execs `/cache/bin/a90_tcpctl listen ...` directly.
- `stage3/linux_init/init_v60.c:5848-5853` - Boot path auto-starts netservice when flag is set.
- `stage3/linux_init/a90_tcpctl.c:517-521` - Listener binds to `INADDR_ANY`, increasing network reachability.
- `stage3/linux_init/a90_tcpctl.c:466-468` - `run` command is exposed in dispatcher with no authentication check.
- `stage3/linux_init/a90_tcpctl.c:303-307` - Only requires absolute path; no authz gate.
- `stage3/linux_init/a90_tcpctl.c:333` - Direct `execve(argv[1], ...)` executes attacker-supplied path.
- `docs/reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md:56` - Documents reachable control endpoint `192.168.7.2:2325` over NCM.
## Narrative
This is a real vulnerability, not a false positive: v60 introduces boot-time autostart based on writable `/cache/native-init-netservice` and executes helpers from `/cache/bin`. When enabled, PID1 launches tcpctl listening on all interfaces and tcpctl accepts unauthenticated `run` requests that call `execve` on attacker-supplied absolute paths. In this project’s lab model, reachability is usually USB-local (NCM), so exploitation likelihood is medium rather than internet-high; however impact is high because successful use gives root command execution and persistence across reboots.
## Controls
- Netservice default OFF unless flag exists
- Absolute-path requirement for `run` command
- tcpctl runtime/output limits (timeout, output cap, max_clients)
- Host serial bridge defaults to localhost for ACM path
## Blindspots
- Static review cannot prove deployed filesystem ownership/SELinux policy for `/cache`; if only root-writable, precondition is stronger.
- No runtime network topology verification; INADDR_ANY risk depends on which interfaces are actually up in deployment.
- Validation logs were provided in prior stage summary, but artifact binaries on target devices could differ from repo source.
