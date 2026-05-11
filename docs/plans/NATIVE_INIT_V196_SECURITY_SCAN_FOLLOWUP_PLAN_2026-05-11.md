# v196 Plan: Fresh Security Scan Follow-up Workflow

## Summary

v196 adds a small host-side workflow for turning fresh Codex Cloud security scan
CSV output into a local follow-up summary. It also records a local targeted
security rescan after v193-v195 broker work.

## Scope

- Add `scripts/revalidation/security_scan_followup.py`.
- Compare a Codex Cloud CSV export against `docs/security/findings/README.md`.
- Report which fresh findings are already imported/indexed and what local status
  they currently have.
- Run local targeted security rescan and record the result as
  `docs/security/SECURITY_FRESH_SCAN_V196_2026-05-11.md`.

## Non-Goals

- Do not call the Codex Cloud UI/API directly.
- Do not modify remote finding status.
- Do not implement another code mitigation batch unless the follow-up summary
  exposes unindexed or unmitigated findings.

## Validation

```bash
python3 -m py_compile scripts/revalidation/security_scan_followup.py
python3 scripts/revalidation/security_scan_followup.py \
  --require-indexed \
  --run-dir tmp/a90-v196-security-followup
python3 scripts/revalidation/local_security_rescan.py \
  --out docs/security/SECURITY_FRESH_SCAN_V196_2026-05-11.md
```

## Acceptance

- The latest CSV findings are indexed locally.
- The follow-up summary shows zero unindexed findings.
- The local targeted security rescan has zero FAIL results.
