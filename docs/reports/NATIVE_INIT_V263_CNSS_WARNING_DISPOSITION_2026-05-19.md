# Native Init v263 CNSS Warning Disposition Report

## Summary

- status: PASS
- decision: `cnss-warning-disposition-ready`
- baseline live evidence: `tmp/wifi/v261-cnss-live-evidence-analysis-final-20260519-085902/manifest.json`
- approved retry evidence: `tmp/wifi/v263-cnss-live-retry-20260519-091608/`
- boot image change: none
- daemon start: not executed by the disposition tool; one separate bounded retry
  was executed after explicit user approval
- Wi-Fi scan/connect/link-up: not executed
- host tool: `scripts/revalidation/wifi_cnss_warning_disposition.py`
- plan: `docs/plans/NATIVE_INIT_V263_CNSS_WARNING_DISPOSITION_PLAN_2026-05-19.md`
- output: `tmp/wifi/v263-cnss-warning-disposition/`
- post-audit: `tmp/wifi/v263-cnss-zombie-audit-post-warning-disposition/`

v263 converts the recurring CNSS start-only warnings into explicit dispositions.
The disposition tool itself is read-only. After the user explicitly approved a
new live retry, the same bounded start-only path was re-run and postflight
analysis remained clean.

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_cnss_warning_disposition.py \
  scripts/revalidation/wifi_cnss_warning_surface_probe.py \
  scripts/revalidation/wifi_cnss_live_evidence_analyzer.py
git diff --check
```

Read-only disposition run:

```bash
python3 scripts/revalidation/wifi_cnss_warning_disposition.py \
  --analysis-manifest tmp/wifi/v261-cnss-live-evidence-analysis-final-20260519-085902/manifest.json \
  --out-dir tmp/wifi/v263-cnss-warning-disposition
```

Result:

```text
decision: cnss-warning-disposition-ready
pass: True
reason: known CNSS warnings are classified for start-only without daemon execution
disposition: perfd-client-unavailable accepted-for-start-only android-runtime-service-gap
disposition: kmsg-write-denied accepted-for-start-only private-namespace-logging-gap
disposition: shell-quote-noise coalesced logging-path-stderr-noise
```

Post CNSS process audit:

```bash
python3 scripts/revalidation/wifi_cnss_zombie_audit.py \
  --out-dir tmp/wifi/v263-cnss-zombie-audit-post-warning-disposition
```

Result:

```text
decision: cnss-process-clean
pass: True
reason: no CNSS target processes found
```

Approved bounded live retry:

```bash
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/preflight \
  --expect-version "A90 Linux init 0.9.60 (v261)" \
  --max-runtime-sec 10 \
  preflight

python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/run \
  --expect-version "A90 Linux init 0.9.60 (v261)" \
  --max-runtime-sec 10 \
  run --allow-daemon-start --assume-yes --i-understand-reboot-only-recovery
```

Result:

```text
preflight: decision=preflight-ready pass=True
run: decision=start-only-pass pass=True
```

Retry postflight:

```bash
python3 scripts/revalidation/wifi_cnss_zombie_audit.py \
  --out-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/zombie-audit-post

python3 scripts/revalidation/wifi_cnss_live_evidence_analyzer.py \
  --run-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/run \
  --out-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/live-evidence-analysis \
  --post-processes tmp/wifi/v263-cnss-live-retry-20260519-091608/run/commands/post-cnss-processes.txt \
  --post-netdev tmp/wifi/v263-cnss-live-retry-20260519-091608/run/commands/cat-proc-net-dev.txt \
  --post-status tmp/wifi/v263-cnss-live-retry-20260519-091608/run/commands/status.txt \
  --post-wifiinv tmp/wifi/v263-cnss-live-retry-20260519-091608/run/commands/wifiinv-full.txt

python3 scripts/revalidation/wifi_cnss_warning_disposition.py \
  --analysis-manifest tmp/wifi/v263-cnss-live-retry-20260519-091608/live-evidence-analysis/manifest.json \
  --out-dir tmp/wifi/v263-cnss-live-retry-20260519-091608/warning-disposition
```

Result:

```text
zombie-audit: decision=cnss-process-clean pass=True
analysis: decision=cnss-start-only-evidence-classified pass=True
warning-disposition: decision=cnss-warning-disposition-ready pass=True
```

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| analysis-pass | PASS | `cnss-start-only-evidence-classified`, `pass=True` |
| surface-pass | PASS | `cnss-warning-surface-classified`, `pass=True` |
| expected-warning-codes | PASS | `perfd-client-unavailable`, `kmsg-write-denied`, `shell-quote-noise` |
| no-blocking-disposition | PASS | no manual-review warning remained |
| approved-live-retry | PASS | `start-only-pass`, postflight CNSS process clean |

## Dispositions

| Warning | Status | Classification | Action |
| --- | --- | --- | --- |
| `perfd-client-unavailable` | accepted for start-only | Android runtime service gap | Do not block start-only; before broader Wi-Fi, design opt-in private perfd/property shim or prove CNSS does not require it beyond warning. |
| `kmsg-write-denied` | accepted for start-only | private namespace logging gap | Do not silently create or relax `/dev/kmsg`; any kmsg-null/log-sink mode must be opt-in and validated separately. |
| `shell-quote-noise` | coalesced | logging-path stderr noise | Track with kmsg logging-path warning unless later evidence proves helper-generated shell syntax. |

## Interpretation

- These warnings do not invalidate the v261 start-only pass.
- They also did not invalidate the separate v263 user-approved bounded retry.
- They remain relevant before broader Wi-Fi behavior because Android normally
  provides logging/property/performance runtime services around vendor daemons.
- The project should not silently add fake `/dev/kmsg`, property service, or
  perfd behavior to the private namespace; those are separate opt-in shims.
- With v262 and v263 complete, the next safe step is a no-transmit QRTR/QMI
  userspace nameservice model or a plan for opt-in perfd/kmsg shim experiments.

## References

- <https://android.googlesource.com/platform/system/core/+/pie-dev/logwrapper/logwrapper.c>
- <https://chromium.googlesource.com/aosp/platform/system/core/libcutils/+/refs/heads/stabilize-15964.9.B/klog.cpp>
- <https://chromium.googlesource.com/aosp/platform/system/core/+/refs/heads/master/init/>

## Guardrails Preserved

- no `cnss-daemon` execution
- no `cnss_diag`
- no property/perfd/kmsg mutation
- no QRTR/QMI request transmission
- no rfkill unblock, `wlan*` link-up, scan/connect, credentials, DHCP, or routing
- no ICNSS bind/unbind, firmware mutation, Android partition write, or reboot

## Next Step

v264 should be one of:

1. QRTR/QMI userspace nameservice model with all packet transmission still behind
   explicit approval.
2. Opt-in kmsg/perfd shim design document without execution.
3. Android property/runtime shim feasibility model, also without live daemon
   expansion.
