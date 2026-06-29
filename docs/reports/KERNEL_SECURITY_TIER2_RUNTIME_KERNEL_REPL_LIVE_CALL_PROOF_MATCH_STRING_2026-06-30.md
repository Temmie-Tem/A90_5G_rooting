# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: match_string

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-match_string-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-match-string-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `match_string`: `0xffffff80099b9c9c`
- Resolution method: `export-recovery`
- Direct BL xrefs: `5`
- Shape: JOPP entry, non-leaf helper; calls `__pi_strcmp`; RET observed at offset `0x78`.
- Disasm contract: x0 is copied to the array base register, x1 is the scalar count, x2 is the search string; each loop loads `array[index]`, stops on NULL, calls `strcmp(item, search)`, returns the index on equality, and returns `0xffffffea` for miss or zero count.
- Source signature: `include/linux/string.h:186`, `int match_string(const char * const *array, size_t n, const char *string)`
- Source pointer contract: x0 is the string-pointer array; x2 is the search string pointer; x1 is scalar bounded count.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `string-pointer-array`, x2 = `search-string-buffer`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with host-supplied numeric pointers. The tool allocated one owned kernel
layout containing a three-entry `const char *` table, a NULL sentinel after the bounded entries, the
three owned string entries, and an owned search string. The hit search was `A90MATCH-BRAVO`, expected
at index `1`. The missing search was `A90MATCH-MISSING`. The proof also called the helper with count
`0`, which disasm predicts returns 32-bit `-EINVAL` (`0xffffffea`) before array traversal.

## Flash And Health

Preconditions:

- v1-repl candidate SHA matched `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- v2321 rollback SHA matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- v2237 fallback SHA matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed with SHA
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
- TWRP recovery image existed with SHA
  `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`.
- Bridge was connected.
- Baseline before flash: `v2321`, `version` OK, `status` OK, `selftest pass=11 warn=1 fail=0`.

Candidate flash:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-readback-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash `version/status` verification passed.
- Candidate native selftest after one transient serial framing retry: `pass=11 warn=1 fail=0`.
- `a90_repl.py selftest`: `a90-repl-v2a1-selftest-pass`.

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
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --timeout 90 \
  --dmesg-tail 80 \
  --safe-op-retries 2 \
  --retry-delay-sec 0.3 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-match-string-20260630/proof \
  match_string
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-match_string-pass",
  "ok": true,
  "array_count": 3,
  "array_items": [
    "A90MATCH-ALPHA",
    "A90MATCH-BRAVO",
    "A90MATCH-CHARLIE"
  ],
  "search": "A90MATCH-BRAVO",
  "missing_search": "A90MATCH-MISSING",
  "expected_hit_index": 1,
  "hit_expected_return_value": "0x1",
  "hit_observed_return_value": "0x1",
  "hit_return_matches_expected_index": true,
  "missing_expected_return_value": "0xffffffea",
  "missing_observed_return_value": "0xffffffea",
  "zero_count_expected_return_value": "0xffffffea",
  "zero_count_observed_return_value": "0xffffffea",
  "layout_unchanged_after_calls": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `match_string` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `int match_string(const char * const *array, size_t n, const char *string)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x2 require verified owned pointers, and x1 count is bounded inside the pointer array.
- `kmalloc-owned-match-string-layout`: OK, allocated one owned kernel layout.
- `owned-match-string-layout-poke-peek`: OK, pointer table, string entries, search string, and canaries were written and read back.
- `match-string-hit-return-contract`: OK, returned index `1`.
- `match-string-hit-layout-immutability`: OK, table, items, and search stayed unchanged.
- `owned-match-string-missing-search-poke-peek`: OK, missing search was written and read back.
- `match-string-missing-return-contract`: OK, returned `0xffffffea`.
- `match-string-zero-count-return-contract`: OK, returned `0xffffffea`.
- `match-string-final-layout-immutability`: OK, table, items, missing search, and canaries stayed unchanged.
- `kfree-owned-match-string-layout`: OK, cleanup succeeded.

Raw runtime slide, `match_string` runtime address, owned layout pointer, item pointers, search pointer,
and raw observed bytes were written only to private evidence and are not included in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-readback-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img
```

Result:

- Remote pushed image SHA matched v2321 SHA.
- Boot readback SHA matched v2321 SHA.
- Post-rollback `version/status` verification passed.
- Final resident: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- Final `selftest`: `pass=11 warn=1 fail=0`.

One candidate selftest read immediately after candidate boot returned no END marker and only stale
serial echo text. The bridge remained reachable; repeated `version` and `selftest` immediately
succeeded. The proof, post-proof health check, rollback, and final health check were clean.

## Conclusion

`match_string` is now live-proven under an owned string-pointer-array plus owned-search-string and
bounded-count contract. The proof confirms the intended helper was reached, returned the expected
array index for a present string, returned 32-bit `-EINVAL` for a missing string and for count `0`,
left the owned layout unchanged, cleaned up the allocation, and left the device healthy. This does
not authorize arbitrary pointer arrays, user pointers, unterminated strings, stale array entries,
out-of-range counts, or mass calling. The device was rolled back to clean v2321 with final
`selftest fail=0`.
