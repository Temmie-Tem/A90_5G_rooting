# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: match_strdup

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-match_strdup-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-match-strdup-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `match_strdup`: `0xffffff800855b98c`
- Resolution method: `export-recovery`
- Direct BL xrefs: `28`
- Shape: JOPP entry, non-leaf helper calling `__kmalloc` and `__memcpy`.
- Disasm contract: x0 is the `substring_t *`; the function reads `from/to`, allocates `len + 1`,
  copies bounded source bytes, writes a generated trailing NUL, and returns the duplicate pointer.
- Source signature: `include/linux/parser.h:37`, `char * match_strdup(const substring_t *)`
- Source pointer contract: x0 is an owned `substring_t` slot whose range points at owned bounded text.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `substring-slot`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.
- The target was not called with host-supplied numeric pointers. The proof used one tool-owned
  layout containing `substring_t {from,to}`, bounded source text `A90MATCH-STRDUP-Q-END`, and
  canaries around the controlled regions.
- The returned duplicate pointer was treated as owned only if it was sane kernel lowmem, distinct
  from the proof layout, byte-verified, and then freed.

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
  --from-native \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-readback-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-version v2321-usb-clean-identity-rodata \
  workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash `version/status` verification passed.
- Standalone candidate selftest confirmed `pass=11 warn=1 fail=0`.
- First `a90_repl.py selftest` attempt hit a transient serial framing timeout while setting
  `panic_on_oops`; immediate device health stayed `selftest pass=11 warn=1 fail=0`.
- Retried `a90_repl.py selftest` with wider serial bounds: `a90-repl-v2a1-selftest-pass`.

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
  --timeout 120 \
  --dmesg-tail 80 \
  --safe-op-retries 3 \
  --retry-delay-sec 0.5 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-match-strdup-20260630/proof \
  match_strdup
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-match_strdup-pass",
  "ok": true,
  "input_ascii": "A90MATCH-STRDUP-Q-END",
  "expected_duplicate_len": 22,
  "duplicate_bytes_match_expected": true,
  "substring_unchanged_after_call": true,
  "input_unchanged_after_call": true,
  "duplicate_pointer_redacted": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `match_strdup` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `char * match_strdup(const substring_t *)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0 requires verified owned pointer.
- `kmalloc-owned-match-strdup-layout`: OK, allocated one owned kernel layout.
- `owned-match-strdup-layout-poke-peek`: OK, substring slot, input text, and canaries were written and read back.
- `match-strdup-return-pointer-contract`: OK, returned a sane distinct kernel duplicate pointer.
- `match-strdup-duplicate-bytes-contract`: OK, duplicate bytes matched the substring plus generated NUL.
- `match-strdup-input-layout-immutability`: OK, substring slot and input text stayed unchanged.
- `kfree-owned-match-strdup-layout-and-duplicate`: OK, cleanup of both returned duplicate and proof layout succeeded.

Raw runtime slide, `match_strdup` runtime address, owned layout pointer, substring pointer, input pointer,
duplicate pointer, and raw observed bytes were written only to private evidence and are not included
in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-readback-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-version v2321-usb-clean-identity-rodata \
  workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img
```

Result:

- Remote pushed image SHA matched v2321 SHA.
- Boot readback SHA matched v2321 SHA.
- Post-rollback `version/status` verification passed.
- Final standalone selftest confirmed `pass=11 warn=1 fail=0` with rc=0/status=ok.
- The final health read contained minor serial echo noise before the valid END marker.

## Conclusion

`match_strdup` is now live-proven under an owned `substring_t` contract. The proof confirms the
intended helper was reached, duplicated bounded substring text `A90MATCH-STRDUP-Q-END` into a new
owned kmalloc string with generated NUL, preserved the input layout and canaries, and cleaned up both
the returned duplicate and proof layout. It does not authorize arbitrary substring pointers, invalid
ranges, user pointers, stale buffers, NULL returns, ownership transfer beyond bounded cleanup, or mass
calling.
