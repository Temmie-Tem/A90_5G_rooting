# S22+ FYG8 P2.19 same-ring implementation host pass

Date: 2026-07-22 KST
Tier: H0, host-only implementation and static validation
Status: `PASS_P219_SAME_RING_IMPLEMENTATION_HOST_ONLY`
Live authority: none

## Result

P2.19 implements the bounded P2.18 discriminator without changing Odin,
rollback, recovery, journal, or final-health behavior:

- one source-pinned FYG8 kernel patch implements the exact target/layout guard,
  45-byte ENTRY/USERSPACE branch, 24-byte UNSAT branch, stable header checks,
  exact write readback, and no ring-metadata mutation;
- one immutable candidate contract derives three 128-bit state tags without
  self-referencing the final patch or compiled artifact hash;
- one static checker applies the patch to the exact base and verifies source
  ordering, compiled record cardinality, Image-to-boot equality, and an exact
  one-member `boot.img.lz4` AP inventory;
- one new typed evidence kind classifies USERSPACE, ENTRY, UNSAT,
  ZERO_AMBIGUOUS, and integrity failure from raw retained bytes; and
- connected D0 uses the same decoder to reject either family and edge-partial
  bytes in the required clean baseline; the common live runner adds only typed
  dispatch.

Only exact USERSPACE is acceptance. ENTRY and UNSAT are diagnostic positives.
Zero still proves nothing. Duplicate, mixed, foreign, or edge-partial family
bytes fail closed as `AMBIGUOUS_INTEGRITY_FAILURE`.

## Fixed identity

```text
contract SHA256
a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae

contract ID (128 bits)
a01800f437cf129e693f32b7199ea6a6

source patch SHA256
6bf03ca0d3448e0a707b03815e94d8ef5c059e9aaa14f3612a0bb953f3758c44
```

The contract preimage binds the exact target, all three base source files,
config symbol, static `/init`, first userspace request, board model, retained
physical layout and magic, state partition, and write semantics. The patch and
every future Image, boot image, AP, run manifest, and static result remain
separately pinned by full SHA-256.

## Validation

The contract checker applied the patch to the clean source-matched FYG8 tree
and verified these patched file identities:

```text
kernel_platform/common/init/main.c
4e4658f083f12543c43112e79fe55241f70be5788cd5456e6d564aca18c78499

kernel_platform/common/init/Kconfig
064f48fb37f8f835c27b8f69b381e14f20774de8e31b29c4eed4d6e3322561b3

kernel_platform/common/arch/arm64/configs/gki_defconfig
b696b4da1514d2a7afab2335d400641fced9f08453d257e69aae1002c0414722
```

Python compilation passed. Focused suites cover patch application, record
derivation/cardinality, artifact closure, design/decoder equivalence, all five
observer states, malformed and foreign records, immutable acceptance identity,
offline candidate binding, kind-specific source closure, typed D0 baseline,
runner dispatch, and existing E0/runner regressions.

## Boundaries

This unit did not compile a kernel, create an Image/boot/AP, create or promote a
manifest, contact a device, invoke Odin, flash, or authorize F1. The artifact
checker is implemented but has not yet verified real compiled artifacts.

Because this unit changes a kernel patch and the Process v2 evidence schema,
one independent safety review of the actual execution-critical closure is the
next step. Candidate build, connected D0, manifest preparation, and F1 remain
forbidden until that review closes.
