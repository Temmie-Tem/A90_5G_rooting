# v323 Report: Private Property Chain Gate Audit

- date: `2026-05-19`
- scope: host-only audit of private property lookup chain gates
- boot image change: none
- baseline native build: `A90 Linux init 0.9.61 (v319)`
- result: `private-property-chain-ready-for-v320-approval`

## Summary

v323 adds `scripts/revalidation/wifi_private_property_chain_audit.py`, a
host-only audit that reads existing manifests/reports and summarizes whether the
private property lookup chain is ready for the next live step.

Initial result: all local/static prerequisites were present, but v317 live
namespace proof PASS evidence was absent. After the approved V317 live proof
passed, the audit now reports that the chain is ready for V320 approval.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_chain_audit.py
python3 scripts/revalidation/wifi_private_property_chain_audit.py \
  --out-dir tmp/wifi/v323-private-property-chain-audit \
  audit
git diff --check
```

Result:

```text
decision: private-property-chain-blocked-v317-missing
audit_pass: True
chain_ready: False
reason: all local/static prerequisites pass, but v317 live namespace proof PASS evidence is absent
device_commands_executed: False
device_mutations: False
```

Post-V317 validation:

```bash
python3 scripts/revalidation/wifi_private_property_chain_audit.py \
  --out-dir tmp/wifi/v323-private-property-chain-audit-after-v317 \
  audit
```

Observed result:

```text
decision: private-property-chain-ready-for-v320-approval
audit_pass: True
chain_ready: True
reason: all prerequisite gates pass; v320 still requires exact live approval before helper execution
device_commands_executed: False
device_mutations: False
```

## Gate Summary

| gate | status |
| --- | --- |
| v312 property layout | PASS |
| v315 live preflight | PASS |
| v316 approval packet | PASS |
| v317 plan | PASS |
| v317 audit | PASS |
| v317 live PASS | PASS |
| v319 native transfer support | PASS |
| v321 helper support | PASS |
| v322 runner integration | PASS |
| v322 current run blocked safely | PASS |

## Current Blocker

Exact V320 approval phrase is required before the next live lookup:

```text
approve v320 private property lookup proof only; no daemon start and no Wi-Fi bring-up
```

Without that phrase, private property lookup remains blocked. No daemon start,
Wi-Fi scan/connect/link-up, routing, rfkill, firmware, or property mutation is
permitted by this audit.

## Evidence

- manifest: `tmp/wifi/v323-private-property-chain-audit/manifest.json`
- summary: `tmp/wifi/v323-private-property-chain-audit/summary.md`
- post-V317 manifest: `tmp/wifi/v323-private-property-chain-audit-after-v317/manifest.json`
- post-V317 summary: `tmp/wifi/v323-private-property-chain-audit-after-v317/summary.md`

## Next Step

The chain is ready up to the V320 live boundary. The next concrete options are:

1. run V320 live lookup only after the exact V320 approval phrase; or
2. continue with another read-only Wi-Fi/kernel inventory task that does not
   require private property namespace mutation.
