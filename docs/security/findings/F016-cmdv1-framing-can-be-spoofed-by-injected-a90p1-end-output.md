# F016. cmdv1 framing can be spoofed by injected A90P1 END output

## Metadata

| field | value |
|---|---|
| finding_id | `a3ea350673e08191a08a8b91ced9f864` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/a3ea350673e08191a08a8b91ced9f864 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T04:19:26.064573Z` |
| committed_at | `2026-04-27 02:06:26 +0900` |
| commit_hash | `c52738a672d377b134560e689f0ce661ca54e84a` |
| relevant_paths | `scripts/revalidation/a90ctl.py | stage3/linux_init/init_v73.c` |
| has_patch | `false` |

## CSV Description

This commit introduces a framed shell protocol (`A90P1 BEGIN/END`) and a host parser (`a90ctl.py`). However, the parser stops reading as soon as any `A90P1 END ` substring appears and then parses the first regex match, without validating that BEGIN/END sequence IDs or command names match the issued request. On-device, cmdv1 intentionally preserves normal command stdout/stderr between BEGIN and END, and `run`/`runandroid` directly forward child process output to the same console stream. A command (or data it prints) can therefore emit a forged `A90P1 END ... rc=0 status=ok` line before the real protocol trailer. This can cause host automation to accept false success/error states, skip safety handling, or make unsafe workflow decisions (e.g., flash/verification orchestration based on spoofed status).

## Codex Cloud Detail

cmdv1 framing can be spoofed by injected A90P1 END output
Link: https://chatgpt.com/codex/cloud/security/findings/a3ea350673e08191a08a8b91ced9f864?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: c52738a
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 1:19:26
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Bug introduced: protocol response-spoofing / parser confusion in newly added cmdv1 framing and host wrapper.
This commit introduces a framed shell protocol (`A90P1 BEGIN/END`) and a host parser (`a90ctl.py`). However, the parser stops reading as soon as any `A90P1 END ` substring appears and then parses the first regex match, without validating that BEGIN/END sequence IDs or command names match the issued request. On-device, cmdv1 intentionally preserves normal command stdout/stderr between BEGIN and END, and `run`/`runandroid` directly forward child process output to the same console stream. A command (or data it prints) can therefore emit a forged `A90P1 END ... rc=0 status=ok` line before the real protocol trailer. This can cause host automation to accept false success/error states, skip safety handling, or make unsafe workflow decisions (e.g., flash/verification orchestration based on spoofed status).

# Validation
## Rubric
- [x] Verify host read loop termination condition is marker-substring based and can stop early (`a90ctl.py:55-73`).
- [x] Verify parser consumes first BEGIN/END match and does not enforce seq/cmd binding (`a90ctl.py:88-96`).
- [x] Verify device-side protocol framing permits untrusted command output between BEGIN and END (`init_v73.c:9596-9637`) and `run` forwards child stdout/stderr (`init_v73.c:8279-8283`).
- [x] Reproduce behavior difference with control vs forged stream (control exit 1 vs attack exit 0) using real `a90ctl.py`.
- [x] Attempt crash/valgrind/debugger sequence before final conclusion: crash attempted (no crash), valgrind unavailable, debugger trace captured via non-interactive pdb.
## Report
I validated the finding as a real host-side protocol spoofing/parser-confusion bug.

Code evidence:
- `scripts/revalidation/a90ctl.py:55-73` (`read_until`) stops as soon as any `b"A90P1 END "` substring appears anywhere in accumulated bytes (`if any(marker in data for marker in markers)`), then breaks.
- `scripts/revalidation/a90ctl.py:88-96` (`parse_protocol_output`) uses `BEGIN_RE.search` / `END_RE.search` (first match) and does not verify BEGIN/END `seq` or `cmd` correlation.
- `scripts/revalidation/a90ctl.py:103-110` calls `bridge_exchange(... markers=(b"A90P1 END ",))`, so first END-like text ends collection.
- `stage3/linux_init/init_v73.c:9596-9637` emits BEGIN before command execution and END after execution, leaving command output in-between.
- `stage3/linux_init/init_v73.c:8279-8283` (`run`, same pattern in `runandroid`) forwards child stdout/stderr to console, allowing injected marker lines.

Dynamic reproduction (non-interactive):
1) Control case (no forged END):
- PoC server sends BEGIN + real END with `rc=-5 status=error`.
- Output: `/workspace/validation_artifacts/cmdv1-spoofing/output/client_control.log` shows `exit_code=1`.
- Parsed JSON (`.../client_control.json`) has end `seq=41 cmd=status rc=-5 status=error`.

2) Attack case (forged early END before real END):
- PoC server sends BEGIN + forged `A90P1 END seq=999 cmd=attacker rc=0 ... status=ok`, delays, then tries to send real error END.
- Output: `/workspace/validation_artifacts/cmdv1-spoofing/output/client_attack.log` shows `exit_code=0`.
- Parsed JSON (`.../client_attack.json`) shows accepted forged end fields: `seq=999 cmd=attacker rc=0 status=ok`.
- Server log (`.../server_attack.log`) includes `BrokenPipeError while sending real END (client closed early)`, proving early termination at forged marker.

Debugger trace:
- Used non-interactive `pdb` breakpoint at `a90ctl.py:90`.
- Trace file `/workspace/validation_artifacts/cmdv1-spoofing/pdb_trace2.txt` shows `text` already truncated to forged END and `END_RE.search(text)` matching attacker fields.

Crash/valgrind attempts:
- Crash method attempted with crafted stream; no crash (logic/integrity bug, not memory-corruption).
- Valgrind unavailable in container (`tooling_checks.txt`: `valgrind_check=not-found`).
- gdb unavailable; debugger validation done with pdb.

# Evidence
scripts/revalidation/a90ctl.py (L103 to 110)
  Note: cmdv1 execution relies on marker-based read/parse path vulnerable to injected `A90P1 END` lines.
```
    text = bridge_exchange(
        args.host,
        args.port,
        line,
        args.timeout,
        markers=(b"A90P1 END ",),
    )
    return parse_protocol_output(text)
```

scripts/revalidation/a90ctl.py (L55 to 73)
  Note: Reader stops at first marker substring found anywhere in accumulated output, enabling early termination on forged marker text.
```
def read_until(sock: socket.socket, markers: tuple[bytes, ...], timeout_sec: float) -> bytes:
    deadline = time.monotonic() + timeout_sec
    data = bytearray()
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(8192)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
        if any(marker in data for marker in markers):
            time.sleep(0.15)
            try:
                data.extend(sock.recv(8192))
            except socket.timeout:
                pass
            break
    return bytes(data)
```

scripts/revalidation/a90ctl.py (L88 to 96)
  Note: Parser uses first BEGIN/END regex matches and does not validate seq/cmd correlation, enabling spoofed result acceptance.
```
def parse_protocol_output(text: str) -> ProtocolResult:
    begin_match = BEGIN_RE.search(text)
    end_match = END_RE.search(text)
    if end_match is None:
        raise RuntimeError(f"A90P1 END marker not found\n{text}")
    return ProtocolResult(
        begin=parse_fields(begin_match.group("fields")) if begin_match else {},
        end=parse_fields(end_match.group("fields")),
        text=text,
```

stage3/linux_init/init_v73.c (L8279 to 8283)
  Note: `run` forwards child stdout/stderr directly to console stream, allowing child output to include forged protocol marker lines.
```
        dup2(console_fd, STDIN_FILENO);
        dup2(console_fd, STDOUT_FILENO);
        dup2(console_fd, STDERR_FILENO);
        execve(argv[1], &argv[1], envp);
        cprintf("run: execve(%s): %s\r\n", argv[1], strerror(errno));
```

stage3/linux_init/init_v73.c (L9596 to 9637)
  Note: BEGIN is emitted before command execution and END after execution while preserving intermediate command output, creating an injection window.
```
    if (protocol_v1) {
        protocol_seq = ++shell_protocol_seq;
        shell_protocol_begin(protocol_seq, argv[0], argc, command->flags);
    }

    native_logf("cmd", "start name=%s argc=%d flags=0x%x",
                argv[0], argc, command->flags);

    if ((command->flags & CMD_DISPLAY) != 0) {
        stop_auto_hud(false);
    }

    errno = 0;
    started_ms = monotonic_millis();
    result = command->handler(argv, argc);
    duration_ms = monotonic_millis() - started_ms;
    if (duration_ms < 0) {
        duration_ms = 0;
    }

    if (result < 0) {
        result_errno = -result;
    } else {
        result_errno = 0;
    }
    save_last_result(argv[0], result, result_errno, duration_ms, command->flags);
    native_logf("cmd", "end name=%s rc=%d errno=%d duration=%ldms flags=0x%x",
                argv[0],
                result,
                result_errno,
                duration_ms,
                command->flags);

    print_shell_result(command, argv[0], result, result_errno, duration_ms);
    if (protocol_v1) {
        shell_protocol_end(protocol_seq,
                           argv[0],
                           result,
                           result_errno,
                           duration_ms,
                           command->flags,
                           shell_protocol_status(result, false, false));
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Kept at medium after static and prior validation evidence review. Probability: moderate—requires realistic but non-default preconditions (control of mixed cmd output stream or bridge path), and default bridge binding is localhost. Impact: meaningful integrity compromise of privileged automation decisions, with potential unsafe workflow actions, but no direct standalone remote RCE or confidentiality break demonstrated from this bug alone. This aligns with the repository threat model's own medium classification for parser/protocol ambiguity causing false automation success.
## Likelihood
medium - Exploit mechanics are simple once attacker can influence output stream, but that precondition is typically local/internal (localhost bridge or device-output influence) rather than broadly public by default.
## Impact
medium - Primary impact is integrity of host automation outcomes (false success/error), which can drive unsafe flashing/verification orchestration and safety-handling bypasses in privileged device-management workflows.
## Assumptions
- v73 cmdv1/a90ctl workflow is used for automation as documented
- Attacker can influence bytes emitted between A90P1 BEGIN and real A90P1 END (via crafted command output, malicious bridge endpoint, or compromised device-side helper)
- Default deployment keeps bridge on localhost unless operator changes --host
- Ability to inject/emit a forged line starting with 'A90P1 END ' before the legitimate trailer
- Host automation relies on a90ctl parsed rc/status for decision-making
- Access to cmdv1 output stream via serial bridge/device output path
## Path
[N1 untrusted output] -> [N2 forged A90P1 END] -> [N3 early read stop] -> [N4 first END accepted] -> [N5 bad automation decision]
## Path evidence
- `scripts/revalidation/a90ctl.py:55-73` - read_until stops when any marker substring appears anywhere in accumulated bytes, enabling early termination on forged text.
- `scripts/revalidation/a90ctl.py:88-96` - parse_protocol_output uses first BEGIN/END regex matches and does not validate seq/cmd correlation.
- `scripts/revalidation/a90ctl.py:103-110` - cmdv1 path uses marker-based read with marker 'A90P1 END '.
- `stage3/linux_init/init_v73.c:9598-9637` - BEGIN emitted before handler execution and END emitted afterward, with command output allowed in-between.
- `stage3/linux_init/init_v73.c:8279-8283` - run maps child stdout/stderr to console stream, allowing child-produced forged protocol lines.
- `stage3/linux_init/init_v73.c:8329-8333` - runandroid has same stdout/stderr forwarding behavior.
- `docs/operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md:119-125` - Project guidance says automation should rely on a90ctl parsing A90P1 END rc/status.
- `scripts/revalidation/serial_tcp_bridge.py:17-18` - Bridge default exposure is localhost:54321, constraining default reachability.
## Narrative
The vulnerability is real and reproducible: host parser logic in a90ctl trusts the first observed END marker in mixed output. Device cmdv1 intentionally allows normal command output between BEGIN and END, and run/runandroid forward child stdout/stderr to the same console stream, enabling injection of forged END lines. Validation artifacts report executable PoC behavior (control exits with error, attack exits success with forged fields), confirming integrity impact on automation decisions. Reachability is in-scope but mostly internal/localhost by default; impact is workflow-integrity compromise rather than direct new code execution.
## Controls
- Bridge defaults to 127.0.0.1:54321
- Single-client bridge behavior
- a90ctl rejects whitespace-containing args to avoid split/quoting ambiguity
- Menu busy gating exists on device side for some commands
- No parser binding between BEGIN and END (missing control)
## Blindspots
- Static-only repository review cannot prove real operator deployment choices (e.g., non-local bridge bind, tunnel exposure).
- Could not assess all downstream automation scripts that may consume a90ctl JSON/text and amplify impact.
- PoC execution details came from prior validation artifacts, not rerun in this step.
