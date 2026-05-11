# F048. Broker forwards exclusive root commands without authorization

## Metadata

| field | value |
|---|---|
| finding_id | `1c09efe426088191a862c203b91a3a92` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/1c09efe426088191a862c203b91a3a92 |
| severity | `high` |
| status | `mitigated-host-batch-h1` |
| detected_at | `2026-05-11T11:30:26.335390Z` |
| committed_at | `2026-05-11 18:45:32 +0900` |
| commit_hash | `1e85d1b0827ca33882abb88ae34a0abe211625b0` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The commit introduces a host-local multi-client broker intended to mediate access to the native-init root control channel. However, client identity is entirely self-supplied in JSON, and command_class is only computed/checked for consistency. In the worker, the only enforced policy is a block for the rebind-destructive class. All other classes, including exclusive and operator-action, are passed to the ACM cmdv1 backend and executed on the device as root. This defeats the broker's apparent role as a safe multiplexing boundary for observer/read-only clients: a compromised or untrusted local client with access to the private socket can issue arbitrary privileged device commands rather than being limited to observe commands. The default private Unix socket reduces exposure to same-account local clients, so this is not Internet-remote by default, but in shared lab/automation setups it becomes a direct root-device command execution path.

## Local Initial Assessment

- Confirmed against current code: broker classification distinguishes `observe`, `operator-action`, and `exclusive`, but worker enforcement only blocks `rebind-destructive`. Exclusive/operator commands can still dispatch to the privileged backend.

## Local Remediation

- Implemented in Batch H1; see `docs/security/SECURITY_FINDINGS_F047_F053_H1_REPORT_2026-05-12.md`. The broker now defaults to observe-only and requires explicit `--allow-operator` or `--allow-exclusive` for mutating command classes; rebind/destructive commands remain blocked.

## Codex Cloud Detail

Broker forwards exclusive root commands without authorization
Link: https://chatgpt.com/codex/cloud/security/findings/1c09efe426088191a862c203b91a3a92?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 1e85d1b
Author: shs02140@gmail.com
Created: 2026. 5. 11. 오후 8:30:26
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced missing authorization/enforcement in the new broker. The broker classifies commands but only blocks rebind/destructive commands; exclusive/default-exclusive commands are still dispatched to the root control backend.
The commit introduces a host-local multi-client broker intended to mediate access to the native-init root control channel. However, client identity is entirely self-supplied in JSON, and command_class is only computed/checked for consistency. In the worker, the only enforced policy is a block for the rebind-destructive class. All other classes, including exclusive and operator-action, are passed to the ACM cmdv1 backend and executed on the device as root. This defeats the broker's apparent role as a safe multiplexing boundary for observer/read-only clients: a compromised or untrusted local client with access to the private socket can issue arbitrary privileged device commands rather than being limited to observe commands. The default private Unix socket reduces exposure to same-account local clients, so this is not Internet-remote by default, but in shared lab/automation setups it becomes a direct root-device command execution path.

# Validation
## Rubric
- [x] Confirm the new broker is runnable and the relevant code path is active (`py_compile` and built-in `selftest` pass).
- [x] Verify request parsing uses self-supplied client identity/class only for syntax/consistency, not authorization.
- [x] Verify classifier maps exclusive/operator/unknown commands to dispatchable classes instead of rejecting them.
- [x] Dynamically prove the worker blocks only `rebind-destructive` while dispatching exclusive/operator/default-exclusive requests to a backend.
- [x] Verify the production ACM backend forwards the accepted argv to the cmdv1 bridge, making dispatch security-relevant for the privileged device channel.
## Report
Validated the finding as a real authorization/enforcement bug in the Python broker. The target is non-compiled Python, so a native crash/ASan path is not applicable; `python3 -m py_compile scripts/revalidation/a90_broker.py` and the built-in `selftest` both passed. `valgrind` and `gdb` were not installed in the container, but I used a non-interactive `pdb` trace and a socket-level PoC against the real BrokerServer.

Key evidence:
1. Production backend forwarding: `scripts/revalidation/a90_broker.py:194-201` passes `request.argv` directly to `run_cmdv1_command(..., request.argv, retry_unsafe=False)`. `scripts/revalidation/a90ctl.py:216-241` encodes and sends that command to the bridge via `bridge_exchange`. A monkeypatch check confirmed AcmCmdv1Backend receives and forwards `['run', 'id']` unchanged: `(0, 'ok', 'ok')` and call record `{'argv': ['run', 'id'], 'retry_unsafe': False}`.
2. Classification permits dangerous classes: `scripts/revalidation/a90_broker.py:247-253` returns `operator-action`, `exclusive`, `observe`, or defaults unknown commands to `exclusive`; it does not reject exclusive/operator/unknown commands.
3. Parser accepts self-supplied identity/class only for consistency: `scripts/revalidation/a90_broker.py:287-312` validates `client_id` syntax, validates `argv`, computes `actual_class`, and only rejects if a supplied class mismatches. There is no authentication, token, peer credential check, or authorization map.
4. Worker enforcement only blocks rebind/destructive: `scripts/revalidation/a90_broker.py:421-427` raises only for `request.command_class == 'rebind-destructive'`, then calls `self.backend.execute(request)` for every other class.
5. Socket exposure is local/same-user by default, not remote: `scripts/revalidation/a90_broker.py:510-511` binds a Unix socket and chmods it `0600`, matching the suspected local/same-account exposure model.

Dynamic PoC result: `/workspace/validation_artifacts/a90_broker_authz_poc/poc_broker_authz.py` starts the real BrokerServer over a Unix socket with a recording backend and connects as self-supplied client `attacker:selfsupplied`. It showed that `run id` with no requested class was classified `exclusive` and executed, `menu` was classified `operator-action` and executed, an unknown command was classified `exclusive` and executed, while only `reboot` was blocked with `operator-required`. This directly reproduces the missing authorization boundary: the broker dispatches privileged non-observe command classes instead of enforcing observer/read-only restrictions.

Non-interactive pdb evidence: `pdb_output.txt` breaks in classification/parser code for `argv=['menu']` and shows `name == 'menu'`, `actual_class == 'operator-action'`, `requested_class == 'operator-action'`, then returns `BrokerRequest(... client_id='attacker:selfsupplied', ... command_class='operator-action')` without any authorization decision.

# Evidence
scripts/revalidation/a90_broker.py (L187 to 202)
  Note: The ACM backend forwards the provided argv directly to run_cmdv1_command, which sends commands to the privileged native-init control channel.
```
class AcmCmdv1Backend(Backend):
    name = "acm-cmdv1"

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def execute(self, request: BrokerRequest) -> tuple[int, str, str]:
        result: ProtocolResult = run_cmdv1_command(
            self.host,
            self.port,
            request.timeout_ms / 1000.0,
            request.argv,
            retry_unsafe=False,
        )
        return result.rc, result.status, result.text
```

scripts/revalidation/a90_broker.py (L230 to 253)
  Note: Commands are classified, but unknown and dangerous commands default to the exclusive class rather than being rejected.
```
def classify_command(argv: list[str]) -> str:
    if not argv:
        raise BrokerError("bad-request", "argv must not be empty")

    name = argv[0]
    if name in REBINDS_OR_DESTRUCTIVE_COMMANDS:
        return "rebind-destructive"

    allowed_subcommands = OBSERVE_SUBCOMMANDS.get(name)
    if allowed_subcommands is not None:
        subcommand = command_subcommand(argv)
        if subcommand is not None and subcommand in allowed_subcommands:
            return "observe"
        if subcommand is None and name in ABSENT_SUBCOMMAND_DEFAULTS_TO_STATUS:
            return "observe"
        return "exclusive"

    if name in OPERATOR_COMMANDS:
        return "operator-action"
    if name in EXCLUSIVE_COMMANDS:
        return "exclusive"
    if name in OBSERVE_COMMANDS:
        return "observe"
    return "exclusive"
```

scripts/revalidation/a90_broker.py (L287 to 312)
  Note: The request parser only validates request shape and a self-supplied client_id/class; it does not authenticate the client or authorize command classes.
```
def parse_wire_request(payload: dict[str, Any]) -> BrokerRequest:
    if payload.get("proto") != PROTO:
        raise BrokerError("bad-request", f"proto must be {PROTO}")
    request_id = validate_id(payload.get("id"), "id", REQUEST_ID_RE)
    client_id = payload.get("client_id", f"pid:{os.getpid()}")
    client_id = validate_id(client_id, "client_id", CLIENT_ID_RE)
    op = payload.get("op")
    if op != "cmd":
        raise BrokerError("bad-request", "only op=cmd is supported")
    argv = validate_argv(payload.get("argv"))
    timeout_ms = parse_timeout_ms(payload.get("timeout_ms"))
    actual_class = classify_command(argv)
    requested_class = payload.get("class")
    if requested_class is not None and requested_class != actual_class:
        raise BrokerError(
            "bad-request",
            f"class mismatch: requested {requested_class!r}, actual {actual_class!r}",
        )
    return BrokerRequest(
        request_id=request_id,
        client_id=client_id,
        op=op,
        argv=argv,
        timeout_ms=timeout_ms,
        command_class=actual_class,
    )
```

scripts/revalidation/a90_broker.py (L421 to 428)
  Note: The worker blocks only rebind-destructive commands, then executes all other classes, including exclusive/operator/default-exclusive commands.
```
            try:
                if request.command_class == "rebind-destructive":
                    raise BrokerError(
                        "operator-required",
                        "rebind/destructive command is not broker-multiplexed; use foreground raw control",
                    )
                rc, status, text = self.backend.execute(request)
                duration_ms = monotonic_ms() - started
```

Proposed patch:
diff --git a/scripts/revalidation/a90_broker.py b/scripts/revalidation/a90_broker.py
index 25ea0f992865083ffc1e6dd7e122c5b30531dedb..858cd5d782ad89e2165bd8899d663a3986920701 100644
--- a/scripts/revalidation/a90_broker.py
+++ b/scripts/revalidation/a90_broker.py
@@ -397,54 +397,54 @@ class BrokerServer:
 
     def audit(self, event: str, payload: dict[str, Any]) -> None:
         record = {"ts_ms": now_ms(), "event": event, **payload}
         with self.audit_lock:
             append_private_jsonl(self.audit_path, record)
 
     def worker_loop(self) -> None:
         while True:
             item = self.work_queue.get()
             if item is None:
                 self.work_queue.task_done()
                 return
             started = monotonic_ms()
             request = item.request
             self.audit(
                 "dispatch",
                 {
                     "id": request.request_id,
                     "client_id": request.client_id,
                     "argv": request.argv,
                     "class": request.command_class,
                     "backend": self.backend.name,
                 },
             )
             try:
-                if request.command_class == "rebind-destructive":
+                if request.command_class != "observe":
                     raise BrokerError(
                         "operator-required",
-                        "rebind/destructive command is not broker-multiplexed; use foreground raw control",
+                        "only observe-class commands are broker-multiplexed; use foreground raw control",
                     )
                 rc, status, text = self.backend.execute(request)
                 duration_ms = monotonic_ms() - started
                 response = BrokerResponse(
                     proto=PROTO,
                     request_id=request.request_id,
                     ok=rc == 0 and status == "ok",
                     rc=rc,
                     status=status,
                     duration_ms=duration_ms,
                     backend=self.backend.name,
                     command_class=request.command_class,
                     text=text,
                 )
             except BrokerError as exc:
                 duration_ms = monotonic_ms() - started
                 response = response_from_error(
                     request.request_id,
                     exc.status,
                     str(exc),
                     command_class=request.command_class,
                     backend=self.backend.name,
                     duration_ms=duration_ms,
                 )
             except Exception as exc:  # noqa: BLE001 - broker must report backend failures
@@ -603,52 +603,52 @@ def cmd_selftest(_: argparse.Namespace) -> int:
         status_request = {
             "proto": PROTO,
             "id": "selftest-status",
             "client_id": "selftest",
             "op": "cmd",
             "argv": ["status"],
             "timeout_ms": 1000,
             "class": "observe",
         }
         status_response = connect_and_call(socket_path, status_request, 3.0)
         if not status_response.get("ok"):
             raise RuntimeError(f"status response failed: {status_response}")
         if status_response.get("class") != "observe":
             raise RuntimeError(f"unexpected status class: {status_response}")
 
         mountsd_request = {
             "proto": PROTO,
             "id": "selftest-mountsd",
             "client_id": "selftest",
             "op": "cmd",
             "argv": ["mountsd"],
             "timeout_ms": 1000,
             "class": "exclusive",
         }
         mountsd_response = connect_and_call(socket_path, mountsd_request, 3.0)
-        if not mountsd_response.get("ok") or mountsd_response.get("class") != "exclusive":
-            raise RuntimeError(f"bare mountsd was not classified exclusive: {mountsd_response}")
+        if mountsd_response.get("status") != "operator-required" or mountsd_response.get("class") != "exclusive":
+            raise RuntimeError(f"exclusive class command was not blocked: {mountsd_response}")
 
         blocked_request = {
             "proto": PROTO,
             "id": "selftest-reboot",
             "client_id": "selftest",
             "op": "cmd",
             "argv": ["reboot"],
             "timeout_ms": 1000,
             "class": "rebind-destructive",
         }
         blocked_response = connect_and_call(socket_path, blocked_request, 3.0)
         if blocked_response.get("status") != "operator-required":
             raise RuntimeError(f"reboot was not blocked: {blocked_response}")
 
         print("a90_broker selftest: PASS")
         return 0
     finally:
         try:
             socket_file = temp_dir / DEFAULT_SOCKET_NAME
             if socket_file.exists() and not socket_file.is_symlink():
                 socket_file.unlink()
             audit_file = temp_dir / DEFAULT_AUDIT_NAME
             if audit_file.exists() and not audit_file.is_symlink():
                 audit_file.unlink()
             meta_file = temp_dir / "broker.json"

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Severity remains high, not critical. The code evidence supports a real authorization/enforcement flaw: parser identity is self-supplied, exclusive/operator/unknown commands are accepted, the worker only blocks rebind-destructive commands, and the ACM backend forwards argv to the privileged cmdv1 channel. The impact is major because accepted commands execute against the attached device's root native-init environment. The probability is constrained by exposure: the broker binds a private local Unix socket and chmods it 0600 inside a private directory, so this is not Internet-reachable and generally requires same-user/root local access or an untrusted automation client. That local/private precondition prevents critical rating, but the repository threat model includes shared host/lab automation control-channel boundaries, making high appropriate.
## Likelihood
medium - Exploitation is straightforward once the local socket is reachable, and validation demonstrated the path with a real BrokerServer. However, default filesystem permissions restrict access to same Unix user/root and the broker is host-local, so exploitation generally requires a compromised/untrusted local automation client or shared lab account rather than remote access.
## Impact
high - A client that reaches the broker can cause non-observe privileged commands to be dispatched to the native-init root control channel on the attached device. This can execute commands, start privileged services, mutate device state, and compromise device integrity/availability. Impact is limited to the attached device/control session rather than a fleet or Internet service.
## Assumptions
- The broker is intended to be used as a host-local multiplexing boundary for multiple clients, including observer/read-only automation clients.
- A realistic attacker is a compromised or untrusted local process running as the broker socket owner, root, or otherwise able to access the private Unix socket in a shared lab or automation environment.
- The ACM bridge and attached native-init device are available when the broker backend is configured as the default acm-cmdv1 backend.
- a90_broker.py serve is running
- attacker can connect to the broker Unix socket, normally requiring same Unix user or root because the socket is chmod 0600 inside a private directory
- broker uses acm-cmdv1 backend or another privileged backend
- attached A90 native-init control channel is reachable through the bridge
## Path
local client -> A90B1 Unix socket -> parser/classifier -> worker permits non-rebind classes -> acm-cmdv1 backend -> device native-init root command
## Path evidence
- `scripts/revalidation/a90_broker.py:187-202` - AcmCmdv1Backend forwards the BrokerRequest argv directly to run_cmdv1_command with retry_unsafe disabled but without any authorization decision.
- `scripts/revalidation/a90_broker.py:230-253` - The classifier marks operator commands as operator-action, known dangerous commands as exclusive, and unknown commands as exclusive instead of rejecting them.
- `scripts/revalidation/a90_broker.py:287-312` - Request parsing accepts a self-supplied client_id and only checks that any supplied class matches the computed class; it does not authenticate or authorize the client.
- `scripts/revalidation/a90_broker.py:421-427` - The worker blocks only rebind-destructive commands and executes all other command classes through the backend.
- `scripts/revalidation/a90_broker.py:507-518` - The service is exposed as a local Unix socket with chmod 0600, confirming local/private exposure rather than public network exposure.
- `scripts/revalidation/a90ctl.py:216-241` - run_cmdv1_command encodes the command and sends it through bridge_exchange to the ACM bridge.
- `scripts/revalidation/README.md:41-47` - Repository documentation describes a90_broker.py as the A90B1 host-local broker that serializes multiple host client requests and forwards commands through the ACM cmdv1 backend.
- `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md:403-409` - Planning documentation frames the broker as a policy boundary for USB ACM serial bridge, cmdv1/A90P1, NCM tcpctl, and rshell, with command classes and non-public multi-client goals.
## Narrative
The finding is real and in scope. The broker exposes a host-local Unix socket and parses attacker-controlled JSON requests, but it only validates syntax and command-class consistency. client_id is self-supplied, class is only compared to the broker's own classifier, and no role or peer-credential authorization is enforced. The worker blocks only reboot/recovery/poweroff-style rebind-destructive commands, then forwards every other class to AcmCmdv1Backend. That backend sends request.argv to run_cmdv1_command, which reaches the native-init root control channel. The default 0700 runtime directory and 0600 socket significantly reduce exposure to same-user/root local clients, so this is not critical or Internet-remote. In the repository's shared-lab/automation threat model, however, it is still a high-impact local privilege-boundary failure because an observer/read-only client with broker access can issue root device commands.
## Controls
- Private runtime directory mode 0700 via ensure_private_dir
- Broker Unix socket chmod 0600
- Host-local AF_UNIX socket rather than public network listener
- Default backend bridge host is 127.0.0.1
- Rebind/destructive commands reboot, recovery, and poweroff are blocked
- Audit JSONL is written through private/no-follow helpers
- No strong authentication or authorization for command classes
## Blindspots
- Static repository review cannot confirm how often the broker is run in real deployments or whether untrusted observer clients are actually granted socket access.
- Static review cannot verify whether the underlying localhost ACM bridge is separately exposed to all local users, which could reduce the broker-specific privilege boundary in some deployments.
- No cloud, Kubernetes, or production ingress manifests were present for this host-local tool.
- Attached device state and native-init runtime behavior were inferred from repository code and prior validation evidence rather than live hardware testing in this stage.

