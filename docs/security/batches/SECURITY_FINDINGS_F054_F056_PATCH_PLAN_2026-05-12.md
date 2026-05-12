# F054-F056 Patch Plan

Date: `2026-05-12`
Source analysis: `docs/security/batches/SECURITY_FINDINGS_F054_F056_ANALYSIS_2026-05-12.md`
Scope: host-side broker observe boundary, Wi-Fi summary fail-closed behavior,
and lifecycle validator token namespace repair

## Summary

The new `F054` through `F056` findings are smaller than the previous H1/H2
security batch, but two of them block the next Wi-Fi track:

1. `F054` shows that observe-only broker policy still allows an unrestricted
   root file read through `cat`.
2. `F055` shows that the v202 kernel capability summary can report PASS even
   when the live Wi-Fi gate could not be verified.

`F056` is informational, but it affects the lifecycle validator used to prove
the broker/NCM tcpctl listener starts and stops cleanly.

Patch in three small batches:

- Batch I1: broker observe read boundary.
- Batch I2: Wi-Fi capability summary fail-closed behavior.
- Batch I3: lifecycle token namespace regression.

## Document Relationship

### Existing design intent

- `docs/plans/NATIVE_INIT_V185_COMMUNICATION_BROKER_PLAN_2026-05-11.md`
  defines broker observe/operator/exclusive classes. `F054` shows that
  class-level observe is not enough when an observe command accepts arbitrary
  root-readable paths.
- `docs/reports/NATIVE_INIT_V202_KERNEL_CAPABILITY_SUMMARY_2026-05-12.md`
  says the summary merges kernel evidence with the live Wi-Fi gate. `F055`
  shows that the gate result is parsed but not treated as a required live
  success condition.
- `docs/security/batches/SECURITY_FINDINGS_F047_F053_H2_REPORT_2026-05-12.md`
  records lifecycle token propagation. `F056` is a follow-up regression in the
  wrapper namespace used to acquire that token.

### New findings mapped to design gaps

| gap | findings | meaning |
|---|---|---|
| Observe read boundary | `F054` | command class is safe, but command arguments can still read secrets |
| Wi-Fi preflight fail-open | `F055` | summary pass/fail ignores live gate command success |
| Host validator compatibility | `F056` | lifecycle wrapper does not provide all fields expected by `tcpctl_host.get_tcpctl_token()` |

## Batch I1: Broker Observe Read Boundary

Covers: `F054`.

### I1.1 Remove unrestricted `cat` from observe-only policy

Default broker policy should not allow arbitrary path reads through `cat`.

Recommended options:

```text
Option A: classify cat as operator-action by default
Option B: keep cat observe only for an explicit allowlist of safe paths
```

Recommended first implementation: Option A. It is simpler and fail-closed.

Expected behavior:

- `status`, `bootstatus`, `timeline`, `logpath`, `selftest`, and similar
  structured observe commands remain default-allowed.
- `cat /cache/native-init-tcpctl.token` is blocked by default.
- `cat <path>` can run only when broker is started with explicit operator or
  exclusive permission, or after a future safe allowlist is implemented.

### I1.2 Add sensitive path guard anyway

Add a broker-side guard for sensitive known paths so future command
classification changes do not re-open token disclosure.

Minimum deny paths/prefixes:

```text
/cache/native-init-tcpctl.token
/mnt/sdext/a90/runtime/
/cache/a90/runtime/
```

Do not log full token file contents in failure evidence.

### I1.3 Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker.py
python3 scripts/revalidation/a90_broker.py selftest
python3 scripts/revalidation/a90_broker_auth_hardening_check.py --run-dir tmp/a90-i1-auth-check
python3 scripts/revalidation/a90_broker_concurrent_smoke.py --backend fake --clients 2 --rounds 2 --include-blocked --run-dir tmp/a90-i1-fake-smoke
```

Acceptance:

- `cat /cache/native-init-tcpctl.token` returns a blocked broker policy result
  in default observe-only mode.
- Observe commands that do not expose arbitrary file contents still pass.
- `--allow-operator` or `--allow-exclusive` behavior remains explicit.

## Batch I2: Wi-Fi Capability Summary Fail-Closed

Covers: `F055`.

### I2.1 Make live Wi-Fi gate success explicit

Change `wifi_gate()` to return:

```text
decision: str
text: str
ok: bool
status: str
```

`ok` must be true only when the live command completed successfully and a
decision line was parsed.

### I2.2 Include gate success in summary pass/fail

Current valid decisions:

```text
baseline-required
no-go
go
```

`unknown` should be failure unless an explicit future offline mode is selected.

Expected behavior:

- Live `wififeas gate` returns `baseline-required`: summary PASS.
- Live `wififeas gate` cannot run or has malformed output: summary FAIL.
- Existing JSON evidence alone is not enough for PASS in normal mode.

### I2.3 Validation

```bash
python3 -m py_compile scripts/revalidation/a90_kernel_tools.py scripts/revalidation/kernel_capability_summary.py
python3 scripts/revalidation/kernel_capability_summary.py --refresh --out tmp/kernel-capability/i2-refresh.md --json-out tmp/kernel-capability/i2-refresh.json
```

Add a local fixture for failed capture if practical:

```text
simulate run_capture failure -> pass=false, exit=1, wifi_decision=unknown
```

Acceptance:

- Normal live v202-style refresh still passes when `wififeas gate` is captured.
- Missing bridge/device or malformed gate output fails the summary.

## Batch I3: Lifecycle Token Namespace Regression

Covers: `F056`.

### I3.1 Provide tcpctl_host-compatible namespace fields

The lifecycle wrapper must provide fields expected by `get_tcpctl_token()`:

```text
device_protocol
busy_retries
busy_retry_sleep
menu_hide_sleep
bridge_host
bridge_port
bridge_timeout
token_command
token_path
```

If adding parser flags is noisy, use an adapter namespace for token capture.

### I3.2 Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker_ncm_lifecycle_check.py scripts/revalidation/tcpctl_host.py
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py --dry-run --token 0123456789ABCDEF0123456789ABCDEF --run-dir tmp/a90-i3-lifecycle-dry
```

Add a targeted token-capture fixture that monkeypatches or fake-runs
`get_tcpctl_token()` and confirms the wrapper namespace has all required
attributes.

Acceptance:

- Non-dry-run no-token path no longer raises `AttributeError` before starting.
- Dry-run planned command redaction remains unchanged.

## Recommended Execution Order

1. Commit the imported `F054-F056` documents.
2. Implement Batch I1 and commit.
3. Implement Batch I2 and commit.
4. Implement Batch I3 and commit.
5. Run local targeted security checks and update statuses.

## Wi-Fi Gate

Wi-Fi read-only baseline refresh can proceed only after `F055` is fixed or the
operator separately verifies the live `wififeas gate` command. Wi-Fi active
bring-up remains blocked until baseline evidence changes and exposure policy is
reviewed again.
