# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: __bitmap_complement

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-__bitmap_complement-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-bitmap-complement-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit continued the bitmap helper sweep with the first simple mutation helper after the read-only
`__bitmap_weight` and `__bitmap_subset` proofs. `__bitmap_complement` was selected because C1
recovered one export candidate, the verified System.map agreed with it, it has a direct BL xref, and
the static shape is leaf/no-BL with only x1 source loads, x0 destination stores, and scalar `nbits`
flow.

This does not promote arbitrary bitmap mutation. The proof creates tool-owned destination and source
bitmap buffers, resets the destination before every case, calls only bounded `nbits` values inside
the 128-bit proof bitmap, re-peeks destination/source/canaries after every call, and frees both
allocations.

## Static Gate

Target:

- `__bitmap_complement`: `0xffffff800855c8e4`
- Resolution method: `export-recovery`
- Direct BL xrefs: `1`
- Shape: JOPP entry, leaf/no-BL.
- Static word checks:
  - `0x53067c48` at entry for `nbits >> 6`.
  - `0xf840854c` for the first source bitmap load.
  - `0xf800856c` for the first destination bitmap store.
  - `0xf8686829` for the tail source bitmap load.
  - `0xf8286809` for the tail destination bitmap store.
- Source signature: `include/linux/bitmap.h:105`,
  `extern void __bitmap_complement(unsigned long *dst, const unsigned long *src, unsigned int nbits)`
- Source pointer contract: x0 is mutable destination, x1 is const source, x2 is scalar `nbits`.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 `bitmap-dst-buffer`, x1 `bitmap-src-buffer`.

The target was not called with arbitrary numeric pointers. The proof requires two owned bitmap
buffers and scalar `nbits` values bounded to the proof bitmaps.

## Host Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  __bitmap_complement

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_a90_repl.CallSafetyClassificationTests.test_safe_with_valid_pointer_seed_records_required_args \
  tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args \
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof___bitmap_complement_passes_with_owned_bitmap_contract

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
```

Result:

- `py_compile`: pass.
- CLI classify: `SAFE-WITH-VALID-PTR`, verified by `export-recovery`, direct-BL xrefs `1`,
  leaf/no-BL, required x0 `bitmap-dst-buffer`, x1 `bitmap-src-buffer`.
- Focused tests: static classification/source tests and the new fake-transport mutation proof passed.
- Full `tests.test_a90_repl`: `Ran 138 tests`, `OK`.

## Flash And Health

Preconditions:

- v1-repl candidate SHA matched `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- v2321 rollback SHA matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- v2237 fallback SHA matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed with SHA
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
- TWRP recovery image existed with SHA
  `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`.
- TWRP recovery tar existed with SHA
  `6d9e929462ea4c85f257b080431d387d5bfb787ff800bd4178c823c3874d862a`.
- Bridge was connected.
- Baseline before flash: `v2321`, `version` OK, `status` OK, `selftest pass=11 warn=1 fail=0`.

Candidate flash:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash helper `version/status` verification passed.
- The first standalone candidate selftest attempt hit a transient bridge prompt/`AT` desync; a
  follow-up `version` re-synchronized the bridge and standalone selftest returned
  `pass=11 warn=1 fail=0`.
- REPL selftest completed and returned `a90-repl-v2a1-selftest-pass`.

The v1-repl image intentionally keeps the v2321 native-init identity string, so `version` alone does
not distinguish it from the clean rollback image. The REPL selftest is the functional proof that the
candidate kernel REPL path is resident.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --timeout 180 --dmesg-tail 80 --safe-op-retries 5 --retry-delay-sec 0.75 \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-bitmap-complement-20260630/proof \
  __bitmap_complement
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-__bitmap_complement-pass",
  "ok": true,
  "proof_status": "trusted-under-owned-input-contract",
  "input_contract": "owned destination unsigned-long bitmap buffer + owned source unsigned-long bitmap buffer + scalar bit count bounded inside both bitmaps",
  "return_contract": "void; destination bitmap words are complemented for the covered words, source bitmap and canaries stay unchanged",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Case table:

| Case | nbits | Destination | Source | Canaries |
| --- | ---: | --- | --- | --- |
| zero-size | 0 | unchanged expected initial pattern | unchanged | preserved |
| low-tail | 10 | matched expected first-word complement tail path | unchanged | preserved |
| first-word-boundary | 64 | matched expected first-word complement | unchanged | preserved |
| second-word-tail | 80 | matched expected first-word plus second-word tail complement | unchanged | preserved |
| full-size | 128 | matched expected full 128-bit complement | unchanged | preserved |

Checks:

- `static-c1-identity`: OK, `__bitmap_complement` resolved by `export-recovery`.
- `static-source-contract`: OK, signature matches the source oracle and pointer arg indices are `[0,1]`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0 `bitmap-dst-buffer`,
  x1 `bitmap-src-buffer`.
- Static word checks: OK for entry `nbits` shift, first source load, first destination store, tail
  source load, and tail destination store.
- Owned source and destination allocations: OK.
- Source/destination poke/peek setup checks: OK.
- Five-case mutation table: OK.
- Immutability: OK, source bitmap and both canaries stayed unchanged; destination changed only as
  expected for each case.
- Cleanup: OK, both buffers freed with `kfree`.

Raw per-boot slide, target runtime address, owned allocation pointers, and observed bytes were
written only to private evidence and are not included in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img
```

Result:

- Remote pushed image SHA matched rollback SHA.
- Boot readback SHA matched rollback SHA.
- Post-rollback helper `version/status` verification passed.
- A first standalone `version` attempt after rollback hit the same transient bridge `AT` desync; the
  bridge was restarted host-side and the next `version` completed normally.
- Final standalone `version` confirmed `v2321-usb-clean-identity-rodata`.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `__bitmap_complement` as `live-proven` only under this contract:

- Static link identity: `0xffffff800855c8e4`, `export-recovery`, direct BL xrefs `1`.
- Trusted input contract: owned destination unsigned-long bitmap buffer, owned source unsigned-long
  bitmap buffer, and scalar bit count bounded inside both bitmaps.
- Observed result: zero-size no-op, low-tail destination mutation, first-word boundary,
  second-word tail, and full-size destination complement cases; source bitmap and canaries preserved.
- Cleanup: `kfree-owned-bitmap-complement-buffers-ok`.

This does not authorize arbitrary bitmap pointers, unbounded `nbits`, aliasing assumptions, other
bitmap mutation helpers, or mass calling.
