# Native Init V258 CNSS Live Evidence Analyzer Plan

## Summary

- V258 adds a host-side, no-start analyzer for the V257 CNSS start-only live evidence.
- It does not execute device commands and does not start `cnss-daemon`.
- Goal: convert the large `cnss-start-only-run.txt` transcript into a small manifest that classifies lifecycle, identity/capability, namespace, mapped libraries, stderr noise, and next blockers.

## Inputs

- Primary run directory: `tmp/wifi/v257-cnss-live-start-only-run/`
- Primary transcript: `commands/cnss-start-only-run.txt`
- Runner manifest: `manifest.json`
- Optional postflight files:
  - `tmp/wifi/v257-live-post-pidof.txt`
  - `tmp/wifi/v257-live-post-proc-net-dev.txt`
  - `tmp/wifi/v257-live-post-status.txt`
  - `tmp/wifi/v257-live-post-wifiinv-full.txt`

## Implementation

- Add `scripts/revalidation/wifi_cnss_live_evidence_analyzer.py`.
- Use `a90harness.evidence.EvidenceStore` for private output handling.
- Parse:
  - top-level helper key/value lines
  - `cnss_start.*` lifecycle fields
  - `cnss_child.*` pre-exec fields
  - `cnss.identity.before/after.*` identity/capability fields
  - `A90_EXECNS_STDERR_BEGIN/END`
  - `A90_EXECNS_CNSS_PROC_status_BEGIN/END`
  - `A90_EXECNS_CNSS_PROC_maps_BEGIN/END`
- Output:
  - `manifest.json`
  - `summary.md`
  - normalized `cnss-keyvals.json`

## Classification Rules

- `start_lifecycle`: PASS only when runner decision is `start-only-pass`, `cnss_start.result=start-only-pass`, `postflight_safe=1`, and `reaped=1`.
- `identity`: PASS when effective uid/gid are `1000`, groups include `1010,3003,3005`, and net-admin capability is present.
- `namespace`: PASS when helper status is `namespace-ready` and required context paths exist.
- `cleanup`: PASS when postflight pidof is absent and no `wlan*` appears in postflight netdev/wifiinv evidence.
- `runtime_warnings`: WARN for `Failed to become a perfd client`, `/dev/kmsg` write denial, or shell quote noise.
- The final decision must remain conservative: analyzer PASS means start-only evidence is classified, not Wi-Fi scan/connect readiness.

## Validation

- Static:
  - `python3 -m py_compile scripts/revalidation/wifi_cnss_live_evidence_analyzer.py`
  - `git diff --check`
- Functional:
  - run analyzer against V257 evidence
  - confirm manifest decision is `cnss-start-only-evidence-classified`
  - confirm `start_lifecycle`, `identity`, `namespace`, and `cleanup` are PASS
  - confirm runtime warnings are captured, not treated as blockers

## Acceptance

- V257 evidence is reduced to a stable, reviewable manifest.
- No daemon execution occurs.
- The next candidate is based on classified evidence rather than manual transcript reading.
