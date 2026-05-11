# F047-F053 Patch Plan

Date: `2026-05-12`
Source analysis: `docs/security/SECURITY_FINDINGS_F047_F053_ANALYSIS_2026-05-12.md`
Scope: host-side broker/tcpctl/recovery/lifecycle hardening before Wi-Fi work

## Summary

The new `F047` through `F053` findings are not independent bugs. They expose
two unfinished parts of the v185 broker design:

1. The broker has command classification, but not a complete authorization
   boundary.
2. The host validators launch nested broker/tcpctl processes, but do not yet
   have a shared process-tree cleanup model.

Before Wi-Fi bring-up or any wider network exposure, patch the confirmed issues
in two batches:

- Batch H1: broker authorization, tcpctl response integrity, and live recovery
  token isolation.
- Batch H2: process-tree cleanup and lifecycle token propagation.

`F049` and `F053` are currently treated as duplicate/reopened scans of already
mitigated `F045` and `F046`.

## Document Relationship

### Existing design intent

- `docs/plans/NATIVE_INIT_V185_COMMUNICATION_BROKER_PLAN_2026-05-11.md`
  defines the intended broker boundary:
  - observe commands are safe and retryable;
  - operator actions are serialized;
  - exclusive commands require explicit locking/control;
  - rebind/destructive commands stay out of broker multiplexing.
- `docs/plans/NATIVE_INIT_V193_BROKER_AUTH_HARDENING_PLAN_2026-05-11.md`
  and `docs/reports/NATIVE_INIT_V193_BROKER_AUTH_HARDENING_2026-05-11.md`
  hardened token handling and no-auth mode, but did not implement full
  authorization for `operator-action` and `exclusive` command classes.
- `docs/security/SECURITY_FINDINGS_F045_F046_ANALYSIS_2026-05-11.md`
  already covers the mutable-device-path trust boundary that appears again in
  `F049` and `F053`.

### New findings mapped to design gaps

| gap | findings | meaning |
|---|---|---|
| Missing broker authorization | `F048` | command class is computed but not enforced beyond `rebind-destructive` |
| TCP response integrity | `F052` | auth success line can mask later command failure |
| Live negative-test secret isolation | `F047` | recovery test can send real token to wrong listener |
| Nested process cleanup | `F050` | suite timeout can bypass child validator cleanup |
| Token propagation/lifecycle cleanup | `F051` | start/smoke/stop subprocesses do not share token state |
| Duplicate/reopen of prior host fixes | `F049`, `F053` | current code appears already mitigated through `F045`/`F046` patches |

## Reference Notes

- MITRE CWE-862 recommends server-side access control tied to business logic and
  a default-deny policy. This supports moving broker authorization into the
  broker worker before backend dispatch instead of trusting client-supplied
  `client_id` or command class.
  - https://cwe.mitre.org/data/definitions/862.html
- Python `subprocess` documents that `start_new_session=True` calls `setsid()`
  in the child process, which is the right basis for process-group cleanup.
  It also documents that `Popen.communicate(timeout=...)` raises
  `TimeoutExpired` and does not kill the child by itself, so callers must kill
  and then finish communication.
  - https://docs.python.org/3/library/subprocess.html
- Linux `unix(7)` documents `SO_PEERCRED`, which can retrieve the peer PID/UID/GID
  for a connected Unix-domain socket. This is useful for broker audit and
  owner checks, but it is not sufficient by itself to separate multiple clients
  running as the same Unix user.
  - https://man7.org/linux/man-pages/man7/unix.7.html

## Batch H1: Broker Authorization and TCP Integrity

Covers: `F047`, `F048`, `F052`.

### H1.1 Add explicit broker policy

Add a small broker policy object in `scripts/revalidation/a90_broker.py`.

Recommended shape:

```text
BrokerPolicy
  allow_operator: bool = false
  allow_exclusive: bool = false
  deny_rebind_destructive: always true
```

CLI:

```text
a90_broker.py serve --allow-operator
a90_broker.py serve --allow-exclusive
```

Default behavior:

- `observe`: allowed;
- `operator-action`: rejected with `operator-required` unless
  `--allow-operator` or `--allow-exclusive`;
- `exclusive`: rejected with `exclusive-required` unless `--allow-exclusive`;
- `rebind-destructive`: always rejected from the broker path.

Important constraint:

- Do not treat client-supplied `client_id` or `class` as authorization.
  They are request metadata only.
- Keep socket mode/private runtime directory checks, but do not rely on them as
  the only policy. A same-user client can still reach a same-user socket.

### H1.2 Add peer credential audit, not as sole auth

On Linux, capture Unix socket peer credentials for audit:

```text
peer_pid
peer_uid
peer_gid
```

Use `SO_PEERCRED` only as an audit/diagnostic field or optional owner check.
It should not replace command-class authorization, because multiple tools can
run under the same user.

### H1.3 Fix `ncm-tcpctl` status parsing

Current issue:

```text
OK authenticated
[exit 1]
ERR exit=1
```

must be failure, not success.

Patch direction:

- Split response into non-empty stripped lines.
- Inspect the final protocol trailer.
- Return success only when the final line is exactly `OK`.
- Treat final `ERR ...` as `error`.
- Keep auth failures classified as `auth-failed`.
- Consider `OK shutdown` separately only if broker later maps `shutdown`
  through the NCM backend. Current broker NCM path primarily maps absolute
  `run` commands, so final `OK` is enough for the first fix.

### H1.4 Stop live recovery token leakage

Patch `scripts/revalidation/a90_broker_recovery_tests.py`.

Recommended approach:

1. Do a closed-port precheck before `run_ncm_down_test`.
   - If `device_ip:port` is open, fail/skip the negative test before starting
     the broker and before retrieving any token.
2. Avoid the fixed port if practical.
   - Keep an override for reproducibility, but pick a high random candidate
     and precheck it by default.
3. Pass safe auth options into the negative test.
   - For the listener-down negative test, use a mode that cannot send the real
     token to an arbitrary listener.
   - If using `--no-auth`, it must also pass `--allow-no-auth` and must be
     clearly limited to the negative test.
4. Expose `--token`, `--no-auth`, and `--allow-no-auth` on the recovery runner
   only if needed for explicit testing. Do not silently fetch and forward a
   real token to an untrusted port.

### H1 validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_recovery_tests.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py

git diff --check
```

Host-only regression:

```bash
python3 scripts/revalidation/a90_broker.py selftest
python3 scripts/revalidation/a90_broker_auth_hardening_check.py \
  --run-dir tmp/a90-h1-auth-check
```

New required checks:

- default fake broker:
  - `status` succeeds;
  - `run id` is rejected with `exclusive-required`;
  - `menu` is rejected with `operator-required`;
  - `reboot` remains rejected with `operator-required` or equivalent
    destructive/rebind status.
- explicit `--allow-exclusive` fake broker:
  - `run id` succeeds through fake backend;
  - audit records include command class and policy mode.
- `NcmTcpctlBackend.tcpctl_status()` fixture:
  - `OK authenticated\n[exit 1]\nERR exit=1\n` returns failure;
  - `OK authenticated\n[exit 0]\nOK\n` returns success;
  - `ERR auth-required` and `ERR auth-failed` return `auth-failed`.
- recovery malicious-listener fixture:
  - listener must not receive a real token;
  - closed-port negative path still produces transport-error evidence.

## Batch H2: Broker Lifecycle Cleanup

Covers: `F050`, `F051`.

### H2.1 Replace outer `subprocess.run(timeout=...)`

Patch `scripts/revalidation/a90_broker_soak_suite.py`.

Add a local or shared helper:

```text
run_process_group(command, timeout_sec)
  Popen(..., start_new_session=True)
  communicate(timeout=timeout_sec)
  on TimeoutExpired:
    killpg(SIGTERM)
    communicate(short_timeout)
    killpg(SIGKILL) if still alive
    communicate()
  return rc, timed_out, stdout
```

Required behavior:

- timeout is recorded as a failed suite step;
- output is still written to the evidence directory;
- no Python traceback is the normal timeout result;
- child broker process groups are killed, not only the immediate validator
  process.

### H2.2 Propagate tcpctl token through lifecycle wrapper

Patch `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`.

Current issue:

- `tcpctl_host.py start` obtains token in its own process;
- smoke and stop do not inherit that token unless the operator supplied
  `--token`;
- start can occupy the single-client serial bridge while smoke/stop attempt
  another token fetch.

Recommended approach:

1. Before starting `tcpctl_host.py start`, obtain one token in the wrapper if
   `--token` was not supplied.
2. Pass that token to start, broker smoke, and stop commands.
3. Redact the token in stored command/evidence text.
4. Cleanup order:
   - first try authenticated `tcpctl shutdown` with the known token;
   - if token shutdown cannot run because the bridge is occupied, terminate the
     host start process group, then retry stop/status if safe;
   - always record residual listener status when possible.

### H2 validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_soak_suite.py \
  scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  scripts/revalidation/tcpctl_host.py

git diff --check
```

Host-only fixtures:

- forced suite timeout:
  - suite returns controlled FAIL;
  - summary/report is written;
  - no orphan broker process remains.
- fake single-client bridge lifecycle:
  - planned commands include a redacted `--token`;
  - smoke and stop do not attempt a second token fetch through the occupied
    bridge;
  - cleanup leaves no fake tcpctl listener alive.

Live validation after host-only PASS:

```bash
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --run-dir tmp/a90-h2-ncm-lifecycle
```

Run only when NCM is intentionally up and the device is in a safe lab state.

## Batch H3: Duplicate Closure Evidence

Covers: `F049`, `F053`.

### H3.1 F049 duplicate check

Current code check:

- `cpu_memory_profiles.py` now uses safe path helpers.
- It creates a per-profile temp directory.
- It no longer writes directly to predictable
  `/tmp/<run-id>-<profile>-mem.bin`.

Action:

- Keep `F049` linked to `F045` and current mitigation evidence.
- If Codex Cloud still reports it after a fresh scan, compare the exact line
  numbers and update the closure note.

### H3.2 F053 duplicate check

Current code check:

- `ncm_tcp_preflight.py` only accepts trusted `/bin/a90_tcpctl`.
- It explicitly refuses `/cache/bin/a90_tcpctl` fallback.

Action:

- Keep `F053` linked to `F046` and current mitigation evidence.
- If Codex Cloud still reports it after a fresh scan, compare the exact line
  numbers and update the closure note.

## Implementation Order

1. Commit the imported security docs and this patch plan.
2. Implement Batch H1.
3. Run H1 host-only validation.
4. Commit H1.
5. Implement Batch H2.
6. Run H2 host-only validation.
7. Run live NCM lifecycle validation only after host-only tests pass.
8. Commit H2.
9. Update `F049`/`F053` closure notes and run fresh scan.

## Wi-Fi Gate

Do not start Wi-Fi bring-up while any of these remain unresolved:

- `F047`
- `F048`
- `F050`
- `F051`
- `F052`

Reason:

- Wi-Fi can widen the control-plane reachability boundary.
- The current issues are mostly host-local/USB-local, but the same broker/tcpctl
  weaknesses become materially riskier if any path becomes reachable beyond the
  local USB/NCM lab setup.

