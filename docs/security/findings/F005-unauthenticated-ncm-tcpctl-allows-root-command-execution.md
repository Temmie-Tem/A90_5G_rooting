# F005. Unauthenticated NCM tcpctl allows root command execution

## Metadata

| field | value |
|---|---|
| finding_id | `5d3c8e5dc184819184af767a0703442d` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/5d3c8e5dc184819184af767a0703442d |
| severity | `high` |
| status | `new` |
| detected_at | `2026-04-28T09:17:55.445463Z` |
| committed_at | `2026-04-26 00:15:40 +0900` |
| commit_hash | `1e8f6446ed7fecedd5c93b1dd1177ecf1c3a737c` |
| relevant_paths | `stage3/linux_init/a90_tcpctl.c` |
| has_patch | `false` |

## CSV Description

The newly added `a90_tcpctl` helper listens on `INADDR_ANY` and processes remote commands without any authentication or authorization checks. Its `run` command allows clients to execute any absolute-path program via `execve`, effectively granting root-level remote command execution to any party that can reach the listener (e.g., over USB NCM, and potentially any other active interface). The same unauthenticated channel also permits `shutdown`, enabling trivial service DoS. While this may be acceptable in a tightly controlled lab, it is a high-impact security vulnerability if trust boundaries are violated or networking is misconfigured.

## Codex Cloud Detail

Unauthenticated NCM tcpctl allows root command execution
Link: https://chatgpt.com/codex/cloud/security/findings/5d3c8e5dc184819184af767a0703442d
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 1e8f644
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:17:55
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced security bug: unauthenticated adjacent-network command channel with root code execution and unauthenticated shutdown in the new `a90_tcpctl` service.
The newly added `a90_tcpctl` helper listens on `INADDR_ANY` and processes remote commands without any authentication or authorization checks. Its `run` command allows clients to execute any absolute-path program via `execve`, effectively granting root-level remote command execution to any party that can reach the listener (e.g., over USB NCM, and potentially any other active interface). The same unauthenticated channel also permits `shutdown`, enabling trivial service DoS. While this may be acceptable in a tightly controlled lab, it is a high-impact security vulnerability if trust boundaries are violated or networking is misconfigured.

# Validation
## Rubric
- [x] Confirm listener exposure scope includes all interfaces (INADDR_ANY in code and runtime socket evidence).
- [x] Confirm command handling path has no authentication/authorization checks before dispatch.
- [x] Confirm `run` accepts attacker-controlled executable path and reaches `execve`.
- [x] Demonstrate practical unauthenticated impact: remote `run` execution and remote `shutdown`.
- [x] Follow compiled-stack validation order: crash attempt, valgrind/ASan attempt, debugger trace (with documented results).
## Report
I validated the finding on commit 1e8f6446ed7fecedd5c93b1dd1177ecf1c3a737c by building and running stage3/linux_init/a90_tcpctl.c directly.

Build/attempt sequence (compiled-stack flow):
1) Crash attempt (no crash): built debug binary and sent a 5000-byte command line; service handled it and exited cleanly (server_exit=0, log: "tcpctl: served=1 stop=0").
2) Valgrind attempt: unavailable in container ("valgrind: command not found"). I used ASan alternative instead.
3) ASan attempt: built with -fsanitize=address; executed `run /bin/echo ASAN_TEST`; no ASan errors in server output.
4) Debugger trace (lldb, non-interactive): breakpoint at `command_run` hit after network input. Backtrace shows remote command path:
   `main` -> `command_listen` -> `handle_client` -> `command_run`
   (from lldb_trace.log: frames at a90_tcpctl.c:592, :570, :467, :296).

Vulnerability-specific evidence:
- Bind on all interfaces: source sets `addr.sin_addr.s_addr = htonl(INADDR_ANY)` (stage3/linux_init/a90_tcpctl.c:517). Runtime evidence in /proc/net/tcp showed `00000000:B26B` (0.0.0.0:45675).
- No auth gate before command dispatch: `handle_client` reads one line and directly dispatches `run`/`shutdown` with no auth checks (a90_tcpctl.c:441-478).
- Arbitrary program execution: `run` only enforces absolute path (a90_tcpctl.c:303-308), then executes attacker-supplied path via `execve(argv[1], &argv[1], envp)` (a90_tcpctl.c:333).
- Unauthenticated RCE demonstrated: client connected and immediately sent `run /usr/bin/id -u`; response included `0` and `[exit 0]`.
- Unauthenticated DoS/shutdown demonstrated: second client sent `shutdown`; response `OK shutdown`; server log ended with `served=2 stop=1`.

Conclusion: the suspected finding is valid. The new TCP control helper exposes unauthenticated command execution and unauthenticated shutdown over a listener bound to INADDR_ANY.

# Evidence
stage3/linux_init/a90_tcpctl.c (L303 to 308)
  Note: The only gate for `run` is 'absolute path'; this is not a security boundary and still permits arbitrary executable selection.
```
    if (argc < 2) {
        return send_text(client_fd, "ERR usage: run <absolute-path> [args...]\n");
    }
    if (argv[1][0] != '/') {
        return send_text(client_fd, "ERR run path must be absolute\n");
    }
```

stage3/linux_init/a90_tcpctl.c (L333 to 333)
  Note: User-supplied executable path is invoked via `execve`, enabling attacker-controlled command execution.
```
        execve(argv[1], &argv[1], envp);
```

stage3/linux_init/a90_tcpctl.c (L441 to 478)
  Note: Incoming commands are dispatched immediately (`run`, `shutdown`, etc.) without any authorization checks.
```
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
    if (strcmp(argv[0], "quit") == 0) {
        return send_text(client_fd, "OK bye\n");
    }
    if (strcmp(argv[0], "shutdown") == 0) {
        *stop_server = true;
        return send_text(client_fd, "OK shutdown\n");
    }

    return sendf(client_fd, "ERR unknown command: %s\n", argv[0]);
}
```

stage3/linux_init/a90_tcpctl.c (L517 to 518)
  Note: The service binds to all interfaces (`INADDR_ANY`), broadening exposure beyond a single intended interface.
```
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);
```

stage3/linux_init/a90_tcpctl.c (L536 to 570)
  Note: Accept loop handles clients directly with no authentication, token, or source validation before command handling.
```
    while (!stop_server && (max_clients == 0 || served < max_clients)) {
        struct pollfd pfd;
        int poll_rc;
        int client_fd;

        pfd.fd = server_fd;
        pfd.events = POLLIN;
        pfd.revents = 0;

        poll_rc = poll(&pfd, 1, idle_timeout_ms);
        if (poll_rc < 0) {
            if (errno == EINTR) {
                continue;
            }
            fprintf(stderr, "poll: %s\n", strerror(errno));
            close(server_fd);
            return 1;
        }
        if (poll_rc == 0) {
            printf("tcpctl: idle timeout\n");
            break;
        }

        client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) {
                continue;
            }
            fprintf(stderr, "accept: %s\n", strerror(errno));
            close(server_fd);
            return 1;
        }

        ++served;
        handle_client(client_fd, &stop_server);
```

Proposed patch:
diff --git a/stage3/linux_init/a90_tcpctl.c b/stage3/linux_init/a90_tcpctl.c
index d5c641c040b0a9291ee96f8a9c86b84d0b6ddbc7..566a81fd9a2b24bdebfdb14d2d2c55158d6cba61 100644
--- a/stage3/linux_init/a90_tcpctl.c
+++ b/stage3/linux_init/a90_tcpctl.c
@@ -492,102 +492,118 @@ static int command_listen(const char *port_text,
     struct sockaddr_in addr;

     if (parse_u16(port_text, &port) < 0 ||
         parse_nonnegative_int(timeout_text, 3600, &idle_timeout_sec) < 0) {
         fprintf(stderr, "listen: invalid port or timeout\n");
         return 2;
     }

     if (max_clients_text != NULL &&
         parse_nonnegative_int(max_clients_text, 10000, &max_clients) < 0) {
         fprintf(stderr, "listen: invalid max_clients\n");
         return 2;
     }

     idle_timeout_ms = idle_timeout_sec * 1000;
     server_fd = socket(AF_INET, SOCK_STREAM, 0);
     if (server_fd < 0) {
         fprintf(stderr, "socket: %s\n", strerror(errno));
         return 1;
     }

     setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

     memset(&addr, 0, sizeof(addr));
     addr.sin_family = AF_INET;
-    addr.sin_addr.s_addr = htonl(INADDR_ANY);
+    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
     addr.sin_port = htons(port);

     if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
         fprintf(stderr, "bind: %s\n", strerror(errno));
         close(server_fd);
         return 1;
     }

     if (listen(server_fd, 4) < 0) {
         fprintf(stderr, "listen: %s\n", strerror(errno));
         close(server_fd);
         return 1;
     }

     printf("tcpctl: listening port=%u idle_timeout=%ds max_clients=%d\n",
            port, idle_timeout_sec, max_clients);
     fflush(stdout);

     while (!stop_server && (max_clients == 0 || served < max_clients)) {
         struct pollfd pfd;
         int poll_rc;
         int client_fd;
+        struct sockaddr_in peer_addr;
+        socklen_t peer_len = sizeof(peer_addr);

         pfd.fd = server_fd;
         pfd.events = POLLIN;
         pfd.revents = 0;

         poll_rc = poll(&pfd, 1, idle_timeout_ms);
         if (poll_rc < 0) {
             if (errno == EINTR) {
                 continue;
             }
             fprintf(stderr, "poll: %s\n", strerror(errno));
             close(server_fd);
             return 1;
         }
         if (poll_rc == 0) {
             printf("tcpctl: idle timeout\n");
             break;
         }

-        client_fd = accept(server_fd, NULL, NULL);
+        memset(&peer_addr, 0, sizeof(peer_addr));
+        client_fd = accept(server_fd, (struct sockaddr *)&peer_addr, &peer_len);
         if (client_fd < 0) {
             if (errno == EINTR) {
                 continue;
             }
             fprintf(stderr, "accept: %s\n", strerror(errno));
             close(server_fd);
             return 1;
         }

+
+        if (peer_addr.sin_family != AF_INET ||
+            ntohl(peer_addr.sin_addr.s_addr) != INADDR_LOOPBACK) {
+            char peer_text[INET_ADDRSTRLEN] = {0};
+
+            inet_ntop(AF_INET, &peer_addr.sin_addr, peer_text, sizeof(peer_text));
+            fprintf(stderr, "tcpctl: rejected non-loopback client %s\n",
+                    peer_text[0] != '\0' ? peer_text : "<unknown>");
+            shutdown(client_fd, SHUT_RDWR);
+            close(client_fd);
+            continue;
+        }
+
         ++served;
         handle_client(client_fd, &stop_server);
         shutdown(client_fd, SHUT_RDWR);
         close(client_fd);
     }

     close(server_fd);
     printf("tcpctl: served=%d stop=%d\n", served, stop_server ? 1 : 0);
     return 0;
 }

 int main(int argc, char **argv)
 {
     if (argc < 2) {
         usage(argv[0]);
         return 2;
     }

     if (strcmp(argv[1], "listen") == 0) {
         if (argc != 4 && argc != 5) {
             usage(argv[0]);
             return 2;
         }
         return command_listen(argv[2], argv[3], argc == 5 ? argv[4] : NULL);
     }

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept at high: impact is clearly severe (unauthenticated command execution path to `execve`, plus DoS). Not raised to critical because default deployment appears lab/adjacent and opt-in (not broad internet-facing by default), making exploitation preconditions narrower despite low technical exploit complexity.
## Likelihood
medium - Exploitation is trivial once listener is enabled and reachable (single TCP line, no auth). However, exposure is typically adjacent USB/NCM lab scope and requires operator enabling/launching tcpctl.
## Impact
high - If reachable, attacker can execute arbitrary binaries in privileged device runtime and can stop the service via `shutdown`; this is direct integrity/availability compromise with potential full device control in-session.
## Assumptions
- a90_tcpctl is installed and launched as documented (`run /cache/bin/a90_tcpctl listen ...`).
- Attacker can reach the listener over USB NCM or another reachable interface on the device.
- Process runs in the native-init root context (project architecture is custom `/init` PID 1).
- Operator enables USB networking/tcpctl workflow
- Attacker can open TCP connection to configured tcpctl port
- No additional auth barrier is present in protocol
## Path
[Attacker on USB/NCM segment] -> [tcpctl TCP port] -> [no-auth command dispatch] -> [run /abs/path] -> [execve as root / shutdown DoS]
## Path evidence
- `stage3/linux_init/a90_tcpctl.c:517-518` - Listener binds `INADDR_ANY`, widening reach to any interface.
- `stage3/linux_init/a90_tcpctl.c:441-478` - Client command is read and dispatched (`run`, `shutdown`, etc.) without any auth/authz checks.
- `stage3/linux_init/a90_tcpctl.c:303-308` - Only gate on `run` is absolute-path syntax; not a security boundary.
- `stage3/linux_init/a90_tcpctl.c:333` - Attacker-supplied executable path is invoked via `execve`.
- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md:123-135` - Operational example shows tcpctl launched and remotely controlled over NCM TCP.
- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md:188-189` - Project doc explicitly states tcpctl has no authentication.
## Narrative
The finding is real and reachable in normal project workflow when tcpctl is used: `a90_tcpctl` listens on all interfaces, accepts unauthenticated commands, and its `run` command directly calls `execve` on attacker-provided absolute paths. Repo documentation demonstrates launching it over USB NCM and issuing remote `run`/`shutdown` commands. Validation evidence confirms practical unauthenticated command execution (including UID 0 outcome) and shutdown. Impact is major (runtime compromise), but reachability is mainly adjacent/lab-network and opt-in rather than internet-default.
## Controls
- Absolute-path requirement for `run`
- Child timeout (10s) and output cap (128 KiB)
- Idle timeout and max_clients parameters
- Operational guidance labels channel as lab-only and unauthenticated
## Blindspots
- Static-only review cannot confirm all real deployments/network topologies or firewalling around NCM.
- Current head lacks a dedicated `tcpctl_host.py`; operational exposure may vary by external scripts not present here.
- No runtime inventory of which interfaces are active simultaneously when tcpctl is launched.
