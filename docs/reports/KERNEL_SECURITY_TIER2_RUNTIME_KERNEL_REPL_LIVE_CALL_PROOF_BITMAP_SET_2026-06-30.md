# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: __bitmap_set

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-__bitmap_set-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-bitmap-set-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit continued the bitmap mutation-helper sweep after `__bitmap_or`. `__bitmap_set`
was selected because C1 recovered one export candidate, the verified System.map agreed with it,
it has direct callers, and the static shape is leaf/no-BL with one mutable bitmap pointer plus scalar
`start` and `len` flow. `__bitmap_clear` was also verified as a nearby candidate but parked for a
separate unit.

This does not promote arbitrary bitmap mutation. The proof creates one tool-owned bitmap buffer,
resets it before every case, calls only bounded `start/len` ranges inside the 128-bit proof bitmap,
re-peeks bitmap/canary state, and frees the allocation.

## Static Gate

Target:

- `__bitmap_set`: `0xffffff800855ce7c`
- Resolution method: `export-recovery`
- Direct BL xrefs: `24`
- Shape: JOPP entry, leaf/no-BL.
- Static word checks:
  - `0x53067c2c` at entry for `start >> 6`.
  - `0xf940012e` for the first affected word load.
  - `0xaa0b01ce` for the first OR operation.
  - `0xf900012e` for the first affected word store.
  - `0xf8008588` for the middle full-word store path.
  - `0xf940012c` for the tail word load.
  - `0xf9000128` for the tail word store.
- Source signature: `include/linux/bitmap.h:124`,
  `extern void __bitmap_set(unsigned long *map, unsigned int start, int len)`
- Source pointer contract: x0 is the mutable bitmap, x1 is scalar `start`, x2 is scalar `len`.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x0 `bitmap-buffer`.

The target was not called with an arbitrary numeric pointer. The proof requires an owned bitmap and
scalar `start/len` values bounded to that bitmap.

## Host Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_a90_repl.CallSafetyClassificationTests.test_proven_live_call_targets_stay_safe \
  tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args \
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof___bitmap_set_passes_with_owned_bitmap_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  __bitmap_set

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
```

Result:

- `py_compile`: pass.
- Focused tests: static classification, source signature, and the fake-transport range-set proof
  passed (`Ran 3 tests`, `OK`).
- CLI classify: `SAFE-WITH-VALID-PTR`, verified by `export-recovery`, direct-BL xrefs `24`,
  leaf/no-BL, required x0 `bitmap-buffer`.
- Full `tests.test_a90_repl`: `Ran 141 tests`, `OK`.

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

A first local-image marker probe with `--expect-version v1-repl` stopped during local image
inspection before any reboot or flash. The candidate image intentionally keeps the v2321 native-init
identity string, so the device run pinned artifact identity by local SHA and boot-block readback SHA
instead of by version text.

Candidate flash:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/native_init_flash.py \
  workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-readback-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --verify-protocol cmdv1 \
  --from-native
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash helper `version/status` verification passed.
- Candidate standalone selftest returned `pass=11 warn=1 fail=0`.
- REPL selftest completed and returned `a90-repl-v2a1-selftest-pass`.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --timeout 180 --dmesg-tail 80 --safe-op-retries 5 --retry-delay-sec 0.75 \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-bitmap-set-20260630/proof \
  __bitmap_set
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-__bitmap_set-pass",
  "ok": true,
  "proof_status": "trusted-under-owned-input-contract",
  "input_contract": "owned unsigned-long bitmap buffer + scalar start/len bounded inside that bitmap",
  "return_contract": "void; bits in the bounded range [start,start+len) are set, other bits and canary stay unchanged",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Case table:

| Case | start | len | Bitmap | Canary |
| --- | ---: | ---: | --- | --- |
| zero-len-noop | 5 | 0 | unchanged expected initial pattern | preserved |
| low-single-bit | 1 | 1 | matched expected single-bit set | preserved |
| low-range | 4 | 6 | matched expected low-range set | preserved |
| cross-word-range | 62 | 5 | matched expected cross-word range set | preserved |
| second-word-range | 80 | 8 | matched expected second-word range set | preserved |
| full-size | 0 | 128 | matched expected full-bitmap set | preserved |

Checks:

- `static-c1-identity`: OK, `__bitmap_set` resolved by `export-recovery`.
- `static-source-contract`: OK, signature matches the source oracle and pointer arg indices are `[0]`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x0 `bitmap-buffer`.
- Static word checks: OK for start word calculation, first load/OR/store, middle full-word store,
  and tail load/store.
- Owned bitmap allocation and poke/peek setup: OK.
- Six-case mutation table: OK.
- Canary preservation: OK.
- Cleanup: OK, the owned bitmap buffer was freed with `kfree`.

Raw per-boot slide, target runtime address, owned allocation pointer, and observed bytes were written
only to private evidence and are not included in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/native_init_flash.py \
  workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-readback-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-version v2321-usb-clean-identity-rodata \
  --verify-protocol cmdv1 \
  --from-native
```

Result:

- Remote pushed image SHA matched rollback SHA.
- Boot readback SHA matched rollback SHA.
- Post-rollback helper `version/status` verification passed.
- Final standalone `version` confirmed `v2321-usb-clean-identity-rodata`.
- A transient final selftest parse miss was cleared by restarting the serial bridge.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `__bitmap_set` as `live-proven` only under this contract:

- Static link identity: `0xffffff800855ce7c`, `export-recovery`, direct BL xrefs `24`.
- Trusted input contract: owned unsigned-long bitmap buffer plus scalar `start` and `len` bounded
  inside that bitmap.
- Observed result: zero-length no-op, low single-bit, low range, cross-word range, second-word range,
  and full-size range set; canary preserved.
- Cleanup: `kfree-owned-bitmap-set-buffer-ok`.

This does not authorize arbitrary bitmap pointers, negative or unbounded lengths, output aliases,
other bitmap mutation helpers, or mass calling.
