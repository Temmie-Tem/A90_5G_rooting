# Security Findings Closure Review

Date: 2026-05-07
Latest verified baseline: `A90 Linux init 0.9.33 (v133)`
Source findings: `docs/security/findings/README.md`
Fix queue: `docs/security/SECURITY_FIX_QUEUE_2026-05-06.md`

## Summary

The original 31 Codex Cloud security findings have all been assigned a current
repository disposition after the security batches and follow-up releases.

Current closure split:

| disposition | count | findings |
|---|---:|---|
| Code/tooling mitigated | 29 | F001-F020, F022-F029, F031 |
| Accepted trusted-lab boundary | 2 | F021, F030 |
| Still open for implementation | 0 | - |

This means there is no known untriaged implementation blocker in the imported
finding set before the next feature cycle. The two accepted findings are not
silently dismissed: they describe the intentional USB-local rescue/control model
and should be closed only as accepted risk / trusted-lab-boundary, not as code
removed.

## Close Candidates

These findings can be closed in the external tracker as fixed/mitigated if the
tracker allows closure based on repository remediation evidence.

| id | severity | disposition | evidence |
|---|---|---|---|
| F001 | high | mitigated-v123 | `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md` |
| F002 | high | mitigated-v124 | `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md` |
| F003 | high | mitigated-v123 | `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md` |
| F004 | high | mitigated-v124 | `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md` |
| F005 | high | mitigated-v123 | `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md` |
| F006 | high | mitigated-host-batch5 | `docs/reports/NATIVE_INIT_SECURITY_BATCH5_LEGACY_TOOLING_2026-05-06.md` |
| F007 | high | mitigated-host-batch5 | `docs/reports/NATIVE_INIT_SECURITY_BATCH5_LEGACY_TOOLING_2026-05-06.md` |
| F008 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F009 | medium | mitigated-v125 | `docs/reports/NATIVE_INIT_V125_SECURITY_BATCH4_2026-05-06.md` |
| F010 | medium | mitigated-v123 | `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md` |
| F011 | medium | mitigated-v124 | `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md` |
| F012 | medium | mitigated-v124 | `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md` |
| F013 | medium | mitigated-v124 | `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md` |
| F014 | medium | mitigated-v123 | `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md` |
| F015 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F016 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F017 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F018 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F019 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F020 | medium | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F022 | low | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |
| F023 | low | mitigated-v127 | `docs/reports/NATIVE_INIT_V127_MENU_BUSY_GATE_2026-05-07.md` |
| F024 | low | mitigated-v125 | `docs/reports/NATIVE_INIT_V125_SECURITY_BATCH4_2026-05-06.md` |
| F025 | low | mitigated-v125 | `docs/reports/NATIVE_INIT_V125_SECURITY_BATCH4_2026-05-06.md` |
| F026 | informational | mitigated-v126 | `docs/reports/NATIVE_INIT_V126_SECURITY_BATCH6_RELIABILITY_2026-05-06.md` |
| F027 | informational | mitigated-v126 | `docs/reports/NATIVE_INIT_V126_SECURITY_BATCH6_RELIABILITY_2026-05-06.md` |
| F028 | informational | mitigated-v126 | `docs/reports/NATIVE_INIT_V126_SECURITY_BATCH6_RELIABILITY_2026-05-06.md` |
| F029 | informational | mitigated-v126 | `docs/reports/NATIVE_INIT_V126_SECURITY_BATCH6_RELIABILITY_2026-05-06.md` |
| F031 | informational | mitigated-host-batch3 | `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md` |

## Accepted Risk Candidates

These findings should not be marked as fixed by code removal. They should be
closed as accepted risk / intended trusted-lab boundary if the tracker supports
that state.

| id | severity | disposition | reason | guardrails |
|---|---|---|---|---|
| F021 | medium | accepted-lab-boundary | USB ACM root shell is the intentional local rescue/control channel. | Physical USB access, local operator bridge, latest docs label it trusted-lab-only. |
| F030 | informational | accepted-lab-boundary | USB ACM plus localhost serial bridge is intentionally unauthenticated for lab recovery. | Bridge defaults to localhost and serial device identity pinning; do not expose bridge on LAN/Wi-Fi. |

If future work exposes these channels beyond physical USB/local host, this
accepted-risk decision must be revisited before enabling that exposure.

## Why The Old Exposure Map Looks Stale

`docs/security/SECURITY_FINDINGS_CURRENT_EXPOSURE_2026-05-06.md` intentionally
preserves the original v122 exposure map used to choose fix order. It is useful
for historical reasoning, but it is no longer the current implementation state.
Use this closure review plus the batch reports as the current v133 disposition.

## Current Guardrail Before Wi-Fi Or Broader Networking

The imported finding set no longer has an open implementation blocker, but Wi-Fi
or broader network exposure should still follow these guardrails:

- keep netservice, tcpctl, and rshell opt-in by default;
- keep tcpctl token-required and bound to the intended NCM address;
- keep USB ACM/serial bridge local-only unless a new authentication layer exists;
- rerun `native_soak_validate.py`, `selftest verbose`, `netservice status`, and
  rshell/tcpctl smoke checks after any network policy change;
- run a new security scan after the next network-facing feature change.

## Recommended Next Action

Close/mark the external findings using the tables above, then run a fresh scan
against the v133 baseline. If the fresh scan reports new issues, start a new
security batch from the new finding set instead of reworking the closed v122-era
map.
