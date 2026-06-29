# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: strncasecmp

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-strncasecmp-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-strncasecmp-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `strncasecmp`: `0xffffff80099b960c`
- Resolution method: `export-recovery`
- Direct BL xrefs: `88`
- Shape: JOPP entry, leaf/no-BL helper; RET observed in scan.
- Disasm contract: x0/x1 are consumed as NUL-terminated byte strings through a casefold compare loop; x2 is the bounded count and can return `0` immediately.
- Source signature: `include/linux/string.h:52`, `extern int strncasecmp(const char *s1, const char *s2, size_t n)`
- Source pointer contract: x0 is the left NUL-terminated string buffer; x1 is the right NUL-terminated string buffer; x2 is the scalar bounded count.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `left-string-buffer`, x1 = `right-string-buffer`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with host-supplied numeric pointers. The tool allocated two distinct owned
kernel string buffers. The left prefix was `A90STRNCASECMP-PREFIX`; the right prefix was
`a90strncasecmp-prefix`; the scalar count was `21`. Bytes immediately after the count differed
(`0x5a` vs `0x40`) to prove the boundary. For the mismatch case, one right-string byte was rewritten
to `0x40` at offset `15`, where the folded left byte is `0x70`. Both strings had private canary bytes
after the NUL terminator.

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
  --timeout 90 \
  --dmesg-tail 80 \
  --safe-op-retries 2 \
  --retry-delay-sec 0.3 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-strncasecmp-20260630/proof \
  strncasecmp
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-strncasecmp-pass",
  "ok": true,
  "proof_left_prefix": "A90STRNCASECMP-PREFIX",
  "proof_right_prefix": "a90strncasecmp-prefix",
  "count_arg": 21,
  "post_count_left_byte": "0x5a",
  "post_count_right_byte": "0x40",
  "equal_expected_return_value": "0x0",
  "equal_observed_return_value": "0x0",
  "bounded_casefold_equal_ignores_post_count_difference": true,
  "mismatch_expected_return_sign": "positive",
  "mismatch_observed_return_value": "0x30",
  "mismatch_offset": 15,
  "mismatch_folded_left_byte": "0x70",
  "mismatch_right_byte": "0x40",
  "strings_unchanged_after_calls": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `strncasecmp` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `extern int strncasecmp(const char *s1, const char *s2, size_t n)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x1 require verified owned string buffers, and x2 count is bounded inside both buffers.
- `kmalloc-owned-strncasecmp-strings`: OK, allocated two distinct owned kernel string buffers.
- `owned-strncasecmp-string-poke-peek`: OK, both strings and canaries were written and read back.
- `strncasecmp-count-bounded-casefold-equal-return-contract`: OK, first 21 bytes matched after case-folding and returned `0x0` while post-count bytes differed.
- `strncasecmp-mismatch-return-contract`: OK, first casefolded mismatch inside count returned positive `0x30`.
- `strncasecmp-string-immutability`: OK, both strings stayed unchanged after both calls.
- `kfree-owned-strncasecmp-strings`: OK, cleanup succeeded.

Raw runtime slide, `strncasecmp` runtime address, owned allocation pointers, and raw observed bytes were
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
- Final slow-mode `selftest`: `pass=11 warn=1 fail=0`.

## Note

One final selftest command after rollback returned rc `0` with a valid END marker but omitted the
summary line in the captured output. The command was repeated and the repeated final selftest passed.
No proof command failed, and no rollback failure occurred.

## Conclusion

`strncasecmp` is now live-proven under the two-owned-NUL-terminated-kernel-string plus bounded-count
contract where count stays inside both owned buffers. The proof confirms the intended helper was
reached, returned `0` for count-bounded casefold-equal bytes while ignoring a post-count difference,
returned a positive sign for the selected first casefolded mismatch inside count, preserved both
strings and their canaries, cleaned up both allocations, and left the device healthy. This does not
authorize arbitrary pointers, user pointers, unterminated strings, out-of-range counts, locale
assumptions beyond the observed kernel helper behavior, or mass calling. The device was rolled back to
clean v2321 with final `selftest fail=0`.
