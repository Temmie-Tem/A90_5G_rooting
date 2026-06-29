# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: strncmp

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-strncmp-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-strncmp-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `strncmp`: `0xffffff80099a8d44`
- Resolution method: `leaf-map-disasm+xref`
- Direct BL xrefs: `590`
- Shape: non-JOPP arm64 leaf helper; no BL in scan; RET observed at offset `0x110` with a function-size scan of `520` bytes.
- Source signature: `include/linux/string.h:46`, `extern int strncmp(const char *,const char *,__kernel_size_t)`
- Source pointer contract: x0 is left string, x1 is right string, x2 is scalar bounded count.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `left-string-buffer`, x1 = `right-string-buffer`

`strncmp` is an arm64 leaf routine without the JOPP marker used by most C functions in this image.
The C1 exception is intentionally narrow: it accepts only the `strncmp` System.map label when the body
is leaf/no-BL, has a RET in a bounded function-size scan, has no zero-return-before-ret pattern, and
has at least 500 direct BL xrefs. The observed xref count was `590`.

This proof owns both strings and fixes `count=17`, which is inside both allocated buffers. It does not
authorize arbitrary pointers, unterminated strings, unbounded counts, user pointers, or other string
helpers.

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with host-supplied numeric pointers. The tool allocated distinct owned left
and right strings. Both strings shared `A90STRNCMP-PREFIX` for exactly `count=17` bytes, then differed
immediately after count (`0x5a` vs `0x40`). The proof first required `strncmp(left, right, 17) == 0`,
then changed the right string inside the count at offset `3` and required a positive return. It
verified string/canary immutability after both calls, then freed both strings.

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
- Baseline before flash: `v2321`, `version` OK, `selftest pass=11 warn=1 fail=0`.

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
- Candidate native selftest: `pass=11 warn=1 fail=0`.
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
  --timeout 60 \
  --dmesg-tail 80 \
  --safe-op-retries 1 \
  --retry-delay-sec 0.2 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-strncmp-20260630/proof \
  strncmp
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-strncmp-pass",
  "ok": true,
  "proof_prefix": "A90STRNCMP-PREFIX",
  "count_arg": 17,
  "post_count_left_byte": "0x5a",
  "post_count_right_byte": "0x40",
  "equal_observed_return_value": "0x0",
  "bounded_equal_ignores_post_count_difference": true,
  "mismatch_offset": 3,
  "mismatch_left_byte": "0x53",
  "mismatch_right_byte": "0x40",
  "mismatch_observed_return_value": "0x98",
  "strings_unchanged_after_calls": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `strncmp` resolved by `leaf-map-disasm+xref`.
- `static-source-contract`: OK, signature `extern int strncmp(const char *,const char *,__kernel_size_t)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x1 require verified string
  buffers, bounded count `17`.
- `kmalloc-owned-strncmp-strings`: OK, allocated distinct owned left and right strings.
- `owned-strncmp-string-poke-peek`: OK, strings plus canaries were written and read back.
- `strncmp-count-bounded-equal-return-contract`: OK, first `17` bytes matched and return was `0x0`
  even though byte `17` differed.
- `strncmp-count-bounded-string-immutability`: OK, bounded equal compare did not modify either string.
- `owned-strncmp-mismatch-poke-peek`: OK, right byte at offset `3` was changed from left `0x53` to
  right `0x40`.
- `strncmp-mismatch-return-contract`: OK, mismatch compare returned positive; observed `0x98`.
- `strncmp-mismatch-string-immutability`: OK, mismatch compare did not modify either string.
- `kfree-owned-strncmp-strings`: OK, left and right cleanup both succeeded.

Raw runtime slide, `strncmp` runtime address, owned allocation pointers, and raw observed bytes were
written only to private evidence and are not included in this report.

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

## Conclusion

`strncmp` is now live-proven under the two-owned-NUL-terminated-string plus scalar bounded-count
contract. The proof confirms the intended helper was reached, ignored a first differing byte
immediately after the count, returned a positive value for a controlled count-internal mismatch, left
both strings unchanged, and left the device healthy after cleanup. This does not authorize arbitrary
pointers, unterminated strings, unbounded counts, user pointers, or other string helpers. The device was
rolled back to clean v2321 with final `selftest fail=0`.
