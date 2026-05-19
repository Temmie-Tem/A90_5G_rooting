# v320 Private Property Lookup Proof Report

- date: `2026-05-19`
- scope: fail-closed host runner for conditional private property lookup proof
- boot image change: none
- baseline native build: `A90 Linux init 0.9.61 (v319)`
- plan: `docs/plans/NATIVE_INIT_V320_PRIVATE_PROPERTY_LOOKUP_PROOF_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_private_property_lookup_proof.py`

## Summary

Result: PASS for the current safe implementation stage.

v320 adds a host-side runner skeleton for the next private property lookup proof.
Before V317 live proof, the runner correctly refused `plan`/`run` as
`private-property-lookup-blocked-v317-missing`. After the approved V317 live
proof passed, the runner now produces a V320 plan and remains blocked only by
the separate V320 exact approval phrase for live lookup.

## Evidence

| item | path | result |
| --- | --- | --- |
| plan/refusal | `tmp/wifi/v320-private-property-lookup-proof-plan/` | `private-property-lookup-blocked-v317-missing` |
| run/refusal | `tmp/wifi/v320-private-property-lookup-proof-refuse/` | `private-property-lookup-blocked-v317-missing` |
| cleanup/no-op | `tmp/wifi/v320-private-property-lookup-proof-cleanup/` | `private-property-lookup-cleanup-not-needed` |
| plan after V317 | `tmp/wifi/v320-private-property-lookup-proof-plan-after-v317/` | `private-property-lookup-plan-ready` |

## Selected Lookup Keys

The runner derives candidate lookup keys from the v312 property layout manifest:

| key | expected | context | type |
| --- | --- | --- | --- |
| `ro.build.version.sdk` | `31` | `u:object_r:build_prop:s0` | `int` |
| `ro.product.name` | `r3qks` | `u:object_r:build_prop:s0` | `string` |
| `ro.hardware` | `qcom` | `u:object_r:bootloader_prop:s0` | `string` |
| `ro.vendor.build.version.sdk` | `30` | `u:object_r:build_vendor_prop:s0` | `int` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_lookup_proof.py
python3 scripts/revalidation/wifi_private_property_lookup_proof.py \
  --out-dir tmp/wifi/v320-private-property-lookup-proof-plan \
  plan || true
python3 scripts/revalidation/wifi_private_property_lookup_proof.py \
  --out-dir tmp/wifi/v320-private-property-lookup-proof-refuse \
  run || true
python3 scripts/revalidation/wifi_private_property_lookup_proof.py \
  --out-dir tmp/wifi/v320-private-property-lookup-proof-cleanup \
  cleanup
git diff --check
```

Result: PASS.

Post-V317 plan validation:

```bash
python3 scripts/revalidation/wifi_private_property_lookup_proof.py \
  --out-dir tmp/wifi/v320-private-property-lookup-proof-plan-after-v317 \
  plan
```

Observed output:

```text
decision: private-property-lookup-plan-ready
pass: True
reason: all prerequisites are present; live run still requires approval and helper implementation
device_commands_executed: false
device_mutations: false
```

## Guardrails Verified

- `device_commands_executed=false`.
- `device_mutations=false`.
- v312 property layout is present and parsed.
- v319 report is present.
- Pre-V317 state blocked because V317 live proof evidence was missing.
- Post-V317 state detects `private-property-namespace-proof-pass`.
- V320 plan records four read-only property lookup commands.
- Required V320 approval phrase is recorded but not accepted implicitly.

## Required Future Approval Phrase

```text
approve v320 private property lookup proof only; no daemon start and no Wi-Fi bring-up
```

This phrase is now the next live blocker after V317 PASS. It is separate from
the V317 approval and still does not approve daemon start or Wi-Fi bring-up.

## Decision

- historical decision: `private-property-lookup-blocked-v317-missing`
- post-V317 decision: `private-property-lookup-plan-ready`
- current status: V320 plan ready, live lookup approval-gated
- next step: review V320 plan and provide the exact V320 phrase only if proceeding.
