# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: strlcat

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-strlcat-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-strlcat-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `strlcat`: `0xffffff80099b98f4`
- Resolution method: `export-recovery`
- Direct BL xrefs: `522`
- Shape: JOPP entry, non-leaf helper; three bounded calls in scan: `__pi_strlen`, `__pi_strlen`, and `__memcpy`; RET observed in scan.
- Fortify guard: disasm branches to a trap when destination length is greater than or equal to size, so the proof pins `size > strlen(dst)`.
- Source signature: `include/linux/string.h:40`, `extern size_t strlcat(char *, const char *, __kernel_size_t)`
- Source pointer contract: x0 is the mutable destination string buffer; x1 is the source NUL-terminated string buffer; x2 is the scalar bounded size.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `destination-buffer`, x1 = `source-string-buffer`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with host-supplied numeric pointers. The tool allocated one owned mutable
destination string buffer and one distinct owned source string buffer. The destination initially held
`A90STRLCAT-DST` followed by a NUL terminator, `0x57` tail bytes, and an `0xcc` canary. The source held
`-SRC-Q-END` followed by its own canary. The live contract required `strlcat(dst, src, 21)` to avoid
the `dlen >= size` trap path, return `strlen(dst) + strlen(src)`, append only the size-bounded source
prefix plus NUL, preserve the destination post-NUL tail and canary, and leave the source buffer
unchanged.

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
- Candidate native selftest: `pass=11 warn=1 fail=0` after one serial echo-noise retry.
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
  --evidence-dir workspace/private/runs/kernel/live-call-proof-strlcat-20260630/proof \
  strlcat
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-strlcat-pass",
  "ok": true,
  "size_arg": 21,
  "copy_len": 6,
  "expected_return_value": "0x18",
  "observed_return_value": "0x18",
  "proof_string": "A90STRLCAT-DST-SRC-Q",
  "destination_appended_size_bounded_source": true,
  "source_unchanged_after_call": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `strlcat` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `extern size_t strlcat(char *, const char *, __kernel_size_t)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x1 require verified owned buffers, and destination length is less than size.
- `kmalloc-owned-strlcat-buffers`: OK, allocated two distinct owned kernel buffers.
- `owned-strlcat-buffer-poke-peek`: OK, destination prefix, source string, tail, and canaries were written and read back.
- `strlcat-return-contract`: OK, returned `0x18`, the original destination length plus source length.
- `strlcat-destination-contract`: OK, appended the first six source bytes to make `A90STRLCAT-DST-SRC-Q`, wrote NUL, and preserved tail/canary.
- `strlcat-source-immutability`: OK, source buffer stayed unchanged.
- `kfree-owned-strlcat-buffers`: OK, cleanup succeeded.

Raw runtime slide, `strlcat` runtime address, owned allocation pointers, and raw observed bytes were
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

Two serial observation commands hit echo noise before an END marker: the first candidate selftest
after flash and the first final selftest after rollback. In both cases `version` re-synchronized the
bridge and the repeated selftest passed. No proof command failed, and no rollback failure occurred.

## Conclusion

`strlcat` is now live-proven under the owned mutable destination string plus owned NUL-terminated
source string plus scalar bounded size contract where `size > strlen(dst)` and size is inside the
destination allocation. The proof confirms the intended helper was reached, returned the expected
`strlen(dst) + strlen(src)` scalar, appended only the size-bounded source prefix plus NUL terminator,
preserved destination bytes after the terminator and the canary, left the source unchanged, cleaned up
both allocations, and left the device healthy. This does not authorize arbitrary pointers, user
pointers, undersized destinations, `size <= strlen(dst)`, unterminated strings, overlapping strings, or
mass calling. The device was rolled back to clean v2321 with final `selftest fail=0`.
