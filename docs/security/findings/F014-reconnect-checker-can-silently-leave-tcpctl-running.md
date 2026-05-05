# F014. Reconnect checker can silently leave tcpctl running

## Metadata

| field | value |
|---|---|
| finding_id | `bc3091e8d83c81918552221cb20b212e` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/bc3091e8d83c81918552221cb20b212e |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T17:41:32.155879Z` |
| committed_at | `2026-04-27 03:13:15 +0900` |
| commit_hash | `8a6cc510c88316ef432b039951aba6e964ac2813` |
| relevant_paths | `scripts/revalidation/physical_usb_reconnect_check.py | scripts/revalidation/netservice_reconnect_soak.py | stage3/linux_init/a90_tcpctl.c` |
| has_patch | `false` |

## CSV Description

In `physical_usb_reconnect_check.py`, the script may auto-start netservice (which enables NCM + tcpctl) and later attempts to restore ACM-only mode in a `finally` block. However, shutdown errors are caught and only logged, not propagated. This means the script can exit with success after reporting PASS while cleanup failed, leaving `tcpctl` active unexpectedly. Because `tcpctl` listens on `INADDR_ANY` and supports `run <absolute-path> ...` command execution as root, this fail-open cleanup behavior can unintentionally expand attack surface after a test run.

## Codex Cloud Detail

Reconnect checker can silently leave tcpctl running
Link: https://chatgpt.com/codex/cloud/security/findings/bc3091e8d83c81918552221cb20b212e
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 8a6cc51
Author: shs02140@gmail.com
Created: 2026. 4. 29. 오전 2:41:32
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced security bug: fail-open cleanup/error suppression in the newly added reconnect validation script. The script starts netservice when needed, but suppresses stop failures, so operators may believe the device returned to safer ACM-only mode when it did not.
In `physical_usb_reconnect_check.py`, the script may auto-start netservice (which enables NCM + tcpctl) and later attempts to restore ACM-only mode in a `finally` block. However, shutdown errors are caught and only logged, not propagated. This means the script can exit with success after reporting PASS while cleanup failed, leaving `tcpctl` active unexpectedly. Because `tcpctl` listens on `INADDR_ANY` and supports `run <absolute-path> ...` command execution as root, this fail-open cleanup behavior can unintentionally expand attack surface after a test run.

# Validation
## Rubric
- [x] Confirm commit-introduced control flow in `physical_usb_reconnect_check.py` can return success before cleanup and suppress cleanup exceptions (lines 87-110).
- [x] Confirm `stop_netservice()` is designed to raise on unsafe post-stop state (`tcpctl=running`) in `netservice_reconnect_soak.py` (lines 371-389).
- [x] Attempt crash-style execution path: ran PoC and observed no crash but incorrect success exit (`POC_RETURN_CODE=0`) despite simulated cleanup failure.
- [x] Attempt valgrind method: unavailable in container (`valgrind: command not found`), recorded in artifact log.
- [x] Attempt debugger method non-interactively (pdb): executed PoC under debugger and observed same fail-open behavior without propagated exception.
## Report
Validated as a real fail-open behavior introduced in commit 8a6cc510c88316ef432b039951aba6e964ac2813. In scripts/revalidation/physical_usb_reconnect_check.py:87-110, run_once() returns 0 after logging PASS, then in finally catches and suppresses any stop_netservice() exception. I reproduced this with a targeted PoC by monkeypatching hardware-dependent functions and forcing stop_netservice to raise RuntimeError. Command/output evidence: `python3 /workspace/validation_artifacts/work_physical_usb/poc_fail_open_cleanup.py` prints PASS, then `restore stop failed; ...`, and ends with `POC_RETURN_CODE=0` (also EXIT_CODE=0 in output_crash_attempt.log). This demonstrates success is reported even when cleanup fails. I also validated that stop_netservice() failures are meaningful: scripts/revalidation/netservice_reconnect_soak.py:371-389 explicitly raises RuntimeError when status is not `ncm0=absent` and `tcpctl=stopped`; PoC `poc_stop_netservice_raises.py` produced `RuntimeError netservice did not stop cleanly: ... tcpctl=running`. Impact relevance is supported by stage3/linux_init/a90_tcpctl.c:466-468 (supports `run` command execution) and 515-518 (binds listener to INADDR_ANY). Attempts for preferred methods: crash attempt executed (no crash; logical vuln), valgrind attempted but unavailable (`command not found`), non-interactive debugger attempt with pdb executed and showed same suppressed-error flow.

# Evidence
scripts/revalidation/netservice_reconnect_soak.py (L351 to 389)
  Note: Shows that starting netservice requires `tcpctl=running`, and stopping netservice raises if `tcpctl` is not stopped; these exceptions are swallowed by the new script.
```
def start_netservice(args: argparse.Namespace) -> None:
    log("starting netservice; USB may re-enumerate")
    try:
        output = device_command(
            args,
            "netservice start",
            timeout=args.netservice_timeout,
            tolerate_disconnect=True,
            use_cmdv1=False,
        )
        print(output, end="" if output.endswith("\n") else "\n")
    except RuntimeError as exc:
        log(f"netservice start output interrupted; checking state next: {exc}")

    wait_for_bridge_version(args)
    status_output = netservice_status(args)
    if "ncm0=present" not in status_output or "tcpctl=running" not in status_output:
        raise RuntimeError(f"netservice did not report ready:\n{status_output}")


def stop_netservice(args: argparse.Namespace) -> None:
    log("stopping netservice; USB may re-enumerate")
    try:
        output = device_command(
            args,
            "netservice stop",
            timeout=args.netservice_timeout,
            tolerate_disconnect=True,
            allow_error=True,
            use_cmdv1=False,
        )
        print(output, end="" if output.endswith("\n") else "\n")
    except RuntimeError as exc:
        log(f"netservice stop output interrupted; checking bridge next: {exc}")

    wait_for_bridge_version(args)
    status_output = netservice_status(args)
    if "ncm0=absent" not in status_output or "tcpctl=stopped" not in status_output:
        raise RuntimeError(f"netservice did not stop cleanly:\n{status_output}")
```

scripts/revalidation/physical_usb_reconnect_check.py (L91 to 110)
  Note: Script can start netservice, then suppresses exceptions from `stop_netservice()` in cleanup; this can hide failure and still allow success return.
```
        started_netservice = ensure_netservice_ready(args)

        initial_devices = acm_devices()
        print_replug_instruction(args, initial_devices)
        wait_for_acm_disconnect(initial_devices, args.disconnect_timeout)
        time.sleep(args.post_disconnect_sleep)

        print(wait_for_bridge_after_replug(args), end="")
        time.sleep(args.post_replug_sleep)
        verify_post_replug(args)

        log("PASS: ACM bridge, NCM ping, and tcpctl survived physical reconnect")
        return 0
    finally:
        if started_netservice and not args.leave_running:
            log("restoring ACM-only state because this script started netservice")
            try:
                stop_netservice(args)
            except Exception as exc:
                log(f"restore stop failed; check bridge manually: {exc}")
```

stage3/linux_init/a90_tcpctl.c (L466 to 518)
  Note: tcpctl handles `run` commands and binds listener to `INADDR_ANY`, so leaving it running unexpectedly materially increases remote command-execution exposure.
```
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

static int command_listen(const char *port_text,
                          const char *timeout_text,
                          const char *max_clients_text)
{
    unsigned short port;
    int idle_timeout_sec;
    int idle_timeout_ms;
    int max_clients = 16;
    int server_fd;
    int one = 1;
    int served = 0;
    bool stop_server = false;
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
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(port);
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Severity remains medium: impact is high (unauthenticated root command channel if left running), but exploitation probability is constrained by preconditions (operator runs this specific script, cleanup must fail, attacker must have local/adjacent network access). This is stronger than a pure reliability bug because it silently widens attack surface, yet weaker than high/critical due limited exposure model and non-internet default topology.
## Likelihood
medium - Trigger condition is plausible in normal operations (physical reconnect script + cleanup failure), but attacker still needs adjacent NCM reachability and the environment is typically lab/internal rather than internet-exposed.
## Impact
high - If exploited after fail-open cleanup, attacker can issue tcpctl run commands as root on device runtime, affecting integrity/confidentiality/availability of the connected device.
## Assumptions
- Repository is used as documented for real device revalidation workflows, not only as dead code.
- USB NCM tcpctl endpoint is reachable at least from the connected host when netservice is enabled.
- No external compensating firewall/auth layer is guaranteed around tcpctl.
- Operator runs scripts/revalidation/physical_usb_reconnect_check.py
- Script starts netservice because it was initially not ready
- stop_netservice() fails during finally cleanup
- An attacker can reach tcpctl on the NCM link
## Path
[n1] -> [n2] -> [n3] -> [n4] -> [n5]
## Path evidence
- `scripts/revalidation/physical_usb_reconnect_check.py:87-110` - run_once returns success then finally swallows stop_netservice errors, causing fail-open cleanup.
- `scripts/revalidation/netservice_reconnect_soak.py:371-389` - stop_netservice intentionally raises if ncm0 is not absent or tcpctl is not stopped, so suppressed errors indicate unsafe residual exposure.
- `stage3/linux_init/a90_tcpctl.c:466-468` - run command is exposed to clients as an executable sink.
- `stage3/linux_init/a90_tcpctl.c:515-518` - listener binds INADDR_ANY, increasing reachability on available interfaces.
- `stage3/linux_init/init_v74.c:55` - netservice tcpctl port is defined as 2325.
- `scripts/revalidation/README.md:79-83` - physical_usb_reconnect_check.py is documented as normal operational workflow and includes netservice/tcpctl validation.
## Narrative
The finding is real and security-relevant: the newly added physical reconnect checker can report PASS and exit 0 even when stopping netservice fails, because cleanup exceptions are caught and only logged. stop_netservice() is designed to raise when tcpctl is still running, so suppression masks an unsafe state. tcpctl listens on INADDR_ANY and supports unauthenticated run of absolute paths, so unintended persistence of tcpctl expands remote command-execution exposure on the USB NCM link.
## Controls
- netservice is opt-in and not always enabled
- serial bridge defaults to localhost (127.0.0.1)
- tcpctl run requires absolute path and has timeout/output caps
- no tcpctl authentication/authorization control
## Blindspots
- Static-only review cannot measure real-world frequency of stop_netservice failures under varied hardware conditions.
- No runtime network topology/firewall data to confirm whether tcpctl becomes reachable beyond intended USB host.
- Could not validate whether downstream wrappers or operator runbooks always perform a post-run netservice status check.
