# F015. Cmdv1 retry can replay privileged commands on reconnect

## Metadata

| field | value |
|---|---|
| finding_id | `2534172617e481919b3be2d7835c68f1` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/2534172617e481919b3be2d7835c68f1 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T17:43:56.783462Z` |
| committed_at | `2026-04-27 02:31:18 +0900` |
| commit_hash | `225089c3bb912c89a195f9da39808407ca748f39` |
| relevant_paths | `scripts/revalidation/a90ctl.py | scripts/revalidation/serial_tcp_bridge.py | stage3/linux_init/init_v73.c` |
| has_patch | `false` |

## CSV Description

Before this commit, `run_cmdv1_command()` sent one command and returned/failed once. After this commit, it retries when socket errors occur or when bridge output is empty / contains the serial-missing text. Because each retry re-sends the full `cmdv1 ...` line, transient disconnects can cause at-least-once execution semantics for non-idempotent root commands. In this project, cmdv1 can invoke destructive operations (`writefile`, `run`, `netservice`, `usbacmreset`, `reboot`, `recovery`, `poweroff`). An attacker who can influence bridge connectivity (or a flaky reconnect event) can trigger unintended repeated execution, causing integrity/availability impact (e.g., repeated reboot/reset or repeated state mutation).

## Codex Cloud Detail

Cmdv1 retry can replay privileged commands on reconnect
Link: https://chatgpt.com/codex/cloud/security/findings/2534172617e481919b3be2d7835c68f1
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 225089c
Author: shs02140@gmail.com
Created: 2026. 4. 29. 오전 2:43:56
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: command replay risk due automatic cmdv1 retries without deduplication/sequence acknowledgement.
Before this commit, `run_cmdv1_command()` sent one command and returned/failed once. After this commit, it retries when socket errors occur or when bridge output is empty / contains the serial-missing text. Because each retry re-sends the full `cmdv1 ...` line, transient disconnects can cause at-least-once execution semantics for non-idempotent root commands. In this project, cmdv1 can invoke destructive operations (`writefile`, `run`, `netservice`, `usbacmreset`, `reboot`, `recovery`, `poweroff`). An attacker who can influence bridge connectivity (or a flaky reconnect event) can trigger unintended repeated execution, causing integrity/availability impact (e.g., repeated reboot/reset or repeated state mutation).

# Validation
## Rubric
- [x] Confirm commit introduced retry loop for `run_cmdv1_command()` and that each retry re-sends full command (`a90ctl.py:83-87`, `117-151`).
- [x] Confirm retry conditions include empty output and bridge serial-missing text (`a90ctl.py:91-92`).
- [x] Confirm bridge emits the same serial-missing text (`serial_tcp_bridge.py:191-197`).
- [x] Dynamically demonstrate duplicate command transmission/execution under transient response loss (PoC `poc_cmdv1_replay.py`, output `exec_count=2`).
- [x] Confirm replay impact is meaningful because `cmdv1` executes dangerous/non-idempotent commands (`init_v73.c:9391-9403`, `9678-9685`).
## Report
I validated the finding with targeted code inspection plus a dynamic PoC against the real `a90ctl.py` logic in this commit.

Key code evidence:
- `scripts/revalidation/a90ctl.py:83-87` sends the full command line on every exchange via `sock.sendall(("\n" + line + "\n").encode("utf-8"))`.
- `scripts/revalidation/a90ctl.py:117-151` adds a retry loop in `run_cmdv1_command()`; on each loop iteration it calls `bridge_exchange(...)` again with the same `line` (no nonce/sequence dedupe).
- `scripts/revalidation/a90ctl.py:91-92` retries when output is empty or contains `"serial device is not connected"`.
- `scripts/revalidation/serial_tcp_bridge.py:191-197` emits `[bridge] serial device is not connected; retry later`, which directly matches the retry trigger.
- `stage3/linux_init/init_v73.c:9678-9685` executes `cmdv1` payload via `execute_shell_command(&argv[1], ...)`; command table includes non-idempotent/dangerous operations (`writefile`, `run`, `netservice`, `usbacmreset`, `reboot`, `recovery`, `poweroff`) at `init_v73.c:9391-9403`.

Dynamic reproduction:
1) Ran `python3 /workspace/validation_artifacts/cmdv1-replay/poc_cmdv1_replay.py`.
   - Mock bridge behavior: first connection reads full `cmdv1 ...` line, simulates execution, then drops connection without END marker; second connection returns valid `A90P1 END`.
   - Output (`poc_output.txt`):
     - `"exec_count": 2`
     - `"lines": ["cmdv1 writefile /tmp/poc 1", "cmdv1 writefile /tmp/poc 1"]`
     - `"result_status": "ok"`
   This shows replay: same command was issued twice and still returned success.

2) Ran comparison script `python3 /workspace/validation_artifacts/cmdv1-replay/poc_compare_pre_post.py`.
   - Pre-commit emulation (single exchange): `exec_count=1`, error `A90P1 END marker not found`.
   - Current commit behavior: `exec_count=2`, result `ok`.
   This demonstrates the behavior was introduced by the retry change.

3) Additional retry-trigger check (`serial_missing_retry_output.txt`): first response set to bridge serial-missing text; client resent identical `cmdv1 status` line (observed twice).

Method attempts per instruction:
- Crash-style attempt: no memory crash path; only expected Python `RuntimeError` timeout.
- Valgrind: unavailable (`command not found`).
- Debugger: `lldb` run attempted; no exploitable crash trace (logic flaw, process exits with Python exception).

# Evidence
scripts/revalidation/a90ctl.py (L127 to 151)
  Note: Loop retries cmdv1 exchanges and reissues the same command after OSError or retryable text, with no deduplication token.
```
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
            )
        except OSError as exc:
            last_error = exc
            sleep_before_retry(deadline)
            continue

        if END_RE.search(text) is not None:
            return parse_protocol_output(text)
        if not should_retry_cmdv1_exchange(text):
            return parse_protocol_output(text)

        last_text = text
        sleep_before_retry(deadline)
```

scripts/revalidation/a90ctl.py (L83 to 87)
  Note: Each attempt sends the full command line to the bridge (`sock.sendall(...)`), so retries are replays.
```
    connect_timeout = min(3.0, max(0.1, timeout_sec))
    with socket.create_connection((host, port), timeout=connect_timeout) as sock:
        sock.settimeout(0.25)
        sock.sendall(("\n" + line + "\n").encode("utf-8"))
        data = read_until(sock, markers, timeout_sec)
```

scripts/revalidation/a90ctl.py (L91 to 92)
  Note: Retry condition includes empty output and bridge serial-missing message.
```
def should_retry_cmdv1_exchange(text: str) -> bool:
    return text.strip() == "" or BRIDGE_SERIAL_MISSING_TEXT in text
```

scripts/revalidation/serial_tcp_bridge.py (L191 to 197)
  Note: Bridge emits the exact serial-missing text used by new retry logic, triggering resend behavior.
```
        if self.serial_fd is None and not self.args.allow_client_without_serial:
            self.log(f"rejecting client from {addr[0]}:{addr[1]}: serial not connected")
            try:
                conn.sendall(b"[bridge] serial device is not connected; retry later\r\n")
            except OSError:
                pass
            conn.close()
```

stage3/linux_init/init_v73.c (L9391 to 9403)
  Note: Command set includes non-idempotent/dangerous operations (e.g., writefile, run, netservice, usbacmreset, reboot/recovery/poweroff), amplifying replay impact.
```
    { "writefile", handle_writefile, "writefile <path> <value...>", CMD_NONE },
    { "cpustress", handle_cpustress, "cpustress [sec] [workers]", CMD_BLOCKING },
    { "run", handle_run, "run <path> [args...]", CMD_BLOCKING },
    { "runandroid", handle_runandroid, "runandroid <path> [args...]", CMD_BLOCKING },
    { "startadbd", handle_startadbd, "startadbd", CMD_BACKGROUND },
    { "stopadbd", handle_stopadbd, "stopadbd", CMD_BACKGROUND },
    { "netservice", handle_netservice, "netservice [status|start|stop|enable|disable]", CMD_DANGEROUS },
    { "reattach", handle_reattach, "reattach", CMD_NONE },
    { "usbacmreset", handle_usbacmreset, "usbacmreset", CMD_DANGEROUS },
    { "sync", handle_sync, "sync", CMD_NONE },
    { "reboot", handle_reboot, "reboot", CMD_DANGEROUS | CMD_NO_DONE },
    { "recovery", handle_recovery, "recovery", CMD_DANGEROUS | CMD_NO_DONE },
    { "poweroff", handle_poweroff, "poweroff", CMD_DANGEROUS | CMD_NO_DONE },
```

stage3/linux_init/init_v73.c (L9678 to 9685)
  Note: Incoming `cmdv1` requests execute embedded command arguments directly; repeated sends mean repeated command execution.
```
        if (strcmp(argv[0], "cmdv1") == 0) {
            if (argc < 2) {
                char *usage_argv[] = { "cmdv1", NULL };

                execute_shell_command(usage_argv, 1, false);
            } else {
                execute_shell_command(&argv[1], argc - 1, true);
            }
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Downgraded from high to medium. The vulnerability is validated and in-scope, with executable PoC evidence of duplicate command execution. However, it is a replay/semantics flaw requiring local/physical bridge-path interference (or non-default exposure) rather than a broadly reachable unauthenticated remote path. The security effect is primarily integrity/availability on a single connected rooted device, not clear cross-tenant/fleet-scale compromise.
## Likelihood
low - Exploitation requires local/physical influence over bridge connectivity timing (or equivalent in exposed non-default bridge setups). This is plausible in shared lab/host threat models but not broadly reachable by default Internet attackers.
## Impact
medium - Replay can duplicate privileged root operations on the connected device, causing unintended state mutation or availability disruptions (e.g., repeated reboot/reset/run side effects). Impact is meaningful but primarily limited to the operator’s connected device/session.
## Assumptions
- scripts/revalidation/a90ctl.py is used in normal operator workflow as documented in scripts/revalidation/README.md
- Attacker can induce transient bridge/socket disruption (or serial-missing state) during an operator-issued cmdv1 command
- Assessment is static-repo based; no cloud/runtime telemetry was used
- Operator runs a90ctl cmdv1 command
- Bridge exchange returns empty output, serial-missing text, or socket error before END marker
- Attacker can influence local bridge connectivity path (or equivalent physical/local disruption)
## Path
[bridge disruption]
      -> [a90ctl retry loop]
      -> [duplicate cmdv1 send]
      -> [init_v73 root command executed again]
## Path evidence
- `scripts/revalidation/a90ctl.py:83-87` - Each bridge exchange sends full command line via sock.sendall; retries replay command bytes.
- `scripts/revalidation/a90ctl.py:91-92` - Retry condition includes empty output or 'serial device is not connected'.
- `scripts/revalidation/a90ctl.py:117-151` - Retry loop re-calls bridge_exchange with same line until timeout, without deduplication.
- `scripts/revalidation/serial_tcp_bridge.py:191-195` - Bridge emits serial-missing text that matches retry trigger.
- `stage3/linux_init/init_v73.c:9678-9685` - cmdv1 input is executed as shell command payload (argv[1..]) on device.
- `stage3/linux_init/init_v73.c:9391-9403` - Command table includes non-idempotent/dangerous operations (writefile, run, netservice, reboot, etc.).
## Narrative
The finding is real: commit 225089c added retry behavior in a90ctl that re-sends the full privileged cmdv1 line on each retry attempt. Retry triggers include socket errors and bridge output indicating missing serial, and there is no nonce/sequence deduplication. Device-side init_v73 executes cmdv1 payload commands directly as root, including dangerous/non-idempotent operations. Validation artifacts report executable PoCs showing duplicated command transmission/execution (exec_count=2). This is security-relevant integrity/availability risk, but attack preconditions are local/physical bridge-path influence, not broad unauthenticated Internet reachability.
## Controls
- Bridge default bind is localhost (127.0.0.1)
- Bridge single-client policy
- Auto-menu gating blocks some dangerous commands only in specific menu-active states
## Blindspots
- Static analysis cannot confirm real-world frequency of operator use of non-idempotent cmdv1 commands.
- No direct runtime measurement of how often bridge disruptions are attacker-induced versus accidental.
- If operators bind bridge to non-localhost in practice, likelihood could increase beyond this default-based estimate.
