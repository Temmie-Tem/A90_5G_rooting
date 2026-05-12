# F047-F053 Security Findings Analysis

Date: 2026-05-12
Source CSV: `docs/security/scans/codex-security-findings-2026-05-11T19-48-19.047Z.csv`
Status: full detail pasted and locally triaged
Patch plan: `docs/security/batches/SECURITY_FINDINGS_F047_F053_PATCH_PLAN_2026-05-12.md`

## Scope

This document tracks the post-v200 Codex Cloud findings imported as `F047` through `F053`.
Full detail is stored in per-finding files under `docs/security/findings/`.
This triage is based on the pasted Codex Cloud detail plus current local code inspection.

## Finding List

| id | severity | local status | title | result |
|---|---|---|---|---|
| F047 | `high` | `confirmed-pending-patch` | Live recovery test can leak tcpctl auth token | valid live-test token disclosure path |
| F048 | `high` | `confirmed-pending-patch` | Broker forwards exclusive root commands without authorization | valid broker authorization boundary issue |
| F049 | `high` | `closed-duplicate-of-F045` | Predictable /tmp root dd target permits symlink overwrite | duplicate/reopen of F045; current code appears fixed |
| F050 | `medium` | `confirmed-pending-patch` | Outer soak timeout can orphan live broker processes | valid process-tree cleanup issue |
| F051 | `medium` | `confirmed-pending-patch` | Default lifecycle run can fail to stop tcpctl listener | valid token/lifecycle cleanup issue |
| F052 | `medium` | `confirmed-pending-patch` | NCM broker treats auth OK as command success | valid tcpctl response parser issue |
| F053 | `medium` | `closed-duplicate-of-F046` | NCM preflight may run untrusted cache tcpctl as root | duplicate/reopen of F046; current code appears fixed |

## Local Code Check

### Broker / tcpctl auth cluster

- `F047`: `scripts/revalidation/a90_broker_recovery_tests.py` still hard-codes port `29999`, starts `ncm-tcpctl`, and sends `run /cache/bin/toybox uptime` without a dummy token or closed-port proof. This is valid when an attacker-controlled listener is present on that port.
- `F048`: `scripts/revalidation/a90_broker.py` classifies commands into observe/operator/exclusive/rebind classes, but `BrokerServer.worker_loop()` only rejects `rebind-destructive`. The current broker still dispatches exclusive/operator commands to the backend.
- `F052`: `NcmTcpctlBackend.tcpctl_status()` still treats any `\nOK` in the combined response as success. This can accept `OK authenticated` even when the final command line is `ERR exit=N`.

### Lifecycle / cleanup cluster

- `F050`: `scripts/revalidation/a90_broker_soak_suite.py` uses `subprocess.run(..., timeout=...)` around validators. Timeout kills the immediate validator process and can bypass the validator's own broker cleanup path.
- `F051`: `scripts/revalidation/a90_broker_ncm_lifecycle_check.py` starts long-running `tcpctl_host.py start`, then runs smoke/stop without passing a token unless the operator supplied one. This can require a second ACM token lookup while the start process owns the single-client serial bridge.

### Duplicate / already-mitigated cluster

- `F049`: current `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py` uses safe path helpers and a per-profile temp directory instead of directly writing to predictable `/tmp/<run>-<profile>-mem.bin`. This matches the previously mitigated `F045` pattern.
- `F053`: current `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py` only accepts `/bin/a90_tcpctl` and explicitly refuses `/cache/bin` fallback. This matches the previously mitigated `F046` pattern.

## Patch Batches

### Batch H1: Broker authorization and tcpctl parser

Covers: `F047`, `F048`, `F052`.

Planned direction:

1. Add broker authorization policy: default observe-only for generic clients; require explicit operator mode/token/allow flag for `operator-action` and `exclusive` classes.
2. Keep `rebind-destructive` out of broker multiplexing.
3. Change `NcmTcpctlBackend.tcpctl_status()` to parse the final non-empty tcpctl protocol line instead of searching for any `OK`.
4. Change live recovery listener-down test so it cannot leak a real token to port `29999`: either closed-port precheck or explicit dummy/no-auth negative-test mode.

### Batch H2: Broker lifecycle cleanup

Covers: `F050`, `F051`.

Planned direction:

1. Replace suite-level `subprocess.run(timeout=...)` with a process-group-aware helper that kills the entire child tree on timeout and still writes failure evidence.
2. In lifecycle wrapper, obtain/pass the tcpctl token consistently to start/smoke/stop, or release the bridge-owning start process before fallback cleanup.
3. Ensure cleanup always attempts to shut down or kill host/device listener paths and records explicit residual status.

### Batch H3: Duplicate closure evidence

Covers: `F049`, `F053`.

Planned direction:

1. Compare Codex Cloud line references against current code.
2. Keep `F049` linked to `F045` closure evidence unless a fresh current-code reproduction exists.
3. Keep `F053` linked to `F046` closure evidence unless a fresh current-code reproduction exists.

## Recommended Priority

1. Patch `F048` and `F052` first: they affect broker command integrity and are central to later multi-client/NCM workflows.
2. Patch `F047` in the same batch if touching broker/tcpctl auth code.
3. Patch `F050` and `F051` before running more long NCM/broker soak workflows.
4. Mark `F049`/`F053` as duplicate/currently mitigated after one explicit local diff check in the closure note.

## Wi-Fi Gate Impact

Do not move to Wi-Fi exposure until Batch H1 and H2 are fixed and rescanned.
Wi-Fi would widen the network threat boundary; the current open broker/tcpctl issues are still USB-local/lab-local, but the same patterns become more serious if any control path is reachable beyond the local USB/NCM setup.
