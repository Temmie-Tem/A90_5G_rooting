# F051. Default lifecycle run can fail to stop tcpctl listener

## Metadata

| field | value |
|---|---|
| finding_id | `9fe8c4632a00819188c50981a9fff7f1` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/9fe8c4632a00819188c50981a9fff7f1 |
| severity | `medium` |
| status | `mitigated-host-batch-h2` |
| detected_at | `2026-05-11T19:25:59.928477Z` |
| committed_at | `2026-05-11 22:02:35 +0900` |
| commit_hash | `33f94392fbce0ca194fa4456ffb15f000752ea2e` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker_ncm_lifecycle_check.py` <br> `scripts/revalidation/tcpctl_host.py` <br> `scripts/revalidation/a90_broker.py` <br> `scripts/revalidation/serial_tcp_bridge.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The new a90_broker_ncm_lifecycle_check.py wrapper launches tcpctl_host.py start as a long-running subprocess and only forwards --token to child commands when the operator explicitly supplied one. tcpctl_host.py start does fetch the token before launching the listener, but that token is cached only inside the start subprocess. The wrapper then runs the broker smoke and finally tcpctl_host.py stop while the start subprocess is still connected to the serial bridge. Both the broker NCM backend and tcpctl_host.py stop need to call back over ACM/serial to obtain the token when --token was not supplied. The serial_tcp_bridge enforces a single-client policy and rejects additional clients while the start subprocess is still attached. Because the wrapper attempts stop before killing/releasing the start subprocess, the default live path can fail to authenticate shutdown. It then kills only the host-side start subprocess, not necessarily the device-side a90_tcpctl listener, leaving the root-capable TCP listener exposed until idle timeout. This is especially relevant because the wrapper deliberately uses max_clients=0, so client count will not terminate the service.

## Local Initial Assessment

- Confirmed against current code: lifecycle wrapper starts long-running `tcpctl_host.py start`, but stop/smoke only receive `--token` if the operator supplied one. Default path can need ACM token retrieval while the start process occupies the single-client bridge.

## Local Remediation

- Implemented in Batch H2; see `docs/security/SECURITY_FINDINGS_F047_F053_H2_REPORT_2026-05-12.md`. The NCM lifecycle wrapper now captures one tcpctl token before starting the listener and passes the redacted token consistently to start, smoke, and stop commands.

## Codex Cloud Detail

Default lifecycle run can fail to stop tcpctl listener
Link: https://chatgpt.com/codex/cloud/security/findings/9fe8c4632a00819188c50981a9fff7f1?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 33f9439
Author: shs02140@gmail.com
Created: 2026. 5. 12. 오전 4:25:59
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: the new lifecycle wrapper composes existing tools in a way that loses the tcpctl token across subprocess boundaries and attempts authenticated smoke/stop while the token retrieval path is blocked by the long-running start process occupying the single-client serial bridge.
The new a90_broker_ncm_lifecycle_check.py wrapper launches tcpctl_host.py start as a long-running subprocess and only forwards --token to child commands when the operator explicitly supplied one. tcpctl_host.py start does fetch the token before launching the listener, but that token is cached only inside the start subprocess. The wrapper then runs the broker smoke and finally tcpctl_host.py stop while the start subprocess is still connected to the serial bridge. Both the broker NCM backend and tcpctl_host.py stop need to call back over ACM/serial to obtain the token when --token was not supplied. The serial_tcp_bridge enforces a single-client policy and rejects additional clients while the start subprocess is still attached. Because the wrapper attempts stop before killing/releasing the start subprocess, the default live path can fail to authenticate shutdown. It then kills only the host-side start subprocess, not necessarily the device-side a90_tcpctl listener, leaving the root-capable TCP listener exposed until idle timeout. This is especially relevant because the wrapper deliberately uses max_clients=0, so client count will not terminate the service.

# Validation
## Rubric
- [x] Command construction loses the token by default: start/stop/smoke omit --token when the wrapper was not explicitly given one.
- [x] The start subprocess obtains the token only in its own process and then keeps the serial bridge occupied for the long-running listener.
- [x] Broker smoke and tcpctl_host stop independently need token retrieval for authenticated run/shutdown commands when no token is supplied.
- [x] The bridge has a single-client policy that rejects additional clients while the start subprocess is attached.
- [x] Cleanup attempts authenticated stop before releasing/killing start, and the reproduced failure leaves the TCP listener reachable afterward.
## Report
Validated the finding with a targeted Python PoC that runs the real lifecycle wrapper against a fake single-client serial bridge and fake tcpctl listener. Code review showed the vulnerable chain: a90_broker_ncm_lifecycle_check.py builds start/stop commands and only appends --token when args.token is set at lines 108-129; smoke_command likewise omits --token by default at lines 141-169. The wrapper starts tcpctl_host.py start as a long-running subprocess, waits for readiness, then runs smoke while start remains connected at lines 214-241. In cleanup it runs stop before stop_process(start_proc) at lines 252-264. tcpctl_host.py caches tokens only in-process at lines 214-224; command_start fetches the token then holds the bridge via BridgeRunThread at lines 342-364; command_stop calls tcpctl_request('shutdown') at lines 403-405, which triggers token retrieval again if no --token was supplied. a90_broker.py NcmTcpctlBackend also fetches a token via the ACM backend for run/shutdown at lines 308-354. serial_tcp_bridge.py enforces one active client and closes extra clients at lines 270-272.

Dynamic evidence: /workspace/validation_poc/poc_lifecycle_token_loss.py gave the start subprocess one token, held the bridge connection for the fake listener, and rejected extra bridge clients close-only. Running `python3 /workspace/validation_poc/poc_lifecycle_token_loss.py` produced WRAPPER_RC=1 after 36.5s. The real lifecycle wrapper crashed with `subprocess.TimeoutExpired` while executing `tcpctl_host.py ... stop` because stop tried to retrieve a token over the occupied bridge. The generated planned-commands.json confirms start/smoke/stop had no --token. tcpctl-start-output.txt shows `tcpctl: listening ... auth=required`. broker concurrent smoke failed with `transport-error` and `A90P1 END marker not found before timeout (20.0s) ... Connection reset by peer`, matching bridge rejection. The fake bridge log repeatedly shows `rejecting extra client` during smoke/stop token retrieval. After the wrapper crash, a TCP status probe still succeeded with `status: fake tcpctl alive\nOK`, while unauthenticated run returned `ERR auth-required`, demonstrating the listener remained exposed until explicit cleanup.

Valgrind/ASan: not applicable to this Python stack; `valgrind --version` was unavailable in the container and logged. Debugger attempt: a small bdb/Python debugger probe in pdb_command_builder_probe.py broke at command-builder lines and printed `has_token_flag=False` for both start and smoke when token=None, confirming token loss across subprocess boundaries.

# Evidence
scripts/revalidation/a90_broker_ncm_lifecycle_check.py (L120 to 129)
  Note: The start/stop command builder only passes --token when the wrapper itself was given one; otherwise later child processes must independently retrieve the token.
```
        args.toybox,
        "--idle-timeout",
        str(args.idle_timeout),
        "--max-clients",
        str(args.max_clients),
        "--tcp-timeout",
        str(args.tcp_timeout),
    ]
    if args.token:
        command.extend(["--token", args.token])
```

scripts/revalidation/a90_broker_ncm_lifecycle_check.py (L141 to 169)
  Note: The broker smoke command is also invoked without a token by default, forcing the NCM broker backend to retrieve the token over the ACM bridge while tcpctl_host.py start is still running.
```
def smoke_command(args: argparse.Namespace, smoke_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(smoke_script()),
        "--backend",
        "ncm-tcpctl",
        "--run-dir",
        str(smoke_dir),
        "--device-ip",
        args.device_ip,
        "--tcp-port",
        str(args.tcp_port),
        "--tcp-timeout",
        str(args.tcp_timeout),
        "--bridge-host",
        args.bridge_host,
        "--bridge-port",
        str(args.bridge_port),
        "--clients",
        str(args.clients),
        "--rounds",
        str(args.rounds),
        "--command",
        f"run {args.toybox} uptime",
        "--command",
        f"run {args.toybox} uname -a",
    ]
    if args.token:
        command.extend(["--token", args.token])
```

scripts/revalidation/a90_broker_ncm_lifecycle_check.py (L214 to 236)
  Note: The wrapper starts tcpctl_host.py start as a long-running subprocess and proceeds to smoke testing after the readiness marker while that subprocess remains active.
```
        start_proc = subprocess.Popen(
            start_command(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert start_proc.stdout is not None
        reader = LineReader(start_proc.stdout)
        reader.start()
        if not reader.ready.wait(args.ready_timeout):
            text = reader.text()
            store.write_text("tcpctl-start-output.txt", redact_text(text))
            results.append(LifecycleResult("tcpctl listener ready", False, "ready marker timeout", ["tcpctl-start-output.txt"]))
            return results
        start_text = reader.text()
        store.write_text("tcpctl-start-output.txt", redact_text(start_text))
        auth_required = "auth=required" in start_text and "auth=none" not in start_text
        results.append(LifecycleResult("tcpctl listener ready", True, READY_MARKER, ["tcpctl-start-output.txt"]))
        results.append(LifecycleResult("tcpctl auth required", auth_required, "auth=required marker", ["tcpctl-start-output.txt"]))

        smoke = subprocess.run(
            smoke_command(args, smoke_dir),
```

scripts/revalidation/a90_broker_ncm_lifecycle_check.py (L252 to 264)
  Note: Cleanup attempts tcpctl_host.py stop before releasing/killing the start subprocess; if stop cannot retrieve the token, only the host-side process is killed afterward, potentially leaving the device listener running.
```
    finally:
        if not args.leave_running:
            stop = subprocess.run(
                stop_command(args),
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15.0,
            )
            store.write_text("tcpctl-stop-output.txt", redact_text(stop.stdout))
            results.append(LifecycleResult("tcpctl stop", stop.returncode == 0, f"rc={stop.returncode}", ["tcpctl-stop-output.txt"]))
        stdout, stderr = stop_process(start_proc)
```

scripts/revalidation/a90_broker.py (L308 to 354)
  Note: The NCM broker backend also retrieves the token over the ACM backend when no token was supplied, which conflicts with the active start subprocess occupying the serial bridge.
```
    def tcpctl_request(self, command: str, timeout_sec: float) -> str:
        payload = command.rstrip("\n") + "\n"
        if not self.no_auth and self.command_requires_auth(command):
            payload = f"auth {self.get_token(timeout_sec)}\n{payload}"
        with socket.create_connection((self.device_ip, self.tcp_port), timeout=min(timeout_sec, self.tcp_timeout)) as sock:
            sock.settimeout(0.5)
            sock.sendall(payload.encode())
            data = bytearray()
            deadline = time.monotonic() + min(timeout_sec, self.tcp_timeout)
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(8192)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                data.extend(chunk)
        return data.decode("utf-8", errors="replace")

    @staticmethod
    def command_requires_auth(command: str) -> bool:
        word = command.lstrip().split(maxsplit=1)[0] if command.strip() else ""
        return word in {"run", "shutdown"}

    def get_token(self, timeout_sec: float) -> str:
        with self.token_lock:
            if self.token:
                return self.token
            token_request = BrokerRequest(
                request_id="ncm-token",
                client_id="broker",
                op="cmd",
                argv=list(DEFAULT_TOKEN_COMMAND),
                timeout_ms=int(timeout_sec * 1000),
                command_class="observe",
            )
            result = self.acm.execute(token_request)
            if result.rc != 0 or result.status != "ok":
                raise RuntimeError(
                    "token command failed "
                    f"rc={result.rc} status={result.status}\n{redact_text(result.text)}"
                )
            match = re.search(r"tcpctl_token=([0-9A-Fa-f]{32})", result.text)
            if not match:
                raise RuntimeError(f"tcpctl token was not found in output:\n{redact_text(result.text)}")
            self.token = self.validate_token(match.group(1))
            return self.token
```

scripts/revalidation/serial_tcp_bridge.py (L257 to 273)
  Note: The serial bridge accepts only one active client and rejects extra clients, so token retrieval by smoke/stop can fail while tcpctl_host.py start remains connected.
```
    def accept_client(self) -> None:
        conn, addr = self.server.accept()
        conn.setblocking(False)

        if self.serial_fd is None and not self.args.allow_client_without_serial:
            self.log(f"rejecting client from {addr[0]}:{addr[1]}: serial not connected")
            try:
                conn.sendall(b"[bridge] serial device is not connected; retry later\r\n")
            except OSError:
                pass
            conn.close()
            return

        if self.client is not None:
            self.log(f"rejecting extra client from {addr[0]}:{addr[1]}")
            conn.close()
            return
```

scripts/revalidation/tcpctl_host.py (L214 to 224)
  Note: tcpctl_host.py caches a token only in the current process; without --token it retrieves the token by issuing a device command over the serial bridge.
```
def get_tcpctl_token(args: argparse.Namespace) -> str:
    cached = getattr(args, "_tcpctl_token", None)
    if cached:
        return cached
    if args.token:
        args._tcpctl_token = args.token
        return args.token
    output = device_command(args, args.token_command, timeout=args.bridge_timeout)
    token = parse_tcpctl_token(output)
    args._tcpctl_token = token
    return token
```

scripts/revalidation/tcpctl_host.py (L342 to 364)
  Note: The start subcommand fetches the token in its own process, starts the listener through BridgeRunThread, and waits until the device-side run completes, keeping the bridge client occupied.
```
def command_start(args: argparse.Namespace) -> int:
    best_effort_hide_menu(args)
    if not args.no_auth:
        get_tcpctl_token(args)
    command = tcpctl_listen_command(args)
    log(f"starting via bridge: {command}")
    runner = BridgeRunThread(args, command, echo=True)
    runner.start()
    try:
        while not runner.done.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        log("interrupt: requesting tcpctl shutdown")
        try:
            print(tcpctl_request(args, "shutdown"), end="")
        except Exception as exc:
            log(f"shutdown request failed: {exc}")
        runner.join(args.bridge_timeout)
        return 130

    if runner.error is not None:
        raise RuntimeError(f"bridge run failed: {runner.error}")
    return 0
```

scripts/revalidation/tcpctl_host.py (L403 to 405)
  Note: The stop subcommand sends authenticated shutdown through tcpctl_request; without a supplied token this triggers another token retrieval attempt.
```
def command_stop(args: argparse.Namespace) -> int:
    print(tcpctl_request(args, "shutdown"), end="")
    return 0
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Medium is retained. Repository evidence supports the bug chain: token is not propagated by default, the start subprocess holds the single-client bridge, smoke/stop need that same bridge to obtain a token, and cleanup attempts stop before releasing start. The affected tcpctl listener is a sensitive root command surface, so an unintended listener lifetime is security-relevant and in scope. It should not be raised to high or critical because the workflow is operator-initiated, lab/USB-NCM scoped, not public by default, and dangerous run/shutdown operations remain protected by token authentication. It should not be ignored because the wrapper is documented operational tooling and the failure mode leaves a privileged network service exposed beyond the intended lifecycle.
## Likelihood
low - Triggering the flaw is plausible in normal documented live use, but exploitation requires a prepared attached device, an operator running the lifecycle wrapper without --token, and an attacker positioned on the lab host or USB/NCM network during the limited exposure window. This is not Internet-facing by default.
## Impact
medium - The affected service is root-capable on the device, and the bug can leave it unintentionally reachable on the USB NCM TCP port with unlimited max_clients until idle timeout. However, direct root command execution still requires the 32-hex tcpctl token, and unauthenticated impact is mainly service/status probing, exposure-window extension, and availability/workflow failure.
## Assumptions
- The operator runs the documented live lifecycle wrapper without providing --token, using the default bridge and tcpctl options.
- The USB NCM device address 192.168.7.2:2325 is reachable to an attacker on the lab host, USB/NCM link, or an adjacent network path exposed by the host.
- Killing the host-side tcpctl_host.py start subprocess does not reliably send an authenticated shutdown to the device-side a90_tcpctl listener.
- The tcpctl token itself is not leaked by this bug; unauthorized attackers can probe unauthenticated commands and can execute root commands only if they also obtain the token through another path.
- attached A90 native-init device with serial bridge and USB NCM prepared
- operator runs scripts/revalidation/a90_broker_ncm_lifecycle_check.py live, not --dry-run
- operator does not pass --token, so child processes independently fetch the token
- attacker can reach the device tcpctl TCP port during the unintended listener lifetime
## Path
operator live wrapper
  -> start(no --token) fetches token in-process
  -> start holds single-client serial bridge
  -> smoke/stop(no --token) try token fetch
  -> bridge rejects extra clients
  -> authenticated shutdown fails
  -> host start process killed after stop attempt
  -> device tcpctl remains on 192.168.7.2:2325
  -> adjacent attacker can probe/keep alive; token holder can run root commands
## Path evidence
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py:46-58` - Wrapper defaults include device/tcp port, 120 second idle timeout, max_clients=0, and optional --token.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py:105-129` - Base start/stop command only forwards --token when args.token is set by the operator.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py:141-169` - Broker smoke command also omits --token by default while issuing authenticated run commands.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py:214-241` - Wrapper launches tcpctl_host.py start and proceeds to smoke testing after the readiness marker while start remains active.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py:252-264` - Cleanup runs stop before stop_process(start_proc), so the bridge-holding start process is still present during stop.
- `scripts/revalidation/tcpctl_host.py:214-224` - Token cache is process-local; without --token, each process retrieves the token over the bridge.
- `scripts/revalidation/tcpctl_host.py:334-364` - start constructs the device listen command, fetches the token, and waits for the bridge-run thread until the device-side command completes.
- `scripts/revalidation/tcpctl_host.py:403-405` - stop sends shutdown through tcpctl_request, which triggers token retrieval when --token is absent.
- `scripts/revalidation/a90_broker.py:308-354` - NCM broker backend prepends auth for run/shutdown and fetches a missing token through the ACM backend.
- `scripts/revalidation/serial_tcp_bridge.py:257-273` - Serial bridge rejects extra clients when one client is already connected.
- `stage3/linux_init/a90_tcpctl.c:560-596` - tcpctl allows unauthenticated ping/version/status but requires authorization for shutdown; run dispatch is handled separately with auth checks.
- `stage3/linux_init/a90_tcpctl.c:642-650` - Device listener reports auth status and, with max_clients=0, continues serving until stop or idle timeout.
- `scripts/revalidation/README.md:67-72` - README describes this lifecycle wrapper as the v194 NCM/tcpctl broker lifecycle validator.
- `scripts/revalidation/README.md:252-254` - README documents running the wrapper live without --dry-run once NCM host IP and bridge are ready.
## Narrative
The finding is real and in scope. The lifecycle wrapper defaults to no --token and max_clients=0, only appends --token if the operator supplied it, starts tcpctl_host.py start as a long-running subprocess, runs smoke while that process remains active, and only then attempts stop. tcpctl_host.py caches an auto-fetched token only in its current process, and both tcpctl_host.py stop and the NCM broker backend independently fetch a token over the ACM/serial bridge when no token is supplied. The serial bridge explicitly permits only one active client and rejects extras, so stop can fail to authenticate while start occupies the bridge. The resulting exposure is constrained to the lab/USB NCM network and dangerous tcpctl run/shutdown commands are token-protected, so medium severity is appropriate rather than high or critical.
## Controls
- tcpctl token authentication is required for run and shutdown commands
- serial TCP bridge defaults to 127.0.0.1:54321
- USB NCM/tcpctl workflow is lab-local and operator-initiated
- wrapper default idle timeout is 120 seconds
- a90_tcpctl run requires an absolute executable path
- evidence output uses redaction/private helpers
## Blindspots
- Static review cannot prove exact native-init child lifetime on all real device disconnect and signal paths after the host start subprocess is killed.
- Actual attacker reachability of 192.168.7.2:2325 depends on host routing, firewall, USB/NCM setup, and whether the lab host is shared or compromised.
- Token secrecy, entropy source, and operational handling were not fully reassessed beyond confirming that this bug does not itself print the token.
- No cloud, Kubernetes, or external deployment manifests exist in scope for broader exposure validation.
