# F055. Wi-Fi gate failure does not fail capability summary

## Metadata

| field | value |
|---|---|
| finding_id | `f634a0fd39088191a848638f85af0421` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/f634a0fd39088191a848638f85af0421 |
| severity | `medium` |
| status | `mitigated-host-batch-i2` |
| detected_at | `2026-05-11T21:29:41.774522Z` |
| committed_at | `2026-05-12 04:39:48 +0900` |
| commit_hash | `4c984a72716d269354789324e5bdca141fa61cdf` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_kernel_tools.py` <br> `scripts/revalidation/kernel_capability_summary.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv` |

## CSV Description

The v202 summary is intended to merge v197-v200 evidence with a live `wififeas gate` result before guiding the next Wi-Fi/network/debug decision. However, `wifi_gate()` initializes the decision to `unknown` and only parses text; it does not propagate whether the command actually succeeded. The shared `run_capture()` helper catches connection/protocol failures and returns an empty failed capture, so a missing bridge, unavailable device, unsupported command, or malformed response becomes `wifi_decision == "unknown"`. `build_summary()` then calculates `pass_ok` only from the four JSON evidence files and their version flags, excluding the Wi-Fi gate result entirely. As a result, stale passing JSON evidence plus a failed live Wi-Fi gate still produces `PASS`, writes a manifest with `"pass": true`, and exits 0. Automation or operators relying on the script exit status can therefore treat the safety preflight as successful despite the live Wi-Fi gate being absent or unverifiable.

## Local Initial Assessment

- New issue in the v202 host-side capability summary workflow.
- Current `kernel_capability_summary.py` computes `pass_ok` from existing JSON evidence and version checks, while the live Wi-Fi gate can degrade to `unknown` without failing the summary.
- This matters because `v203` is expected to start Wi-Fi baseline work from the v202 summary gate.

## Local Remediation

- Implemented in Batch I2; see `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_REPORT_2026-05-12.md`.
- `wifi_gate()` now returns parsed decision, evidence text, capture status, and a boolean `wifi_gate_ok`.
- `kernel_capability_summary.py` now includes `wifi_gate_ok` in `pass_ok`, so missing or malformed live gate output fails the summary.
- A local fixture confirmed failed `run_capture()` produces `pass=false` and `wifi_gate_ok=false`.

## Codex Cloud Detail

Wi-Fi gate failure does not fail capability summary
Link: https://chatgpt.com/codex/cloud/security/findings/f634a0fd39088191a848638f85af0421
Criticality: medium
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 4c984a7
Author: shs02140@gmail.com
Created: 2026-05-11T21:29:41.774522Z
Assignee: Unassigned
Signals: Security

# Summary
The v202 summary is intended to merge v197-v200 evidence with a live `wififeas gate` result before guiding the next Wi-Fi/network/debug decision. However, `wifi_gate()` initializes the decision to `unknown` and only parses text; it does not propagate whether the command actually succeeded. The shared `run_capture()` helper catches connection/protocol failures and returns an empty failed capture, so a missing bridge, unavailable device, unsupported command, or malformed response becomes `wifi_decision == "unknown"`. `build_summary()` then calculates `pass_ok` only from the four JSON evidence files and their version flags, excluding the Wi-Fi gate result entirely. As a result, stale passing JSON evidence plus a failed live Wi-Fi gate still produces `PASS`, writes a manifest with `"pass": true`, and exits 0. Automation or operators relying on the script exit status can therefore treat the safety preflight as successful despite the live Wi-Fi gate being absent or unverifiable.
