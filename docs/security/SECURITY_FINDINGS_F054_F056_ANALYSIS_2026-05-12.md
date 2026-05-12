# F054-F056 Security Findings Analysis

Date: 2026-05-12
Source CSV: `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv`
Status: CSV imported and locally triaged
Patch plan: `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_PLAN_2026-05-12.md`

## Scope

This document tracks the post-H1/H2/H3 Codex Cloud findings imported as `F054`
through `F056`.
The CSV contains 10 rows. Seven rows duplicate the already tracked F047-F053
batch, and three rows are new.
Full CSV-derived detail is stored in per-finding files under
`docs/security/findings/`.

## Finding List

| id | severity | local status | title | result |
|---|---|---|---|---|
| F054 | `high` | `mitigated-host-batch-i1` | Observe-only broker can leak tcpctl auth token | valid broker observe read-boundary issue |
| F055 | `medium` | `mitigated-host-batch-i2` | Wi-Fi gate failure does not fail capability summary | valid fail-open preflight issue |
| F056 | `informational` | `mitigated-host-batch-i3` | Lifecycle token capture crashes before starting tcpctl | valid host validator availability regression |

## Local Code Check

### Broker observe read cluster

- `F054`: `scripts/revalidation/a90_broker.py` still includes `cat` in
  `OBSERVE_COMMANDS`. Native init `cat` opens the requested file path as root,
  and `NETSERVICE_TCP_TOKEN_PATH` is known as `/cache/native-init-tcpctl.token`.
  Therefore an observer-only broker client can request a sensitive token path
  unless broker-side path policy blocks it.

### Wi-Fi gate / capability summary cluster

- `F055`: `scripts/revalidation/kernel_capability_summary.py` runs
  `wififeas gate`, parses the decision text, but does not include the capture
  success/failure in `pass_ok`. If stale JSON evidence is valid and the live
  gate fails, the summary can still return PASS with `wifi_decision=unknown`.

### Lifecycle token namespace cluster

- `F056`: `scripts/revalidation/a90_broker_ncm_lifecycle_check.py` imports
  `get_tcpctl_token()` from `tcpctl_host.py`, but its parser namespace lacks
  tcpctl-host common fields such as `device_protocol` and `busy_retries`.
  Non-dry-run token capture can raise `AttributeError` before lifecycle
  validation starts.

### Duplicate rows from this CSV

| incoming title | duplicate of | current state |
|---|---|---|
| Live recovery test can leak tcpctl auth token | `F047` | `mitigated-host-batch-h1` |
| Broker forwards exclusive root commands without authorization | `F048` | `mitigated-host-batch-h1` |
| Predictable /tmp root dd target permits symlink overwrite | `F049` / `F045` | `closed-duplicate-of-F045` |
| Outer soak timeout can orphan live broker processes | `F050` | `mitigated-host-batch-h2` |
| Default lifecycle run can fail to stop tcpctl listener | `F051` | `mitigated-host-batch-h2` |
| NCM broker treats auth OK as command success | `F052` | `mitigated-host-batch-h1` |
| NCM preflight may run untrusted cache tcpctl as root | `F053` / `F046` | `closed-duplicate-of-F046` |

## Patch Batches

### Batch I1: Broker observe read boundary

Covers: `F054`.

Implemented direction:

1. Remove unrestricted `cat` from default observe-only broker access, or gate it
   behind explicit operator/exclusive permission.
2. Add broker-side sensitive path denial for token/log/runtime secret paths,
   at minimum `/cache/native-init-tcpctl.token`.
3. Keep structured observe commands such as `status`, `bootstatus`,
   `timeline`, `logpath`, and `selftest` available.
4. Add broker selftest and fake smoke coverage for blocked token reads.

### Batch I2: Wi-Fi capability summary fail-closed

Covers: `F055`.

Implemented direction:

1. Make `wifi_gate()` return both parsed decision and capture success state.
2. Treat missing/unverifiable `wififeas gate` execution as summary failure by
   default.
3. Keep `baseline-required` and `no-go` as valid successful decisions when the
   gate command itself ran and was parsed.
4. Add an explicit offline/stale-evidence mode only if a future workflow needs
   report generation without live device access.

### Batch I3: Lifecycle token namespace regression

Covers: `F056`.

Implemented direction:

1. Add missing `tcpctl_host` common namespace fields to the lifecycle wrapper,
   or call `get_tcpctl_token()` through a small compatibility namespace.
2. Add a focused non-dry-run fixture proving token capture does not raise
   `AttributeError`.
3. Keep dry-run behavior and token redaction unchanged.

## Recommended Priority

1. `F054` was patched first. It weakened the broker observe-only guarantee and could
   expose the tcpctl token.
2. `F055` was patched second. It gates the next Wi-Fi baseline work; Wi-Fi decisions
   should not proceed from a failed live gate.
3. `F056` was patched third. It is informational, but lifecycle validation should be
   reliable before more broker/NCM soak testing.

## Wi-Fi Gate Impact

Do not treat older v202 kernel capability summary outputs as a green Wi-Fi
preflight unless they were generated after the `F055` fail-closed patch or the
live `wififeas gate` result is independently verified. `F054` is now patched, but
broker observe/token boundaries should remain part of the pre-Wi-Fi exposure
checklist.
