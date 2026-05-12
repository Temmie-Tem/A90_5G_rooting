# F054-F056 Security Findings Relationship Analysis

Date: 2026-05-12

Source:

- CSV: `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv`
- Split index: `docs/security/findings/README.md`
- Analysis: `docs/security/SECURITY_FINDINGS_F054_F056_ANALYSIS_2026-05-12.md`
- Patch plan: `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_PLAN_2026-05-12.md`
- Patch report: `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_REPORT_2026-05-12.md`

## Summary

`F054` through `F056` are not a new large vulnerability family. They are
follow-up gaps around the post-H1/H2 broker and pre-Wi-Fi decision workflow:

1. `F054` shows the broker now has command-class authorization, but not enough
   resource/argument-aware authorization for observe commands.
2. `F055` shows the Wi-Fi preflight summary can fail open if the live gate is
   missing.
3. `F056` shows the NCM lifecycle validator still has host-tool namespace drift
   after the token propagation fix.

The most important relationship is this:

```text
F054 token disclosure
  -> tcpctl token obtained by an observe-only broker client
  -> direct authenticated tcpctl connection
  -> absolute-path root run path
```

Therefore `F054` had to be fixed before any wider broker/NCM/Wi-Fi exposure.
`F055` had to be fixed before treating `v202` as a reliable Wi-Fi go/no-go
summary. Both are now patched in Batch I1/I2.

## Relationship Groups

| group | theme | findings | primary risk |
|---|---|---|---|
| R1 | Broker observe read boundary | `F054` | observe-only client can read a secret token through unrestricted root `cat` |
| R2 | Safety preflight fail-open | `F055` | Wi-Fi decision summary can pass even when live gate is absent/unverified |
| R3 | Host validator namespace drift | `F056` | lifecycle validation can crash before proving tcpctl start/stop cleanup |

## R1: Broker Observe Read Boundary

### Related findings

- `F054` is the direct issue: `cat` is still classified as observe-only in
  `scripts/revalidation/a90_broker.py`.
- `F048` is the parent authorization theme: broker command classes must be
  enforced before backend dispatch.
- `F047` and `F052` are adjacent tcpctl token/protocol issues that show why
  token exposure is high impact.
- `F005` is the older root command sink: once tcpctl is authenticated, its
  `run` operation reaches root command execution.

### Relationship

H1 fixed command-class authorization, but `F054` shows that class-level policy is
insufficient when an observe command has unbounded arguments.

Attack chain:

```text
same-user/local broker client
  -> broker default observe-only policy
  -> cat /cache/native-init-tcpctl.token
  -> token returned as command output
  -> client connects to NCM tcpctl directly
  -> auth <token>
  -> run <absolute-path>
  -> native-init root exec path
```

This is both:

- sensitive information exposure, because a secret token is returned to an
  observer; and
- authorization bypass, because the leaked token can unlock a different control
  channel.

### Fix direction

The policy must be resource-aware, not just command-name-aware.

Recommended baseline:

- treat unrestricted `cat` as `operator-action`, not observe;
- keep structured observe commands such as `status`, `bootstatus`, `timeline`,
  `logpath`, and `selftest`;
- add a sensitive path denylist for tcpctl token/runtime secret paths;
- later, if needed, add a narrow allowlist for safe read-only paths.

## R2: Wi-Fi Safety Preflight Fail-Open

### Related findings

- `F055` is the direct issue: `kernel_capability_summary.py` can report PASS
  while `wififeas gate` failed or could not be parsed.
- It relates to `v202 Kernel Capability Summary View`, which is intended to be
  the preflight summary before the next Wi-Fi baseline refresh.
- It also relates to `F054`, because any Wi-Fi/NCM exposure decision should only
  happen after broker/token boundaries are known-good.

### Relationship

The current summary combines static JSON evidence with a live gate. If the live
gate fails, the decision becomes `unknown`, but that is not included in the
summary pass/fail calculation.

Failure chain:

```text
bridge down or malformed wififeas output
  -> run_capture() returns failed/empty capture
  -> wifi_decision = unknown
  -> stale v197-v200 JSON evidence still passes
  -> kernel_capability_summary exits 0
  -> operator/automation may treat Wi-Fi preflight as safe
```

This is a process-control bug rather than direct root execution. It matters
because Wi-Fi work changes reachability and should not be driven by stale or
unverified evidence.

### Fix direction

The Wi-Fi gate should be mandatory in normal mode.

Recommended baseline:

- `wifi_gate()` returns `decision`, `text`, and `ok`;
- accepted successful decisions are `baseline-required`, `no-go`, and `go`;
- `unknown`, missing command output, failed capture, or malformed output fail
  the summary;
- if offline reporting is needed later, make it explicit and label it as stale
  evidence.

## R3: Host Validator Namespace Drift

### Related findings

- `F056` is the direct issue: `a90_broker_ncm_lifecycle_check.py` calls
  `tcpctl_host.get_tcpctl_token(args)` with an argparse namespace that does not
  provide all tcpctl-host fields.
- It relates to `F051`, which H2 mitigated by sharing a token across
  lifecycle start/smoke/stop commands.

### Relationship

The H2 direction was correct, but the wrapper now shares a helper function whose
input contract is larger than the lifecycle parser provides.

Failure chain:

```text
lifecycle wrapper non-dry-run and no explicit --token
  -> calls get_tcpctl_token(args)
  -> args.device_protocol or args.busy_retries missing
  -> AttributeError before listener lifecycle starts
  -> no evidence that start/smoke/stop cleanup path works
```

This does not expose a new command-execution path. It weakens the validation
tooling that is supposed to prove NCM/tcpctl lifecycle safety.

### Fix direction

Make helper contracts explicit.

Recommended baseline:

- either add all `tcpctl_host` common fields to the lifecycle parser, or
  construct a small compatibility namespace before calling `get_tcpctl_token()`;
- add a targeted fixture for no-token non-dry-run token capture;
- keep dry-run redaction and planned-command output unchanged.

## Cross-Generation Mapping

| new finding | closest prior theme | relation |
|---|---|---|
| `F054` | `F048`, `F047`, `F052`, older `F005` | follows H1; class authorization is fixed, but observe arguments still leak secrets |
| `F055` | v202 kernel capability summary, Wi-Fi gate docs | follows v202; summary needs fail-closed live gate semantics |
| `F056` | `F051` / H2 lifecycle cleanup | follows H2; token propagation exists but wrapper namespace is incomplete |

## Dependency Order

Recommended order:

```text
I1 / F054 broker observe read boundary
  -> I2 / F055 Wi-Fi summary fail-closed
  -> I3 / F056 lifecycle namespace regression
  -> v203 Wi-Fi read-only baseline refresh
```

Rationale:

- `F054` is high impact and can turn observe access into authenticated tcpctl
  access.
- `F055` directly affects whether Wi-Fi preflight evidence is trustworthy.
- `F056` is lower severity but should be fixed before more NCM lifecycle soak
  validation.

## Reference Notes

- MITRE CWE-200 covers exposure of sensitive information to an unauthorized
  actor. `F054` fits this as a direct token disclosure path, and the disclosed
  token can become an authorization bypass in tcpctl.
  - https://cwe.mitre.org/data/definitions/200.html
- MITRE CWE-862 covers missing authorization. `F054` also fits this angle
  because a broker client authorized only for observe behavior can access a
  secret resource through unrestricted `cat`.
  - https://cwe.mitre.org/data/definitions/862.html

## Conclusion

Wi-Fi active work still should not proceed from this state. The safe path is:

1. Keep the `F054` broker observe read boundary verified.
2. Keep the `F055` Wi-Fi gate fail-closed summary verified.
3. Keep `F056` lifecycle token namespace regression covered before further lifecycle soak evidence.
4. Then resume `v203` as read-only Wi-Fi baseline refresh, not Wi-Fi bring-up.
