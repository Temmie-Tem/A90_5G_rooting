# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: memchr

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-memchr-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-memchr-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `memchr`: `0xffffff80099a8488`
- Resolution method: `leaf-map-disasm+xref`
- Direct BL xrefs: `25`
- Shape: non-JOPP arm64 leaf helper; no BL in scan; RET observed at offset `0x1c`.
- Source signature: `include/linux/string.h:149`, `extern void * memchr(const void *,int,__kernel_size_t)`
- Source pointer contract: x0 is the buffer pointer, x1 is the scalar search byte, x2 is scalar size.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `buffer`

`memchr` is an arm64 leaf routine without the JOPP marker used by most C functions in this image. The
C1 exception is intentionally narrow: it accepts only the `memchr` System.map label when the body is
leaf/no-BL, has a RET in scan, has no zero-return-before-ret pattern, and has at least 20 direct BL
xrefs. The observed xref count was `25`.

This proof owns the buffer and fixes `size=26`, which is inside the allocated buffer. It does not
authorize arbitrary pointers, unbounded sizes, user pointers, or other memory helpers.

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with a host-supplied numeric pointer. The tool allocated one owned buffer,
filled the bounded scan window with initialized bytes plus a post-size canary, verified it by peek,
called `memchr(buf, 'Q', 26)` for the hit case, verified the buffer stayed unchanged, called
`memchr(buf, '@', 26)` while `@` existed only in the post-size canary, verified the missing return
contract and buffer immutability, then freed the buffer.

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
  --evidence-dir workspace/private/runs/kernel/live-call-proof-memchr-20260630/proof \
  memchr
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-memchr-pass",
  "ok": true,
  "proof_bytes_label": "A90MEMCHR-HIT-Q-END-012345",
  "size_arg": 26,
  "search_byte": "0x51",
  "expected_hit_offset": 14,
  "hit_return_matches_expected_offset": true,
  "missing_byte": "0x40",
  "missing_observed_return_value": "0x0",
  "missing_return_matches_null": true,
  "canary_contains_missing_byte": true,
  "buffer_unchanged_after_calls": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `memchr` resolved by `leaf-map-disasm+xref`.
- `static-source-contract`: OK, signature `extern void * memchr(const void *,int,__kernel_size_t)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0 requires a verified buffer,
  bounded size `26`.
- `kmalloc-owned-memchr-buffer`: OK, allocated one owned kernel buffer.
- `owned-memchr-buffer-poke-peek`: OK, bounded scan bytes plus canary were written and read back.
- `memchr-hit-return-contract`: OK, hit returned owned buffer pointer plus offset `14`.
- `memchr-hit-buffer-immutability`: OK, hit search did not modify the buffer.
- `memchr-missing-return-contract`: OK, missing byte returned `0x0` even though the post-size canary
  contained `@`.
- `memchr-missing-buffer-immutability`: OK, missing search did not modify the buffer.
- `kfree-owned-memchr-buffer`: OK, cleanup succeeded.

Raw runtime slide, `memchr` runtime address, owned allocation pointer, returned pointer, and raw
observed bytes were written only to private evidence and are not included in this report.

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

## Note On Serial Noise

The first candidate and final standalone `selftest` reads hit serial-input echo noise and failed to
parse an `A90P1 END` marker. In both cases the body either already showed or the bounded retry showed
`selftest fail=0`; a clean `version` probe restored framing before retry. This was a transport
capture/input issue, not a device health regression.

## Conclusion

`memchr` is now live-proven under the owned initialized buffer plus scalar-search-byte and bounded-size
contract. The proof confirms the intended helper was reached, returned the first matching owned-buffer
pointer offset, returned `NULL` when the byte existed only beyond the size argument, left the buffer
unchanged, and left the device healthy after cleanup. This does not authorize arbitrary pointers,
unbounded sizes, user pointers, or other memory helpers. The device was rolled back to clean v2321 with
final `selftest fail=0`.
