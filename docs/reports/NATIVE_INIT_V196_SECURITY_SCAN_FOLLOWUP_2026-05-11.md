# v196 Fresh Security Scan Follow-up Workflow

## Summary

v196 adds a host-side workflow to check fresh Codex Cloud CSV exports against the
local finding archive and records a local targeted security rescan after the
broker v193-v195 work. This is a host tooling/documentation change only.

## Changes

- Added `scripts/revalidation/security_scan_followup.py`.
- Added `docs/security/scans/SECURITY_FRESH_SCAN_V196_2026-05-11.md`.
- Updated the security findings index with the fresh v196 rescan reference.
- Updated broker/tooling README and task queue docs.

## Validation

```bash
python3 -m py_compile scripts/revalidation/security_scan_followup.py
```

Result: PASS.

```bash
python3 scripts/revalidation/security_scan_followup.py \
  --require-indexed \
  --run-dir tmp/a90-v196-security-followup
```

Result: PASS.

Evidence:

- `tmp/a90-v196-security-followup/security-scan-followup-summary.json`
- `tmp/a90-v196-security-followup/security-scan-followup-report.md`

Summary:

- CSV findings: 2
- Indexed locally: 2
- Unindexed: 0
- Local statuses: `mitigated-host-batch-f=2`

```bash
python3 scripts/revalidation/local_security_rescan.py \
  --out docs/security/scans/SECURITY_FRESH_SCAN_V196_2026-05-11.md
```

Result: PASS by local targeted scan.

Summary:

- PASS: 29
- WARN: 1
- FAIL: 0
- New implementation blocker: 0

## Acceptance

- Fresh F045/F046 CSV entries are imported and indexed locally.
- Current local targeted security scan has no FAIL items.
- The remaining warning is the accepted USB-local/localhost root-control boundary.

## Next

After v196, the next concrete choice is either a live v195 broker soak run or the
next network/Wi-Fi baseline cycle guarded by the security scan workflow.
