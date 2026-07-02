# Native Init V3357 Self-dd F0 Source-Plan Source Build

- Cycle: `V3357`
- Decision: `v3357-self-dd-f0-plan-source-build-pass`
- Init: `A90 Linux init 0.11.120 (v3357-self-dd-f0-plan)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3357_self_dd_f0_plan.img`
- Boot SHA256: `fd379bfde2b4566e926cfec16339a6e43e1d992012401551384fa5e1584ef63e`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `boot-flash-plan <candidate-path> <expected-sha256> <expected-version>` as the read-only F0 rung after the V3355 E5 full-partition identity pass.
- The command resolves and guards the current boot partition, computes an O_DIRECT `before_full_sha`, validates a staged candidate image under approved staging roots, checks the expected SHA/version/header/size, and computes the `target_full_sha` that a later content-changing rung would write.
- F0 performs no boot-partition write and emits `would_write=0`; F1 remains blocked until F0 passes live and the policy gate for content-changing self-write is deliberately resolved.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `version` 0.11.120, a staged candidate image, and `boot-flash-plan` emitting `candidate_sha` with `expected_sha_match=1`, `version_marker_found=1`, `candidate_header=ok`, `target_full_sha=...`, `changed_chunks=...`, `would_write=0`, and `result=ok source-plan-only`, then rollback to `v2321` with `selftest fail=0`.
- This is a source-build preparation only; no live V3357 source-plan result is claimed here.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `self-dd-f0-plan-candidate`.
