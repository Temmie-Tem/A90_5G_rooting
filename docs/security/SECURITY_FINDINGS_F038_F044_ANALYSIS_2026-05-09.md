# F038-F044 Security Findings Relationship and Fix Plan

Date: `2026-05-09`
Source CSV: `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv`
Scope: fresh Codex Cloud findings against the host-side stability/harness work from v160-v177.

## Summary

F038-F044 are not one unrelated batch. They cluster around the same operational
transition: moving from one-off local validation scripts toward long-running,
network-aware, server-readiness testing.

The primary risk is not a new device-side kernel bug. The primary risk is that
host validation tools can accidentally turn a lab-only root-control workflow into
unsafe automation:

- weak path validation before root-side file commands;
- raw serial command construction with untrusted strings;
- retrying non-idempotent root commands after partial transport failure;
- reports that certify network/authentication properties without checking them;
- unbounded host memory growth during `unlimited` observation;
- operational docs that bypass safety defaults.

These must be fixed before v179-v184 mixed long-soak runs become the basis for
Wi-Fi or serverization decisions.

## Finding Table

| id | severity | status | class | immediate priority |
|---|---|---|---|---|
| F038 | medium | mitigated-host-batch-a | device path confinement / destructive cleanup | P1 |
| F039 | medium | mitigated-host-batch-d | host NIC selection / unsafe operational docs | P2 |
| F040 | medium | mitigated-host-batch-b | unsafe replay of non-idempotent root commands | P1 |
| F041 | medium | mitigated-host-batch-a | raw serial command injection / path validation | P0 |
| F042 | medium | mitigated-host-batch-c | false PASS for unauthenticated tcpctl evidence | P1 |
| F043 | low | mitigated-host-batch-b | unbounded host observer memory | P1 for long-run, P2 generally |
| F044 | informational | mitigated-host-batch-c | NCM module false failure | P2 |

Priority interpretation:

- `P0`: patch before any further NCM/storage/mixed-soak automation.
- `P1`: patch before using results as stability/security evidence.
- `P2`: patch in the same cycle, but can follow the P0/P1 safety fixes.

## Relationship Groups

### G1. Host/device path and command boundary failures

Findings:

- F038: `fs_exerciser_mini.py` accepts paths that are not strictly confined to
  `/mnt/sdext/a90/test-fsx/<safe-run-id>`, then runs root-side `rm -rf`.
- F041: `storage_iotest.py` builds raw serial command lines from `run_id`,
  `test_root`, `toybox`, and device paths without rejecting newline/control
  characters or whitespace.
- F039: resume docs recommend automatic host interface selection even though the
  script's safer default requires explicit `--interface`.

Shared cause:

- String prefix checks are treated as a security boundary.
- Path components are not consistently restricted to safe single components.
- Some operations still build line-oriented commands rather than framed argv.
- Device-reported or operator-supplied values can steer privileged host/device
  side effects.

Required pattern:

```text
safe component -> normalized path -> exact prefix boundary -> no raw command text
```

For raw bridge cases that cannot use `cmdv1x`, all interpolated values must be
strictly limited to a small safe character set before command construction.

### G2. Non-idempotent command replay and long-run resource accounting

Findings:

- F040: `cpu_mem_thermal_stability.py` sets `retry_unsafe=True` and sometimes
  `attempts=2` for mutating commands such as `dd`, `rm`, `longsoak start`, and
  `/bin/a90_cpustress`.
- F043: `a90harness/observer.py` streams samples to JSONL but also keeps every
  sample in memory for the entire unlimited run.

Shared cause:

- Short-run validation assumptions leaked into long-run tooling.
- Retry and accounting policies are not separated by operation type.

Required pattern:

```text
read-only commands may retry
mutating commands are single-shot unless explicitly idempotent
long-run observers use counters/ring excerpts, not full in-memory history
```

### G3. Evidence correctness and false confidence

Findings:

- F042: `ncm_tcp_stability_report.py` claims to validate token-authenticated
  tcpctl but does not require `auth=required` in the transcript.
- F044: `ncm_tcp_preflight.py` expects a marker that `tcpctl_host.py smoke` never
  prints, so a good NCM environment can fail the wrapper.

Shared cause:

- Reports/wrappers use loose or stale text markers instead of checking the
  actual security property or real child output contract.

Required pattern:

```text
report checks must verify the security property directly
wrapper success must match the child tool's stable output contract
```

## Fix Batches

### Batch A — Block command injection and destructive path escape

Fixes:

- F041 first.
- F038 immediately after, using the same path/component helpers where possible.

Implementation details:

- Add strict safe component validation:
  - reject empty, `.`, `..`;
  - allow only `[A-Za-z0-9._-]+`;
  - reject whitespace, newline, `#`, quotes, shell metacharacters, and NUL.
- Normalize device paths with POSIX semantics.
- Require run directories to be a child of the intended test root, not the root
  itself.
- Replace prefix checks like `startswith("/mnt/sdext/a90/test-fsx")` with exact
  root or `root + "/"` boundary checks.
- For `storage_iotest.py`, validate `--test-root`, `--run-id`, `--toybox`, all
  generated paths, and transfer temp paths before they are interpolated into a
  `BridgeRunThread` raw command.
- Prefer `cmdv1x`/argv-framed commands for non-listener operations; keep raw
  bridge only where an active streaming listener requires it, and then only with
  sanitized values.

Validation:

- Unit checks for malicious `run-id` values:
  - `.`
  - `..`
  - `ok\nwritefile /cache/native-init-netservice 1\n#`
  - `test-fsx-other`
  - `a b`
  - `a#b`
- `python3 -m py_compile` for changed scripts.
- Existing smoke mode still works with normal run ids.

### Batch B — Remove unsafe replay and fix long-run observer accounting

Fixes:

- F040.
- F043.

Implementation details:

- Remove `retry_unsafe=True` from mutating `cpu_mem_thermal_stability.py`
  commands.
- Keep script-level `attempts=1` for:
  - tmpfs `dd`;
  - tmpfs cleanup `rm`;
  - `longsoak start`;
  - `/bin/a90_cpustress`;
  - any `run ...` command with side effects.
- Allow retries only for known read-only observations such as `status`,
  `selftest verbose`, `longsoak status verbose`, and possibly host-side ping.
- In `run_observer()`, replace `all_samples` with streaming counters:
  - `samples_count`;
  - `failures_count`;
  - last N failure excerpts if needed;
  - no full in-memory sample list for unlimited runs.
- Keep `observer.jsonl` as the complete evidence source.

Validation:

- Confirm no mutating CPU/memory validator call uses `retry_unsafe=True`.
- `observe --duration-sec unlimited --max-cycles 2` remains PASS.
- A bounded observer run writes the same JSONL/schema-level summary.

### Batch C — Make NCM/TCP evidence security-aware and wrapper-correct

Fixes:

- F042.
- F044.

Implementation details:

- Update `ncm_tcp_stability_report.py` to require:
  - `auth=required` in the tcpctl serial/listener transcript;
  - absence of `auth=none`;
  - `OK authenticated` or authenticated command flow evidence when present.
- Add a negative test fixture or self-check where a `--no-auth` transcript must
  fail.
- Update `ncm_tcp_preflight.py` to match actual `tcpctl_host.py smoke` output:
  - require `--- ping ---`;
  - require `--- version ---`;
  - require `--- status ---`;
  - require `--- shutdown ---`;
  - require `[done] run`;
  - do not require non-existent `--- tcpctl-checks ---`.

Validation:

- `tcpctl_host.py smoke` wrapper accepts real smoke success output.
- Reporter rejects no-auth transcript even if ping/status/run counts pass.

### Batch D — Correct unsafe NCM resume instructions

Fix:

- F039.

Implementation details:

- Update `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md`
  to require explicit interface pinning:

```text
python3 scripts/revalidation/ncm_host_setup.py setup --interface <known-usb-ncm-ifname>
```

- Keep `--allow-auto-interface` documented only as a diagnostic fallback, not as
  the recommended resume path.
- Avoid committing real host interface identifiers or IP evidence in new reports
  unless needed for debugging and intentionally redacted.
- Optionally add a stronger warning in `ncm_host_setup.py --help`.

Validation:

- `rg "--allow-auto-interface" docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md`
  no longer finds the recommended resume command.

## Recommended Execution Order

1. Commit the imported F038-F044 finding documentation and v178-v184 roadmap if
   not already committed.
2. Patch Batch A in one security-focused commit.
3. Patch Batch B in one commit.
4. Patch Batch C and D in one commit, or split C and D if the report updates are
   easier to review separately.
5. Run local targeted security checks and add F038-F044 coverage.
6. Only then resume v178/v179 mixed-soak implementation.

## Wi-Fi / Serverization Impact

These findings reinforce the decision to delay Wi-Fi baseline refresh until after
the mixed-soak gate.

Before Wi-Fi or broader server-style operation:

- host validators must not be able to inject root serial commands through path
  arguments;
- reports must not certify unauthenticated network control as PASS;
- long-run observers must not fail from predictable host memory growth;
- operator docs must not steer privileged host network commands toward
  automatically selected interfaces.

This means F038-F044 should be treated as blockers for using v160-v177 evidence
as a Wi-Fi/serverization readiness basis, even if some individual findings are
only low or informational severity.
