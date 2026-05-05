# F001. rshell start exposes unauthenticated tcpctl root command port

## Metadata

| field | value |
|---|---|
| finding_id | `6c6868a5a51481918710b5c0a6401801` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/6c6868a5a51481918710b5c0a6401801 |
| severity | `high` |
| status | `new` |
| detected_at | `2026-05-04T10:30:58.912130Z` |
| committed_at | `2026-05-03 23:23:18 +0900` |
| commit_hash | `27afbc3f13869206f1e03a3c4e2fbe1a097fd1e0` |
| relevant_paths | `stage3/linux_init/v100/70_storage_android_net.inc.c | stage3/linux_init/a90_netservice.c | stage3/linux_init/a90_tcpctl.c` |
| has_patch | `false` |

## CSV Description

The v100 rshell command is presented as a token-authenticated remote shell on port 2326. However, rshell_start_service() checks whether NCM is present and, if not, calls a90_netservice_start(). That function does more than configure USB NCM: it also spawns a90_tcpctl on port 2325. a90_tcpctl binds to INADDR_ANY and its protocol has no authentication step; clients can immediately issue run <absolute-path> [args...] and the service execve()s that program as the native init/root environment. Therefore an attacker who can reach the USB NCM network can ignore the rshell token entirely and connect to tcpctl port 2325 for unauthenticated root command execution whenever an operator starts/enables rshell. This is introduced by the new rshell integration path, even though tcpctl itself pre-existed.

## Codex Cloud Detail

rshell start exposes unauthenticated tcpctl root command port
Link: https://chatgpt.com/codex/cloud/security/findings/6c6868a5a51481918710b5c0a6401801
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 27afbc3
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:30:58
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced: rshell_start_service() implicitly starts netservice as a dependency, and netservice unconditionally starts the unauthenticated tcpctl root command service. This undermines the security boundary promised by rshell token authentication.
The v100 rshell command is presented as a token-authenticated remote shell on port 2326. However, rshell_start_service() checks whether NCM is present and, if not, calls a90_netservice_start(). That function does more than configure USB NCM: it also spawns a90_tcpctl on port 2325. a90_tcpctl binds to INADDR_ANY and its protocol has no authentication step; clients can immediately issue run <absolute-path> [args...] and the service execve()s that program as the native init/root environment. Therefore an attacker who can reach the USB NCM network can ignore the rshell token entirely and connect to tcpctl port 2325 for unauthenticated root command execution whenever an operator starts/enables rshell. This is introduced by the new rshell integration path, even though tcpctl itself pre-existed.

# Validation
## Rubric
- [x] Confirm v100 rshell startup invokes netservice automatically when NCM is absent.
- [x] Confirm `a90_netservice_start()` unconditionally starts tcpctl on the configured tcpctl port.
- [x] Confirm tcpctl binds broadly enough to be reachable over the NCM interface.
- [x] Confirm tcpctl has no authentication before accepting `run <absolute-path>`.
- [x] Confirm with a live PoC/debugger trace that a TCP client can trigger `execve()` without presenting an rshell token.
## Report
Validated the finding. Code path evidence: commit 27afbc3 adds the v100 rshell integration; `stage3/linux_init/helpers/a90_rshell.c` and `stage3/linux_init/v100/70_storage_android_net.inc.c` are new in HEAD. The v100 report describes rshell as token-authenticated on `192.168.7.2:2326` (`docs/reports/NATIVE_INIT_V100_REMOTE_SHELL_2026-05-03.md:7-10`). In `rshell_start_service()`, when NCM is absent, the code calls `a90_netservice_start()` before launching rshell (`stage3/linux_init/v100/70_storage_android_net.inc.c:869-877`), then starts the token-authenticated helper on `A90_RSHELL_BIND_ADDR:A90_RSHELL_PORT` (`stage3/linux_init/v100/70_storage_android_net.inc.c:879-891`). `a90_netservice_start()` unconditionally reaches `netservice_spawn_tcpctl()` after USB NCM setup (`stage3/linux_init/a90_netservice.c:202-246`), and `netservice_spawn_tcpctl()` spawns `NETSERVICE_TCPCTL_HELPER listen NETSERVICE_TCP_PORT ...` (`stage3/linux_init/a90_netservice.c:149-156`), where `NETSERVICE_TCP_PORT` is `2325` (`stage3/linux_init/a90_config.h:31`). tcpctl binds to `INADDR_ANY` (`stage3/linux_init/a90_tcpctl.c:515-518`). Its client handler sends a ready banner, reads a command, and dispatches `run` directly with no authentication gate (`stage3/linux_init/a90_tcpctl.c:434-468`). `command_run()` only requires an absolute path (`stage3/linux_init/a90_tcpctl.c:303-307`) and then calls `execve(argv[1], &argv[1], envp)` (`stage3/linux_init/a90_tcpctl.c:323-334`). Dynamic validation: compiled the actual `a90_tcpctl.c` with `gcc -O0 -g` and connected as a TCP client; sending `run /usr/bin/id` immediately returned `uid=0(root) gid=0(root) groups=0(root)` with no token/auth exchange. Debugger validation: LLDB breakpoint at `a90_tcpctl.c:333` after sending the same unauthenticated command produced a backtrace `main -> command_listen -> handle_client -> command_run -> execve`, proving the network command reaches privileged exec. Crash/Valgrind attempts: this is an auth-bypass/design vulnerability, so no crash is expected; the direct exploit did not crash. `valgrind` and `gdb` were not installed in the container; I used an ASan build as a bounded substitute, which reproduced command execution and emitted no sanitizer error. Actual Android USB NCM device startup was not run in-container because it depends on device-only `/cache/bin/a90_usbnet`, toybox, and interface creation, but the deterministic source path from rshell to netservice to tcpctl plus runtime tcpctl execution validates the issue.

# Evidence
stage3/linux_init/a90_netservice.c (L149 to 199)
  Note: netservice_spawn_tcpctl() starts the tcpctl helper on NETSERVICE_TCP_PORT.
```
static int netservice_spawn_tcpctl(void) {
    static char *const argv[] = {
        NETSERVICE_TCPCTL_HELPER,
        "listen",
        NETSERVICE_TCP_PORT,
        NETSERVICE_TCP_IDLE_SECONDS,
        NETSERVICE_TCP_MAX_CLIENTS,
        NULL
    };
    static char *const envp[] = {
        "PATH=/cache/bin:/cache:/bin:/system/bin",
        "HOME=/",
        "TERM=vt100",
        NULL
    };
    struct a90_run_config config = {
        .tag = "tcpctl",
        .argv = argv,
        .envp = envp,
        .stdio_mode = A90_RUN_STDIO_LOG_APPEND,
        .log_path = NETSERVICE_LOG_PATH,
        .setsid = true,
        .ignore_hup_pipe = true,
        .stop_timeout_ms = 2000,
    };
    pid_t pid;
    int status = 0;
    int rc;

    a90_netservice_reap();
    if (a90_service_pid(A90_SERVICE_TCPCTL) > 0) {
        a90_logf("netservice", "tcpctl already running pid=%ld",
                    (long)a90_service_pid(A90_SERVICE_TCPCTL));
        return 0;
    }

    rc = a90_run_spawn(&config, &pid);
    if (rc < 0) {
        return rc;
    }
    a90_service_set_pid(A90_SERVICE_TCPCTL, pid);

    usleep(200000);
    if (a90_service_reap(A90_SERVICE_TCPCTL, &status) > 0) {
        a90_logf("netservice", "tcpctl exited immediately pid=%ld", (long)pid);
        return -EIO;
    }

    a90_logf("netservice", "tcpctl started pid=%ld port=%s",
                (long)pid, NETSERVICE_TCP_PORT);
    return 0;
```

stage3/linux_init/a90_netservice.c (L202 to 247)
  Note: a90_netservice_start() configures NCM and then unconditionally calls netservice_spawn_tcpctl(), so rshell's dependency startup exposes tcpctl.
```
int a90_netservice_start(void) {
    char *const usbnet_argv[] = {
        NETSERVICE_USB_HELPER,
        "ncm",
        NULL
    };
    char *const ifconfig_argv[] = {
        NETSERVICE_TOYBOX,
        "ifconfig",
        NETSERVICE_IFNAME,
        NETSERVICE_DEVICE_IP,
        "netmask",
        NETSERVICE_NETMASK,
        "up",
        NULL
    };
    int rc;

    a90_logf("netservice", "start requested");
    if (access(NETSERVICE_USB_HELPER, X_OK) < 0 ||
        access(NETSERVICE_TCPCTL_HELPER, X_OK) < 0 ||
        access(NETSERVICE_TOYBOX, X_OK) < 0) {
        int saved_errno = errno;
        a90_logf("netservice", "required helper missing errno=%d error=%s",
                    saved_errno, strerror(saved_errno));
        return -ENOENT;
    }

    rc = netservice_run_wait(usbnet_argv, "a90_usbnet ncm", 15000);
    a90_console_reattach("netservice-ncm", false);
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

stage3/linux_init/a90_tcpctl.c (L284 to 307)
  Note: The unauthenticated run command accepts an absolute executable path for command execution.
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

stage3/linux_init/a90_tcpctl.c (L323 to 334)
  Note: tcpctl executes the requested program with execve(), inheriting the privileged service context.
```
    if (pid == 0) {
        close(pipefd[0]);
        devnull = open("/dev/null", O_RDONLY);
        if (devnull >= 0) {
            dup2(devnull, STDIN_FILENO);
            close(devnull);
        }
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);
        execve(argv[1], &argv[1], envp);
        dprintf(STDERR_FILENO, "execve(%s): %s\n", argv[1], strerror(errno));
```

stage3/linux_init/a90_tcpctl.c (L434 to 468)
  Note: tcpctl handles client commands immediately without any authentication check; the run command is accepted directly.
```
static int handle_client(int client_fd, bool *stop_server)
{
    char line[MAX_LINE];
    char *argv[MAX_ARGS];
    int argc;
    int rc;

    send_text(client_fd, TCPCTL_VERSION " ready\n");
    rc = read_line(client_fd, line, sizeof(line), 15000);
    if (rc < 0) {
        return sendf(client_fd, "ERR read=%d\n", rc);
    }

    argc = split_args(line, argv, MAX_ARGS);
    if (argc == 0) {
        return send_text(client_fd, "ERR empty\n");
    }

    if (strcmp(argv[0], "help") == 0) {
        return command_help(client_fd);
    }
    if (strcmp(argv[0], "ping") == 0) {
        send_text(client_fd, "pong\n");
        return send_text(client_fd, "OK\n");
    }
    if (strcmp(argv[0], "version") == 0) {
        send_text(client_fd, TCPCTL_VERSION "\n");
        return send_text(client_fd, "OK\n");
    }
    if (strcmp(argv[0], "status") == 0) {
        return command_status(client_fd);
    }
    if (strcmp(argv[0], "run") == 0) {
        return command_run(client_fd, argv, argc);
    }
```

stage3/linux_init/a90_tcpctl.c (L515 to 518)
  Note: tcpctl binds to INADDR_ANY, making it reachable on the NCM interface once netservice is started.
```
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);
```

stage3/linux_init/v100/70_storage_android_net.inc.c (L869 to 877)
  Note: The new rshell startup path automatically calls a90_netservice_start() when NCM is not already present, which also starts tcpctl.
```
    a90_netservice_status(&net_status);
    if (!net_status.ncm_present) {
        a90_console_printf("rshell: starting NCM netservice first\r\n");
        rc = a90_netservice_start();
        if (rc < 0) {
            a90_console_printf("rshell: netservice start failed rc=%d\r\n", rc);
            return rc;
        }
    }
```

stage3/linux_init/v100/70_storage_android_net.inc.c (L879 to 891)
  Note: After starting netservice, rshell launches the token-protected helper on port 2326, but the unauthenticated tcpctl service is already exposed as a side effect.
```
    child_argv[0] = (char *)helper_path;
    child_argv[1] = (char *)A90_RSHELL_BIND_ADDR;
    child_argv[2] = (char *)A90_RSHELL_PORT;
    child_argv[3] = token_path;
    child_argv[4] = (char *)busybox_path;
    child_argv[5] = (char *)A90_RSHELL_IDLE_SECONDS;
    child_argv[6] = NULL;
    memset(&config, 0, sizeof(config));
    config.tag = "rshell";
    config.argv = child_argv;
    config.envp = envp;
    config.stdio_mode = A90_RUN_STDIO_LOG_APPEND;
    config.log_path = A90_RSHELL_LOG_PATH;
```

Proposed patch:
diff --git a/stage3/linux_init/a90_netservice.c b/stage3/linux_init/a90_netservice.c
index d7fbebafaba2a0ef4fcda6a4795adb60c64c2cb8..1f79c1bc456e69710d7b9c3fee541980e5d9aab6 100644
--- a/stage3/linux_init/a90_netservice.c
+++ b/stage3/linux_init/a90_netservice.c
@@ -177,106 +177,120 @@ static int netservice_spawn_tcpctl(void) {

     a90_netservice_reap();
     if (a90_service_pid(A90_SERVICE_TCPCTL) > 0) {
         a90_logf("netservice", "tcpctl already running pid=%ld",
                     (long)a90_service_pid(A90_SERVICE_TCPCTL));
         return 0;
     }

     rc = a90_run_spawn(&config, &pid);
     if (rc < 0) {
         return rc;
     }
     a90_service_set_pid(A90_SERVICE_TCPCTL, pid);

     usleep(200000);
     if (a90_service_reap(A90_SERVICE_TCPCTL, &status) > 0) {
         a90_logf("netservice", "tcpctl exited immediately pid=%ld", (long)pid);
         return -EIO;
     }

     a90_logf("netservice", "tcpctl started pid=%ld port=%s",
                 (long)pid, NETSERVICE_TCP_PORT);
     return 0;
 }

-int a90_netservice_start(void) {
+static int netservice_start(bool start_tcpctl) {
     char *const usbnet_argv[] = {
         NETSERVICE_USB_HELPER,
         "ncm",
         NULL
     };
     char *const ifconfig_argv[] = {
         NETSERVICE_TOYBOX,
         "ifconfig",
         NETSERVICE_IFNAME,
         NETSERVICE_DEVICE_IP,
         "netmask",
         NETSERVICE_NETMASK,
         "up",
         NULL
     };
     int rc;

     a90_logf("netservice", "start requested");
     if (access(NETSERVICE_USB_HELPER, X_OK) < 0 ||
         access(NETSERVICE_TCPCTL_HELPER, X_OK) < 0 ||
         access(NETSERVICE_TOYBOX, X_OK) < 0) {
         int saved_errno = errno;
         a90_logf("netservice", "required helper missing errno=%d error=%s",
                     saved_errno, strerror(saved_errno));
         return -ENOENT;
     }

     rc = netservice_run_wait(usbnet_argv, "a90_usbnet ncm", 15000);
     a90_console_reattach("netservice-ncm", false);
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

-    rc = netservice_spawn_tcpctl();
-    if (rc < 0) {
-        return rc;
-    }
+    if (start_tcpctl) {
+        rc = netservice_spawn_tcpctl();
+        if (rc < 0) {
+            return rc;
+        }

-    a90_timeline_record(0, 0, "netservice", "ncm=%s tcp=%s",
-                    NETSERVICE_IFNAME, NETSERVICE_TCP_PORT);
-    a90_logf("netservice", "ready if=%s ip=%s port=%s",
-                NETSERVICE_IFNAME, NETSERVICE_DEVICE_IP, NETSERVICE_TCP_PORT);
+        a90_timeline_record(0, 0, "netservice", "ncm=%s tcp=%s",
+                        NETSERVICE_IFNAME, NETSERVICE_TCP_PORT);
+        a90_logf("netservice", "ready if=%s ip=%s port=%s",
+                    NETSERVICE_IFNAME, NETSERVICE_DEVICE_IP, NETSERVICE_TCP_PORT);
+    } else {
+        a90_timeline_record(0, 0, "netservice", "ncm=%s", NETSERVICE_IFNAME);
+        a90_logf("netservice", "ready if=%s ip=%s (tcpctl skipped)",
+                    NETSERVICE_IFNAME, NETSERVICE_DEVICE_IP);
+    }
     return 0;
 }

+int a90_netservice_start(void) {
+    return netservice_start(true);
+}
+
+int a90_netservice_start_ncm_only(void) {
+    return netservice_start(false);
+}
+
 int a90_netservice_stop(void) {
     char *const usbnet_argv[] = {
         NETSERVICE_USB_HELPER,
         "off",
         NULL
     };
     int rc = 0;

     a90_logf("netservice", "stop requested");
     a90_netservice_reap();
     if (a90_service_pid(A90_SERVICE_TCPCTL) > 0) {
         pid_t pid = a90_service_pid(A90_SERVICE_TCPCTL);

         (void)a90_service_stop(A90_SERVICE_TCPCTL, 2000);
         a90_logf("netservice", "tcpctl stopped pid=%ld", (long)pid);
     }

     if (access(NETSERVICE_USB_HELPER, X_OK) == 0) {
         rc = netservice_run_wait(usbnet_argv, "a90_usbnet off", 15000);
         a90_console_reattach("netservice-off", false);
     }

     return rc;
 }



diff --git a/stage3/linux_init/a90_netservice.h b/stage3/linux_init/a90_netservice.h
index 4549264270fc04a56ff43689abed307d3fe2e544..58d525850dd672c5404349891b379db5f383d47b 100644
--- a/stage3/linux_init/a90_netservice.h
+++ b/stage3/linux_init/a90_netservice.h
@@ -3,30 +3,31 @@

 #include <stdbool.h>
 #include <sys/types.h>

 struct a90_netservice_status {
     bool enabled;
     bool usbnet_helper;
     bool tcpctl_helper;
     bool toybox_helper;
     bool ncm_present;
     bool tcpctl_running;
     pid_t tcpctl_pid;
     const char *flag_path;
     const char *log_path;
     const char *ifname;
     const char *device_ip;
     const char *netmask;
     const char *tcp_port;
     const char *tcp_idle_seconds;
     const char *tcp_max_clients;
 };

 bool a90_netservice_enabled(void);
 int a90_netservice_set_enabled(bool enabled);
 int a90_netservice_start(void);
+int a90_netservice_start_ncm_only(void);
 int a90_netservice_stop(void);
 void a90_netservice_reap(void);
 int a90_netservice_status(struct a90_netservice_status *out);

 #endif


diff --git a/stage3/linux_init/v100/70_storage_android_net.inc.c b/stage3/linux_init/v100/70_storage_android_net.inc.c
index 66483e64ff95b5de13095f3c6ca95f96dd491e77..2555e0585ac61e03d05f40f6760f1e372e9f794c 100644
--- a/stage3/linux_init/v100/70_storage_android_net.inc.c
+++ b/stage3/linux_init/v100/70_storage_android_net.inc.c
@@ -847,51 +847,51 @@ static int rshell_start_service(bool print_token) {

     helper_path = a90_helper_preferred_path("a90_rshell", A90_RSHELL_RAMDISK_HELPER);
     busybox_path = a90_userland_path("busybox");
     if (busybox_path == NULL || busybox_path[0] == '\0') {
         busybox_path = a90_helper_preferred_path("busybox", A90_BUSYBOX_HELPER);
     }
     if (helper_path == NULL || helper_path[0] == '\0' || access(helper_path, X_OK) < 0) {
         a90_console_printf("rshell: helper missing: %s\r\n",
                 helper_path != NULL && helper_path[0] != '\0' ? helper_path : "a90_rshell");
         return -ENOENT;
     }
     if (busybox_path == NULL || busybox_path[0] == '\0' || access(busybox_path, X_OK) < 0) {
         a90_console_printf("rshell: busybox shell missing\r\n");
         return -ENOENT;
     }

     rc = rshell_ensure_token(token, sizeof(token), print_token);
     if (rc < 0) {
         return rc;
     }
     rshell_state_path(token_path, sizeof(token_path), A90_RSHELL_TOKEN_NAME);

     a90_netservice_status(&net_status);
     if (!net_status.ncm_present) {
         a90_console_printf("rshell: starting NCM netservice first\r\n");
-        rc = a90_netservice_start();
+        rc = a90_netservice_start_ncm_only();
         if (rc < 0) {
             a90_console_printf("rshell: netservice start failed rc=%d\r\n", rc);
             return rc;
         }
     }

     child_argv[0] = (char *)helper_path;
     child_argv[1] = (char *)A90_RSHELL_BIND_ADDR;
     child_argv[2] = (char *)A90_RSHELL_PORT;
     child_argv[3] = token_path;
     child_argv[4] = (char *)busybox_path;
     child_argv[5] = (char *)A90_RSHELL_IDLE_SECONDS;
     child_argv[6] = NULL;
     memset(&config, 0, sizeof(config));
     config.tag = "rshell";
     config.argv = child_argv;
     config.envp = envp;
     config.stdio_mode = A90_RUN_STDIO_LOG_APPEND;
     config.log_path = A90_RSHELL_LOG_PATH;
     config.setsid = true;
     config.ignore_hup_pipe = true;
     config.kill_process_group = true;
     config.stop_timeout_ms = 2000;

     rc = a90_run_spawn(&config, &pid);

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
The original high severity is appropriate. The code evidence shows a concrete reachable chain from normal rshell operation to an unauthenticated tcpctl listener and then to privileged execve. The validation evidence further reports an executable PoC against the actual tcpctl source returning root `id` output without a token. Impact is high because this is root-equivalent command execution and authentication bypass. It is not raised to critical because exposure is limited to USB NCM/local-network reachability, rshell/netservice is disabled until an operator starts/enables it, and there is no evidence of default Internet-facing or fleet-wide exposure. It should not be lowered because the affected component is the main privileged device runtime and the bypass undermines a newly introduced token-authenticated remote shell boundary.
## Likelihood
medium - Exploitation is simple after exposure: connect to port 2325 and send a `run` command with no credentials. However, the service is not Internet-public by default; it requires v100 rshell/netservice to be started and attacker reachability to the USB NCM/local link. Those preconditions are plausible in the project threat model but reduce likelihood compared with a public remote service.
## Impact
high - Successful exploitation gives an unauthenticated local-network client the ability to execute arbitrary absolute-path programs in the privileged native init/root device context. This can compromise confidentiality, integrity, and availability of the rooted device and defeats the intended rshell token-authenticated control boundary.
## Assumptions
- The v100 native init image is built/flashed and used as the device runtime.
- An operator starts or enables rshell, or an enabled rshell flag causes it to start in normal operation.
- The attacker can reach the USB NCM network path to the device, for example from the connected host, a compromised/shared lab host, or another reachable local link segment.
- The spawned native init helpers execute in the privileged/root device context unless explicitly dropped; the reviewed spawn paths do not show privilege dropping.
- v100 rshell code path present in runtime image
- rshell start or enable is invoked
- NCM is absent at rshell start so rshell calls a90_netservice_start, or netservice/tcpctl is otherwise running
- attacker has reachability to device TCP port 2325 on the USB NCM/local network
## Path
operator rshell start/enable
        |
        v
rshell_start_service()
        |
        | if NCM absent
        v
a90_netservice_start()
        |
        v
netservice_spawn_tcpctl() -> tcpctl listen 0.0.0.0:2325
                                      |
                                      v
                         attacker sends: run /absolute/path
                                      |
                                      v
                         execve() in privileged root context
## Path evidence
- `docs/reports/NATIVE_INIT_V100_REMOTE_SHELL_2026-05-03.md:7-10` - Documents v100 rshell as a token-authenticated TCP remote shell over USB NCM on 192.168.7.2:2326 and disabled by default.
- `stage3/linux_init/helpers/a90_rshell.c:285-298` - The intended rshell service requires an `AUTH` token before proceeding, establishing the authentication boundary that tcpctl bypasses.
- `stage3/linux_init/v100/70_storage_android_net.inc.c:869-877` - rshell_start_service starts NCM by calling a90_netservice_start when NCM is not already present.
- `stage3/linux_init/v100/70_storage_android_net.inc.c:879-891` - After starting netservice, rshell launches the token-protected helper on port 2326, leaving netservice side effects active.
- `stage3/linux_init/a90_netservice.c:149-199` - netservice_spawn_tcpctl constructs and spawns the tcpctl helper with `listen` and NETSERVICE_TCP_PORT.
- `stage3/linux_init/a90_netservice.c:202-247` - a90_netservice_start configures NCM and then unconditionally reaches netservice_spawn_tcpctl.
- `stage3/linux_init/a90_config.h:28-38` - Defines NCM interface/IP and ports: tcpctl on 2325 and rshell on 2326.
- `stage3/linux_init/a90_tcpctl.c:515-518` - tcpctl binds to INADDR_ANY, making it reachable on available interfaces including the NCM network.
- `stage3/linux_init/a90_tcpctl.c:434-468` - tcpctl client handler reads one command and dispatches `run` directly; there is no authentication step before command dispatch.
- `stage3/linux_init/a90_tcpctl.c:284-334` - The `run` command only requires an absolute path and then calls execve on attacker-controlled argv[1].
- `stage3/linux_init/v100/80_shell_dispatch.inc.c:575-578` - rshell is registered as a v100 shell command, showing the vulnerable startup path is reachable through the product's command interface.
## Narrative
This is a real, in-scope vulnerability. The v100 remote shell is documented as token-authenticated on 192.168.7.2:2326, and the helper enforces an `AUTH` token exchange. However, the rshell startup path calls `a90_netservice_start()` when NCM is absent. That netservice startup path unconditionally calls `netservice_spawn_tcpctl()`, which launches tcpctl on NETSERVICE_TCP_PORT 2325. tcpctl binds to INADDR_ANY, reads a client command, dispatches `run` without any authentication check, and `command_run()` forks and `execve()`s the attacker-supplied absolute path. The main mitigating factors are that the exposure is local/USB NCM rather than Internet-facing and requires rshell/netservice to be started. The impact is still high because a reachable unauthenticated client obtains root-equivalent command execution and bypasses the token boundary that rshell introduced.
## Controls
- rshell itself has token authentication
- rshell is documented as disabled by default
- USB NCM/local network reachability is required
- tcpctl has run timeout and output cap controls
- tcpctl requires an absolute executable path
- no tcpctl authentication or authorization gate is present
- tcpctl binds INADDR_ANY
## Blindspots
- Static repository review cannot confirm the exact deployed Android device networking/firewall state.
- The full USB NCM device startup path depends on device-only helpers under /cache/bin and was not re-executed in this static pass.
- No cloud, Kubernetes, load balancer, or IaC artifacts are present for broader exposure analysis.
- Severity depends on operational context: isolated single-operator bench use reduces likelihood, while shared labs or exposed NCM/host networking increase it.
