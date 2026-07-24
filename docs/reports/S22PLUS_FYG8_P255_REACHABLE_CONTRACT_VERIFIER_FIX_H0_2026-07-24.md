# S22+ FYG8 P2.55 reachable-contract verifier fix H0

Date: 2026-07-24 KST
Tier: H0 host-only
Status: `PASS_P255_REACHABLE_CONTRACT_VERIFIER_FIX_HOST_ONLY`
Device contact: none
Live authority: none

## Result

The first P2.54 ready-manifest validation stopped host-only before connected
D0. The exact candidate static result contains the P2.52/P2.54
`classifier_detail_count` field, while
`device_action_f1_evidence_v2.py` still required the older fixed
reachable-record key set.

The verifier now obtains the expected reachable-record dict from the selected
versioned source contract's `validate_reachable_records()` method. It requires
exact keys, exact top-level types, and exact values. Missing fields, additional
fields, integer/boolean aliases, and changed values remain fail-closed.

The historical no-source-contract path retains its prior explicit eight-field
shape. No manifest schema, observation policy, candidate acceptance, rollback,
transport, recovery, or device behavior changed.

## Host catches

Two earlier manifest-construction attempts were also rejected before bundle
validation:

1. `target_profile` must use the canonical repository-relative path; and
2. the rollback identity object must exactly match the target profile before
   its path is resolved.

Both were data-only corrections in private storage. They created no journal,
binding, approval, device contact, or one-shot consumption.

## Validation

- Python compilation passes.
- Seven focused P2.54 source-contract tests pass, including exact
  `classifier_detail_count`, missing/value/type mutations, and the historical
  no-source-contract shape.
- The 58-test P2.34 Process v2 plus reusable live-adapter regression set passes.
- Earlier P2.45/P2.48/P2.52 source-contract regressions passed; their only
  initial failures were two expected-message mismatches, and the affected
  tests passed after preserving the existing bound-error prefix.
- The exact private P2.54 ready manifest returns
  `PASS_DEVICE_ACTION_F1_LIVE_V2_HOST_READY`.
- Plan rendering retains D0-only preparation, fresh exact F1 approval, and
  preapproved rollback semantics.
- Independent read-only execution-critical review returned GO.

## Artifact and safety impact

Only the host typed-evidence verifier and its tests changed. The P2.54 kernel,
userspace, `boot.img`, `boot.img.lz4`, candidate AP, rollback AP, source
contract, and candidate run ID are unchanged. No candidate rebuild is needed.

```text
host_only=true
device_contact=false
device_write=false
odin_invoked=false
candidate_rebuilt=false
f1_authorized=false
live_authorized=false
```

## Next

Run one fresh connected read-only D0 preparation against the exact P2.54
manifest. A passing preparation may create one private approval binding. It
does not authorize candidate transfer; the new boot-only flash still requires
the exact fresh approval emitted by that binding.
