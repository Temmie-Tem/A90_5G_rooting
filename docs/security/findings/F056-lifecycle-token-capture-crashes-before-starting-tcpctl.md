# F056. Lifecycle token capture crashes before starting tcpctl

## Metadata

| field | value |
|---|---|
| finding_id | `c8ec2316bbf88191aa389761867c9e36` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c8ec2316bbf88191aa389761867c9e36 |
| severity | `informational` |
| status | `mitigated-host-batch-i3` |
| detected_at | `2026-05-11T21:30:58.972757Z` |
| committed_at | `2026-05-12 05:53:31 +0900` |
| commit_hash | `5f0462aa9568f20907b0dc2efd814fe783a2a448` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker_ncm_lifecycle_check.py` <br> `scripts/revalidation/tcpctl_host.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv` |

## CSV Description

In non-dry-run mode without an explicit --token, a90_broker_ncm_lifecycle_check.py now calls get_tcpctl_token(args). That helper is imported from tcpctl_host.py and expects tcpctl_host-style common arguments such as device_protocol and busy_retries. The lifecycle parser only added token_command, token_path, and bridge_timeout, so the default execution path raises AttributeError before any listener lifecycle validation can run. This is a host-side validation/availability regression rather than a direct exploitable security issue.

## Local Initial Assessment

- New host-side regression introduced by the H2 token propagation patch.
- It is related to `F051` but not a duplicate: `F051` covered listener cleanup/token propagation failure; this item covers a parser namespace mismatch before the lifecycle run starts.
- Severity is informational, but it blocks the lifecycle validator path that should prove `F051` stays mitigated.

## Local Remediation

- Implemented in Batch I3; see `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_REPORT_2026-05-12.md`.
- `a90_broker_ncm_lifecycle_check.py` now exposes the `tcpctl_host.get_tcpctl_token()` namespace fields required for token acquisition: `device_protocol`, `busy_retries`, `busy_retry_sleep`, and `menu_hide_sleep`.
- Dry-run planned command redaction remains unchanged.
- A local namespace fixture confirmed the lifecycle wrapper parser provides all token helper fields.

## Codex Cloud Detail

Lifecycle token capture crashes before starting tcpctl
Link: https://chatgpt.com/codex/cloud/security/findings/c8ec2316bbf88191aa389761867c9e36
Criticality: informational
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 5f0462a
Author: shs02140@gmail.com
Created: 2026-05-11T21:30:58.972757Z
Assignee: Unassigned
Signals: Security

# Summary
In non-dry-run mode without an explicit --token, a90_broker_ncm_lifecycle_check.py now calls get_tcpctl_token(args). That helper is imported from tcpctl_host.py and expects tcpctl_host-style common arguments such as device_protocol and busy_retries. The lifecycle parser only added token_command, token_path, and bridge_timeout, so the default execution path raises AttributeError before any listener lifecycle validation can run. This is a host-side validation/availability regression rather than a direct exploitable security issue.
