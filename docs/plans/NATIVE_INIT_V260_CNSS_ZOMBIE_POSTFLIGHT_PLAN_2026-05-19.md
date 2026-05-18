# Native Init V260 CNSS Zombie Postflight Plan

## Summary

- V260 changes the next step from QRTR/QMI probing to CNSS postflight hardening.
- Reason: a later read-only process audit found `cnss-daemon` PID `5900` still present as a PID1-adopted zombie even though `pidof cnss-daemon` returned rc=1.
- Scope is read-only host tooling and evidence classification. No daemon start, scan, connect, link-up, credential, DHCP, routing, rfkill, or ICNSS bind/unbind is authorized.

## Problem

The V257 live retry relied on:

- helper-side `reaped=1`
- helper-side `postflight_safe=1`
- host `pidof cnss-daemon` rc=1
- no `wlan*` in `/proc/net/dev`

That was insufficient because `pidof` does not report zombie processes. A process table check showed:

```text
5900 Zs [cnss-daemon]
```

and `/proc/5900/status` showed:

```text
Name: cnss-daemon
State: Z (zombie)
PPid: 1
```

This means the current live-start gate must treat target-process zombie residue as a cleanup blocker before any further live CNSS retry.

## Implementation

- Add `scripts/revalidation/wifi_cnss_zombie_audit.py`.
  - Runs `run /cache/bin/toybox ps -A -o pid,stat,comm`.
  - Parses target processes `cnss-daemon` and `cnss_diag`.
  - Captures `/proc/<pid>/status` for any target process.
  - Classifies:
    - `cnss-process-clean`
    - `cnss-zombie-present`
    - `cnss-process-still-running`
    - `cnss-process-audit-incomplete`
- Update `scripts/revalidation/wifi_cnss_start_only_runner.py`.
  - Adds CNSS process audit to preflight.
  - Blocks live start if a CNSS target zombie or live process is present before the run.
  - Adds a post-run CNSS process audit and folds it into `postflight_safe`.
- Update `scripts/revalidation/wifi_cnss_live_evidence_analyzer.py`.
  - Accepts optional post-process evidence.
  - Marks evidence incomplete if post-process evidence shows CNSS target zombie/running residue.

## Validation

- Static:
  - `python3 -m py_compile scripts/revalidation/wifi_cnss_zombie_audit.py scripts/revalidation/wifi_cnss_start_only_runner.py scripts/revalidation/wifi_cnss_live_evidence_analyzer.py`
  - `git diff --check`
- Device read-only:
  - `python3 scripts/revalidation/wifi_cnss_zombie_audit.py --out-dir tmp/wifi/v260-cnss-zombie-audit`
  - `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v260-runner-preflight-with-zombie preflight`
  - `python3 scripts/revalidation/wifi_cnss_live_evidence_analyzer.py --out-dir tmp/wifi/v260-cnss-live-evidence-reclass-with-process-audit --post-processes tmp/wifi/v260-ps-o-pid-stat-comm.txt`

## Acceptance

- New audit must detect the current PID1-adopted CNSS zombie.
- Runner preflight must block another live start while target zombie residue exists.
- Analyzer must reclassify the V257 evidence as incomplete when post-process evidence is supplied.
- QRTR/QMI probing remains deferred until the CNSS process table is clean or the blocker is explicitly accepted and documented.
