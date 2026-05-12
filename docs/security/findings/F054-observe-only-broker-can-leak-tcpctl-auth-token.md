# F054. Observe-only broker can leak tcpctl auth token

## Metadata

| field | value |
|---|---|
| finding_id | `7e29d366e9c88191858b21e4613abe7f` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/7e29d366e9c88191858b21e4613abe7f |
| severity | `high` |
| status | `mitigated-host-batch-i1` |
| detected_at | `2026-05-11T21:31:14.823973Z` |
| committed_at | `2026-05-12 05:50:19 +0900` |
| commit_hash | `fc300f7cce5ec46abcd0aef5bc840de02f498e40` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker.py` <br> `stage3/linux_init/init_v73.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv` |

## CSV Description

This commit adds a broker authorization boundary where default policy permits only `observe` commands. However, `cat` remains classified as an observe command without path restrictions. The native init implementation of `cat` opens and returns any requested file path as root. Since the tcpctl token path is known (`/cache/native-init-tcpctl.token`), an observer-only broker client can request `cat /cache/native-init-tcpctl.token`, obtain the tcpctl authentication token, and then connect to the device tcpctl service directly to authenticate and run absolute-path commands as root. Even without the tcpctl escalation step, the policy allows arbitrary root file reads through a mode documented as observe-only.

## Local Initial Assessment

- New issue, not a duplicate of `F048`. `F048` covered mutating/exclusive command authorization; this issue covers sensitive read access through commands still classified as observe-only.
- Current `scripts/revalidation/a90_broker.py` includes `cat` in `OBSERVE_COMMANDS`.
- Native init `cat` opens arbitrary requested paths as root, so known token/log/helper paths are not safe to expose through an observer-only broker policy.

## Local Remediation

- Implemented in Batch I1; see `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_REPORT_2026-05-12.md`.
- `cat` is no longer a default observe-only broker command; it is classified as `operator-action`.
- Broker policy now blocks `cat /cache/native-init-tcpctl.token` and runtime secret prefixes with `sensitive-path-denied`, even when broader operator/exclusive flags are enabled.
- Broker selftest and auth hardening checks now cover sensitive token path reads.

## Codex Cloud Detail

Observe-only broker can leak tcpctl auth token
Link: https://chatgpt.com/codex/cloud/security/findings/7e29d366e9c88191858b21e4613abe7f
Criticality: high
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: fc300f7
Author: shs02140@gmail.com
Created: 2026-05-11T21:31:14.823973Z
Assignee: Unassigned
Signals: Security

# Summary
This commit adds a broker authorization boundary where default policy permits only `observe` commands. However, `cat` remains classified as an observe command without path restrictions. The native init implementation of `cat` opens and returns any requested file path as root. Since the tcpctl token path is known (`/cache/native-init-tcpctl.token`), an observer-only broker client can request `cat /cache/native-init-tcpctl.token`, obtain the tcpctl authentication token, and then connect to the device tcpctl service directly to authenticate and run absolute-path commands as root. Even without the tcpctl escalation step, the policy allows arbitrary root file reads through a mode documented as observe-only.
