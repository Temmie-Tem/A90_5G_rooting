# F040. Validator re-enables unsafe replay of root commands

## Metadata

| field | value |
|---|---|
| finding_id | `2ad2950f54ec8191a433659de7af6d82` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/2ad2950f54ec8191a433659de7af6d82 |
| severity | `medium` |
| status | `mitigated-host-batch-b` |
| detected_at | `2026-05-08T18:19:21.821699Z` |
| committed_at | `2026-05-09 01:48:08 +0900` |
| commit_hash | `7e63134745ecc4f4b50662bba7c5a43650f1e270` |
| relevant_paths | `scripts/revalidation/cpu_mem_thermal_stability.py` <br> `scripts/revalidation/a90ctl.py` |
| source_csv | `docs/security/scans/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

The new script sends several non-observation commands through a90ctl's cmdv1 transport with retry_unsafe=True, and some of those calls also set attempts=2 in the script-level retry wrapper. a90ctl's retry path re-sends the same full command line after socket errors or retryable incomplete responses. If a local/physical attacker, flaky bridge, or malicious bridge endpoint causes a disconnect or missing END marker after the device has already received the command, the validator can enqueue or execute the same privileged root command more than once. In this commit the replayable operations include writing a tmpfs file with dd, removing it, starting longsoak, and repeatedly running /bin/a90_cpustress. The impact is primarily device availability/integrity degradation: stress runs can be extended far beyond the intended bounded test window, and tmpfs writes/cleanup can be repeated unexpectedly. This regresses the safety intent of a90ctl's default allowlist, where retries are limited to known safe observation commands unless explicitly opted in.

## Local Initial Assessment

- Valid class: non-idempotent root commands should not use transport-level replay.
- Related to F043: short-run retry/accounting assumptions are unsafe for long-running validation.
- Treat as a mixed-soak blocker because CPU/memory validators are intended to run unattended.

## Local Remediation

- Implemented in `c214478` (`Avoid unsafe replay in stability observers`).
- Planned Batch B fix.
- Remove `retry_unsafe=True` and script-level `attempts=2` from mutating commands.
- Keep retries only for known read-only observation commands.
- Let ambiguous transport loss fail the validator rather than risk replaying `dd`, `rm`, `longsoak start`, or `/bin/a90_cpustress`.

## Codex Cloud Detail

Validator re-enables unsafe replay of root commands
Link: https://chatgpt.com/codex/cloud/security/findings/2ad2950f54ec8191a433659de7af6d82?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 7e63134
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:19:21
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: the newly added cpu_mem_thermal_stability.py uses retry_unsafe=True and script-level retries for privileged root operations, making those operations susceptible to duplicate execution on reconnect or incomplete-response conditions.
The new script sends several non-observation commands through a90ctl's cmdv1 transport with retry_unsafe=True, and some of those calls also set attempts=2 in the script-level retry wrapper. a90ctl's retry path re-sends the same full command line after socket errors or retryable incomplete responses. If a local/physical attacker, flaky bridge, or malicious bridge endpoint causes a disconnect or missing END marker after the device has already received the command, the validator can enqueue or execute the same privileged root command more than once. In this commit the replayable operations include writing a tmpfs file with dd, removing it, starting longsoak, and repeatedly running /bin/a90_cpustress. The impact is primarily device availability/integrity degradation: stress runs can be extended far beyond the intended bounded test window, and tmpfs writes/cleanup can be repeated unexpectedly. This regresses the safety intent of a90ctl's default allowlist, where retries are limited to known safe observation commands unless explicitly opted in.

# Validation
## Rubric
- [x] Confirm `a90ctl` only retries unsafe/non-observation commands when `retry_unsafe=True`, and that retrying reuses the same encoded cmdv1 line.
- [x] Confirm the new `cpu_mem_thermal_stability.py` applies `retry_unsafe=True` to privileged/non-observation operations such as tmpfs writes/removal, longsoak start, and cpustress.
- [x] Confirm some new script calls also use `attempts=2`, creating a second script-level replay mechanism after `run_cmdv1_command` raises.
- [x] Reproduce duplicate receipt of an unsafe command under a missing-END/incomplete-response bridge condition.
- [x] Include a negative control showing `retry_unsafe=False` does not replay the same unsafe command.
## Report
Validated the finding. This is a Python logic/replay issue, not a memory-corruption crash; a direct PoC run produced duplicate command execution rather than a crash, and `valgrind --version` showed valgrind is unavailable in the container. I then used a non-interactive Python bdb debugger trace and targeted fake-bridge PoCs.

Code evidence: `scripts/revalidation/a90ctl.py:225` sets `allow_retry = retry_unsafe or command_allows_retry(command)`, so `retry_unsafe=True` bypasses the safe retry allowlist. `a90ctl.py:227` encodes the command once, and `a90ctl.py:233-241` calls `bridge_exchange` inside the retry loop. `a90ctl.py:155-157` opens a new socket and sends `("\n" + line + "\n")`, so each retry transmits the same full cmdv1 command line again. `a90ctl.py:249-257` retries incomplete/no-END responses when retry is allowed.

New script evidence: `scripts/revalidation/cpu_mem_thermal_stability.py:181-199` has a script-level attempts loop around `run_cmdv1_command`. `cpu_mem_thermal_stability.py:288-318` sends tmpfs `dd`, `sha256sum`, and `rm -f` with `retry_unsafe=True`; `dd`, `sha256sum`, and cleanup use `attempts=2` in the shown code. `cpu_mem_thermal_stability.py:409-435` sends `longsoak start 15` and `/bin/a90_cpustress` with `retry_unsafe=True`, and cpustress uses `attempts=2`.

Dynamic evidence: I wrote `/workspace/poc_retry/retry_replay_poc.py`, a fake bridge that records received cmdv1 lines, intentionally closes the first connection after receiving a target command without sending an `A90P1 END`, then replies successfully on the next identical command. Control run `lowlevel-safe` with `retry_unsafe=False` logged one `cmdv1 run /bin/echo SIDE_EFFECT` and failed with missing END. Vulnerable run `lowlevel-unsafe` logged the exact same line twice and returned ok: counts `{"lowlevel-echo": 2}`.

Full integration evidence: running the actual validator via `python3 /workspace/poc_retry/retry_replay_poc.py full` returned PASS, but the fake bridge recorded duplicated privileged operations: `{"cpustress": 2, "longsoak-start": 2, "mem-cleanup": 2, "mem-dd": 2, "mem-sha256": 2, "other": 7}`. The logged duplicate lines include two each of `cmdv1 longsoak start 15`, `cmdv1 run /cache/bin/toybox dd if=/dev/zero ...`, `cmdv1 run /cache/bin/toybox sha256sum ...`, `cmdv1 run /cache/bin/toybox rm -f ...`, and `cmdv1 run /bin/a90_cpustress 1 1`.

Script-level retry evidence: `/workspace/poc_retry/script_attempt_poc.py` calls `cpu_mem_thermal_stability.run_cmd(... retry_unsafe=True, attempts=2 ...)` with a short first timeout; the fake bridge recorded two identical `cmdv1 run /bin/a90_cpustress 1 1` lines and the wrapper returned ok.

Debugger evidence: `/workspace/poc_retry/debugger_trace.py` breaks at `a90ctl.py:233` and records local variables. Output shows two debugger hits with `allow_retry: true` and identical `encoded_line: "cmdv1 run /bin/echo SIDE_EFFECT"`; the fake bridge simultaneously recorded the same command twice and the client returned ok. This confirms the retry path re-enters `bridge_exchange` with the identical unsafe command line after an incomplete response.

# Evidence
scripts/revalidation/a90ctl.py (L147 to 158)
  Note: Each retry sends the full cmdv1 line again to the bridge, so retries can duplicate root command execution if the previous send reached the device.
```
def bridge_exchange(host: str,
                    port: int,
                    line: str,
                    timeout_sec: float,
                    markers: tuple[bytes, ...],
                    *,
                    require_prompt_after_end: bool = False) -> str:
    connect_timeout = min(3.0, max(0.1, timeout_sec))
    with socket.create_connection((host, port), timeout=connect_timeout) as sock:
        sock.settimeout(0.25)
        sock.sendall(("\n" + line + "\n").encode("utf-8"))
        data = read_until(
```

scripts/revalidation/a90ctl.py (L225 to 257)
  Note: a90ctl's retry_unsafe path permits retries for commands outside the safe observation allowlist and re-enters bridge_exchange with the same encoded command line.
```
    allow_retry = retry_unsafe or command_allows_retry(command)

    line = encode_cmdv1_line(command)
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        try:
            text = bridge_exchange(
                host,
                port,
                line,
                remaining,
                markers=(b"A90P1 END ",),
                require_prompt_after_end=True,
            )
        except OSError as exc:
            last_error = exc
            if not allow_retry:
                raise
            sleep_before_retry(deadline)
            continue

        if END_RE.search(text) is not None:
            return parse_protocol_output(text)
        if not allow_retry:
            return parse_protocol_output(text)
        if not should_retry_cmdv1_exchange(text):
            return parse_protocol_output(text)

        last_text = text
        sleep_before_retry(deadline)
```

scripts/revalidation/cpu_mem_thermal_stability.py (L181 to 200)
  Note: The new wrapper retries a failed command attempt without checking whether the command may already have reached the device, enabling script-level replay when attempts > 1.
```
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            result = run_cmdv1_command(
                args.bridge_host,
                args.bridge_port,
                args.bridge_timeout if timeout is None else timeout,
                command,
                retry_unsafe=retry_unsafe,
            )
            duration = time.monotonic() - started
            write_private_text(output_file, result.text)
            ok = result.rc == 0 and result.status == "ok"
            if not ok and not allow_error:
                add_check(checks, label, False, f"rc={result.rc} status={result.status}")
            return CommandRecord(label, command, result.rc, result.status, duration, ok, str(output_file))
        except Exception as exc:  # noqa: BLE001 - validator keeps failure evidence
            last_exc = exc
            if attempt < attempts:
                time.sleep(0.5)
```

scripts/revalidation/cpu_mem_thermal_stability.py (L288 to 318)
  Note: The tmpfs dd, sha256sum, and rm operations are sent via root 'run' commands with retry_unsafe=True; dd and rm also use attempts=2.
```
    write = run_cmd(
        args,
        "mem-dd",
        ["run", args.toybox, "dd", "if=/dev/zero", f"of={path}", f"bs={block_size}", f"count={count}"],
        out_dir,
        checks,
        retry_unsafe=True,
        timeout=max(args.bridge_timeout, 30.0),
        attempts=2,
    )
    sha = run_cmd(
        args,
        "mem-sha256",
        ["run", args.toybox, "sha256sum", path],
        out_dir,
        checks,
        retry_unsafe=True,
        attempts=2,
    )
    device_sha = None
    if sha.output_file:
        device_sha = parse_sha256(Path(sha.output_file).read_text(encoding="utf-8", errors="replace"))
    cleanup = run_cmd(
        args,
        "mem-cleanup",
        ["run", args.toybox, "rm", "-f", path],
        out_dir,
        checks,
        allow_error=True,
        retry_unsafe=True,
        attempts=2,
```

scripts/revalidation/cpu_mem_thermal_stability.py (L409 to 435)
  Note: The validator enables unsafe retry for longsoak start and for each /bin/a90_cpustress invocation, making bounded stress operations replayable under bridge disruption.
```
    command_records.append(
        run_cmd(
            args,
            "longsoak-start",
            ["longsoak", "start", "15"],
            out_dir,
            checks,
            allow_error=True,
            retry_unsafe=True,
        )
    )
    memory = run_memory_verify(args, out_dir, checks)
    sample, record = read_status_sample(args, "baseline", out_dir)
    samples.append(sample)
    command_records.append(record)
    pings.append(maybe_host_ping(args, "baseline", out_dir))

    for index in range(1, args.cycles + 1):
        stress = run_cmd(
            args,
            f"cpustress-{index:02d}",
            ["run", "/bin/a90_cpustress", str(args.stress_sec), str(args.stress_workers)],
            out_dir,
            checks,
            retry_unsafe=True,
            timeout=max(args.bridge_timeout, args.stress_sec + 20.0),
            attempts=2,
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Kept at medium. The code evidence confirms the bug: retry_unsafe=True bypasses a90ctl's safe retry allowlist and resends the same cmdv1 line, while the new validator uses retry_unsafe and attempts=2 for non-idempotent root operations. The path is in scope because the threat model covers revalidation tooling, localhost bridge control, and device availability/integrity. However, exposure is localhost/lab-local, exploitation needs operator action plus transport manipulation, and the attacker replays fixed validator commands rather than gaining arbitrary command execution through this bug. That supports medium availability/integrity risk, not high or critical.
## Likelihood
medium - Exploitation requires operator interaction and local/physical/bridge-path influence, but the retry behavior is deterministic once the bridge endpoint or transport can omit END/close after receipt. The executable validation PoC demonstrated this against the normal validator path.
## Impact
medium - The attacker can force replay of predetermined privileged commands, causing duplicate tmpfs writes/cleanup and longer or repeated CPU/thermal stress on a single connected rooted device. This can affect device availability and test integrity, but it is not arbitrary command selection, host compromise, broad fleet compromise, or sensitive data exfiltration by itself.
## Assumptions
- Analysis is limited to repository artifacts in /workspace/A90_5G_rooting; no cloud APIs or live device APIs were called.
- Normal use for this component is a trusted operator running host-side revalidation scripts against a rooted A90 device through the localhost serial TCP bridge.
- The attacker in this path can influence the bridge/transport timing or endpoint behavior, but does not necessarily choose arbitrary validator commands.
- The impact is bounded to the connected rooted device and the operator workflow unless the local bridge is additionally exposed beyond localhost.
- Operator runs scripts/revalidation/cpu_mem_thermal_stability.py against a native-init/rooted A90 device
- cmdv1 traffic is routed through a bridge endpoint, normally 127.0.0.1:54321
- Attacker, malicious bridge, or physical/local fault can cause a socket close, missing END marker, or retryable incomplete response after the device has already received a non-idempotent command
## Path
operator validator -> a90ctl retry_unsafe -> localhost:54321 bridge -> device root cmdv1
                                      ^                                  |
                                      |-- missing END / socket close ----|
                                      `-- resend identical command ------> duplicate root execution
## Path evidence
- `scripts/revalidation/a90ctl.py:13-14` - Default cmdv1 client target is localhost TCP port 54321, matching the normal serial bridge exposure.
- `scripts/revalidation/a90ctl.py:147-158` - Each bridge_exchange opens a connection and sends the full encoded command line with sock.sendall, so each retry retransmits the same command.
- `scripts/revalidation/a90ctl.py:220-257` - retry_unsafe sets allow_retry outside the safe retry allowlist and retries after socket errors or retryable incomplete/no-END responses.
- `scripts/revalidation/a90ctl.py:306-309` - CLI help documents the intended safety boundary: retrying non-observation commands is unsafe and normally disabled.
- `scripts/revalidation/cpu_mem_thermal_stability.py:169-201` - The validator adds a script-level attempts loop around run_cmdv1_command without determining whether the previous attempt already reached the device.
- `scripts/revalidation/cpu_mem_thermal_stability.py:288-318` - tmpfs dd, sha256sum, and rm commands are sent as root run commands with retry_unsafe=True and attempts=2.
- `scripts/revalidation/cpu_mem_thermal_stability.py:409-435` - longsoak start and /bin/a90_cpustress are run with retry_unsafe=True; cpustress also uses attempts=2.
- `scripts/revalidation/serial_tcp_bridge.py:16-18` - The bridge is localhost-only by default, limiting exposure but still providing the normal local attack path.
- `scripts/revalidation/serial_tcp_bridge.py:413-418` - The bridge listen host and port are operator-configurable; default port is 54321.
## Narrative
The finding is real and reachable in the repository's stated workflow. cpu_mem_thermal_stability.py wraps cmdv1 calls in an attempts loop and passes retry_unsafe=True for privileged root operations. a90ctl.py uses retry_unsafe to bypass the safe observation-command allowlist and re-enters bridge_exchange with the same encoded line after OSError or retryable incomplete output. bridge_exchange sends the full line on each connection, so a response disruption after the device has already received the line can cause duplicate execution. The validated PoC used a fake bridge to close or omit END after receiving commands and observed duplicated longsoak, tmpfs dd/sha/rm, and cpustress invocations. Severity remains medium: the issue is not remote internet RCE and does not let the attacker choose arbitrary commands by itself, but it can materially degrade availability/integrity of the connected rooted device through realistic local/physical or bridge-path manipulation.
## Controls
- serial_tcp_bridge defaults to 127.0.0.1 rather than a public bind
- a90ctl has SAFE_RETRY_COMMANDS for observation commands
- retry_unsafe flag explicitly bypasses the retry allowlist
- cmdv1 requires A90P1 END marker parsing for successful completion
- serial_tcp_bridge uses a single-client model and rejects clients while serial is absent unless configured otherwise
- No authentication is present on the local bridge/native-init command channel in this lab model
## Blindspots
- No live A90 device was inspected in this attack-path stage; reachability is inferred from repository code and prior validation artifacts.
- Actual deployment exposure of serial_tcp_bridge depends on operator bind address, tunnels, and host firewall, which are not represented by IaC/manifests in this repository.
- The exact physical reliability of inducing a disconnect after device-side receipt but before END response cannot be measured from static artifacts.
- No cloud, Kubernetes, or service-account manifests were present for this path.
