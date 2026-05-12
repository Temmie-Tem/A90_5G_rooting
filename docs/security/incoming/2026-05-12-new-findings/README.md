# 2026-05-12 New Security Findings Intake

Purpose: paste only newly reported Codex security findings here before
triage. After paste, compare each item against `docs/security/findings/F001` to
`F053` and split only non-duplicates into canonical `F054+` finding files.

## Files

- `RAW_NEW_FINDINGS.md`: paste the new finding details here.
- `DUPLICATE_NOTES.md`: record findings that overlap existing issues.

## Triage Rules

- If the title/root cause matches an existing `F0xx` finding and the current
  code is already mitigated, mark it as duplicate evidence instead of creating
  a new canonical finding.
- If the affected current code path is new or still reachable, create a new
  `F054+` file under `docs/security/findings/`.
- Preserve original links, severity, status, metadata, evidence, and validation
  text in the canonical finding file.
