# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: memzero_explicit

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-memzero_explicit-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-memzero-explicit-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `memzero_explicit`: `0xffffff80099b9dd4`
- Resolution method: `export-recovery`
- Direct BL xrefs: `140`
- Shape: JOPP entry, non-leaf helper calling `__memset`.
- Disasm contract: x0 is the owned destination buffer, x1 is the scalar count. The code moves
  `x1` to `x2`, sets `w1 = 0`, and calls `__memset(x0, 0, x1)`.
- Source signature: `include/linux/string.h:218`, `void memzero_explicit(void *s, size_t count)`
- Source pointer contract: x0 is an owned initialized destination buffer; x1 is a bounded scalar count.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `destination-buffer`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.
- The target was not called with a host-supplied numeric pointer. The proof used one tool-owned
  initialized destination buffer and a scalar count inside the allocation.

Because the source API is `void`, the observed x0 value after the call was recorded only in private
evidence and was not used as a success condition.

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
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --from-native \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-readback-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash `version/status` verification passed.
- Post-flash selftest confirmed `pass=11 warn=1 fail=0`.
- REPL selftest: `a90-repl-v2a1-selftest-pass`.

The v1-repl image intentionally keeps the v2321 native-init identity string, so `version` alone does
not distinguish it from the clean rollback image. The REPL selftest is the functional proof that the
candidate kernel REPL path is resident.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof memzero_explicit \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-memzero-explicit-20260630/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-memzero_explicit-pass",
  "ok": true,
  "zero_count": 24,
  "source_len": 40,
  "expected_return_value": "void-return-ignored",
  "observed_return_value": "void-return-ignored",
  "zeroed_prefix_matches": true,
  "tail_after_count_preserved": true,
  "post_count_canary_preserved": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `memzero_explicit` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `void memzero_explicit(void *s, size_t count)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0 requires a verified owned buffer.
- `kmalloc-owned-memzero-explicit-destination-buffer`: OK, allocated one owned destination buffer.
- `owned-memzero-explicit-destination-poke-peek`: OK, initialized bytes and canary were written and read back.
- `memzero-explicit-return-ignored`: OK, return kind is `void`; observed x0 was not trusted.
- `memzero-explicit-zero-tail-canary-contract`: OK, first 24 bytes zeroed, tail after count preserved,
  and post-count canary preserved.
- `kfree-owned-memzero-explicit-destination-buffer`: OK, owned buffer was freed.

Raw runtime slide, target runtime address, owned allocation pointer, observed return register, and raw
observed buffer bytes were written only to private evidence and are not included in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img \
  --from-native \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-readback-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
```

Result:

- Remote pushed image SHA matched v2321 SHA.
- Boot readback SHA matched v2321 SHA.
- Post-rollback `version/status` verification passed.
- Final standalone selftest had minor serial echo noise before the valid frame, then confirmed
  `pass=11 warn=1 fail=0` with rc=0/status=ok.

## Conclusion

`memzero_explicit` is now live-proven under an owned initialized destination buffer plus scalar bounded
zero-count contract. The proof confirms the intended helper was reached, ignored the void return,
zeroed exactly the bounded prefix, preserved bytes after the count and the post-count canary, cleaned
up the owned allocation, and left the device healthy. This does not authorize arbitrary destination
pointers, user pointers, unbounded counts, NULL pointers, unowned memory, broader zeroing contracts, or
mass calling. The device was rolled back to clean v2321 with final `selftest fail=0`.
