# S22+ Ramoops DTBO + M18 Capture Policy Activation (2026-07-08)

## Scope

Operator approved the attended live `S22+ ramoops DTBO + M18 capture` run after
reviewing the non-boot DTBO write risk and the patched-DTBO AVB
hash-descriptor caveat under the already-observed disabled-vbmeta/orange state.

This activation only authorizes the existing guarded helper:

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m18_capture_live_gate.py`

Live token:

`S22PLUS-RAMOOPS-DTBO-M18-CAPTURE-LIVE-GATE`

## Activation

`AGENTS.md` now contains the narrow S22+ ramoops DTBO + M18 capture exception
with the helper's required authorization markers:

- patched DTBO AP SHA256:
  `4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00`
- stock DTBO rollback AP SHA256:
  `6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa`
- patched raw DTBO SHA256:
  `1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab`
- stock raw DTBO SHA256:
  `97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c`
- M18 candidate AP SHA256:
  `9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805`
- M18 padded boot SHA256:
  `a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083`
- Magisk boot rollback AP SHA256:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`

The activation also corrected the inert draft copy block to use the full
64-character stock raw DTBO SHA256. The marker checklist and build report
already had the correct value.

## Guardrails

The exception does not authorize recovery, vendor_boot, vbmeta, vbmeta_system,
BL, CP, CSC, super, userdata, persist, EFS, sec_efs, RPMB, keymaster, modem,
bootloader, raw host `dd`, fastboot, Magisk modules, multidisabler, format
data, additional boot candidates, additional DTBO candidates, kernel rebuilds,
or any A90 action.

Next required step before live: rerun the adjusted readiness audit, default
dry-run gate, and Android baseline preflight.
