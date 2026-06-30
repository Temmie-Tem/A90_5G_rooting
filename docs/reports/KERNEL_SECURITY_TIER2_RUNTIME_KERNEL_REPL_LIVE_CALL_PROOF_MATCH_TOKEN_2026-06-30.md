# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: match_token

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-match_token-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-match-token-20260630/proof/a90_repl_evidence.json`

## Static Gate

Target:

- `match_token`: `0xffffff800855b404`
- Resolution method: `export-recovery`
- Direct BL xrefs: `23`
- Shape: JOPP entry, non-leaf parser helper.
- Helper calls in the function body include `__pi_strcmp`, `strchr`, `simple_strtoul`,
  `__pi_strncmp`, `__pi_strlen`, and `simple_strtol`.
- Disasm contract used for this proof: `struct match_token` entries are 16 bytes; the pattern pointer
  is loaded at entry offset `+8`; a NULL pattern terminates the table; an exact pattern with no `%`
  takes the `strcmp(pattern, option)` path and does not write `args[]`.
- Source signature: `include/linux/parser.h:30`,
  `int match_token(char *, const match_table_t table, substring_t args[])`
- Source pointer contract: x0 is an owned mutable option string, x1 is an owned `match_token` table
  after `match_table_t` array-typedef decay, and x2 is an owned `substring_t args[MAX_OPT_ARGS]`
  array.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 = `mutable-option-string-buffer`, x1 = `match-token-table`,
  x2 = `substring-args-array`

Owned-input orchestration:

- `__kmalloc`: `0xffffff800826ae34`, `export-recovery`, direct BL xrefs `1765`
- `kfree`: `0xffffff800826b354`, `export-recovery`, direct BL xrefs `10596`
- `__kmalloc` passed the no-pre-call-x0-deref guard.
- The target was not called with host-supplied numeric pointers. The proof used one tool-owned layout
  containing a mutable option string `A90MATCH-TOKEN`, a two-entry table
  `{0x4a90, "A90MATCH-TOKEN"}, {0, NULL}`, an owned canary-filled `args` array, and canaries around
  controlled regions.
- `%d/%s/%u/%o/%x` extraction patterns were intentionally excluded from this unit.

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
  --timeout 180 \
  --dmesg-tail 80 \
  --safe-op-retries 5 \
  --retry-delay-sec 0.75 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-match-token-20260630/proof \
  match_token
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-match_token-pass",
  "ok": true,
  "input_ascii": "A90MATCH-TOKEN",
  "pattern_ascii": "A90MATCH-TOKEN",
  "expected_token": "0x4a90",
  "observed_return": "0x4a90",
  "return_matches_expected_token": true,
  "table_unchanged_after_call": true,
  "args_unchanged_after_call": true,
  "input_unchanged_after_call": true,
  "pattern_unchanged_after_call": true,
  "proof_status": "trusted-under-owned-input-contract",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Checks:

- `static-c1-identity`: OK, `match_token` resolved by `export-recovery`.
- `static-source-contract`: OK, signature
  `int match_token(char *, const match_table_t table, substring_t args[])`; pointer args x0/x1/x2.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0/x1/x2 require verified owned
  pointers.
- `kmalloc-owned-match-token-layout`: OK, allocated one owned kernel layout.
- `owned-match-token-layout-poke-peek`: OK, table, args array, option string, pattern string, and
  canaries were written and read back.
- `match-token-exact-hit-return-contract`: OK, returned token `0x4a90`.
- `match-token-exact-layout-immutability`: OK, table, args, input, and pattern regions stayed
  unchanged.
- `kfree-owned-match-token-layout`: OK, cleanup of the proof layout succeeded.

Raw runtime slide, `match_token` runtime address, owned layout pointer, table pointer, args pointer,
input pointer, pattern pointer, and raw observed bytes were written only to private evidence and are
not included in this report.

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
- Rollback helper health showed `selftest pass=11 warn=1 fail=0`.
- A first standalone final `selftest` read hit serial echo noise and missed the END marker; immediate
  retry confirmed `selftest pass=11 warn=1 fail=0`.

## Conclusion

`match_token` is now live-proven under an owned exact-table parser contract. The proof confirms the
intended helper was reached, returned token `0x4a90` for exact pattern `A90MATCH-TOKEN`, preserved
the owned table, args array, input, pattern, and canaries, and cleaned up the proof layout. It does
not authorize `%d/%s/%u/%o/%x` extraction paths, arbitrary parser tables, arbitrary substring output
buffers, user pointers, unterminated strings, invalid terminators, stale buffers, or mass calling.
