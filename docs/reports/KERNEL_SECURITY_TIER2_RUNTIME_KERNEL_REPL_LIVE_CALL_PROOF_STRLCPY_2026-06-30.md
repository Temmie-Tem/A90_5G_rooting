# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: strlcpy

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-strlcpy-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-strlcpy-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `strlcpy`: `0xffffff80099b9724`
- Resolution method: `export-recovery`
- Direct BL xrefs: `963`
- Shape: JOPP entry true; body calls `__pi_strlen` and `__memcpy`; RET observed at offset `0x64`.
- Source signature: `include/linux/string.h:28`, `size_t strlcpy(char *, const char *, size_t)`
- Source pointer contract: x0 is destination buffer, x1 is source string buffer, x2 is scalar size.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `destination-buffer`, x1 = `source-string-buffer`

The initial advisory sweep classified `strlcpy` as a safe pointer candidate but kept the call gate at
DENY because it was not yet in the vetted seed whitelist. This proof owns both buffers and fixes
`size=32`, which is inside the allocated destination. It does not authorize arbitrary
destination/source pointers or arbitrary sizes.

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.

The target was not called with host-supplied numeric pointers. The tool allocated distinct owned
destination and source buffers, filled the destination scan window with a canary, zero-filled the
source window, wrote `A90STRLCPY\0`, verified the source by peek, called
`strlcpy(dst, src, 32)`, verified the destination prefix and post-size canary, then freed both
buffers.

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
- Candidate selftest: `pass=11 warn=1 fail=0`.
- `a90_repl.py selftest`: `a90-repl-v2a1-selftest-pass`.

One REPL selftest attempt hit serial echo/END-marker noise before the proof call. `version` realigned
the bridge and the REPL selftest retry passed. This was a transport artifact, not a device health
regression.

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
  --evidence-dir workspace/private/runs/kernel/live-call-proof-strlcpy-20260630/proof \
  strlcpy
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-strlcpy-pass",
  "ok": true,
  "proof_string": "A90STRLCPY",
  "size_arg": 32,
  "expected_return_value": "0xa",
  "observed_return_value": "0xa",
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `strlcpy` resolved by `export-recovery`.
- `static-source-contract`: OK, signature `size_t strlcpy(char *, const char *, size_t)`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x1 require verified buffers,
  bounded size `32`.
- `kmalloc-owned-strlcpy-buffers`: OK, allocated distinct owned destination and source buffers.
- `owned-strlcpy-source-poke-peek`: OK, `A90STRLCPY\0` was written and read back.
- `strlcpy-return-contract`: OK, returned `0xa`, expected source length `0xa`.
- `strlcpy-destination-contract`: OK, destination prefix matched the source string and the canary
  after the size boundary remained intact.
- `kfree-owned-strlcpy-buffers`: OK, destination and source cleanup both succeeded.

Raw runtime slide, `strlcpy` runtime address, owned allocation pointers, and raw observed bytes were
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
- Final `selftest verbose`: `pass=11 warn=1 fail=0`.

One immediate final selftest command hit serial echo/END-marker noise after a clean `version`.
Selftest retry passed. This was a transport artifact, not a device health regression.

## Conclusion

`strlcpy` is now live-proven under the owned destination buffer plus owned NUL-terminated source
buffer plus bounded-size contract. The proof confirms the intended helper was reached, returned the
exact expected source length for `A90STRLCPY`, wrote the expected destination prefix without crossing
the size boundary, and left the device healthy after cleanup. This does not authorize arbitrary
string pointers, arbitrary destination sizes, or other string/memory copy helpers. The device was
rolled back to clean v2321 with final `selftest fail=0`.
