# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: cpumask_next_and

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-cpumask_next_and-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-cpumask-next-and-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit continued the cpumask wrapper sweep after `cpumask_next`, `cpumask_any_but`, and
`cpumask_next_wrap`. `cpumask_next_and` was selected as the first two-owned-cpumask wrapper proof:
the function must return the next CPU greater than `n` that is set in both masks, or the runtime
`nr_cpu_ids` sentinel when no common set CPU remains.

The selected target is not trusted as a general cpumask facility. The proof creates two owned kernel
cpumask buffers, verifies the wrapper's compiled and runtime 8-CPU shape, calls a bounded case table,
checks the return table, re-peeks both cpumasks/canaries after every call, and frees both allocations.

## Static Gate

Target:

- `cpumask_next_and`: `0xffffff80099a9e44`
- Resolution method: `export-recovery`
- Direct BL xrefs: `88`
- Shape: JOPP entry, non-leaf wrapper, one BL to `find_next_bit`.
- Wrapper evidence:
  - `0x52800101` (`mov w1,#8`) for `nr_cpumask_bits`.
  - `0x97aeebee` for the pinned BL to `find_next_bit`.
  - `0xb940faa8` for the runtime `nr_cpu_ids` load.
  - `0xf868da68` for the second cpumask word load from x2/`andp`.
- Source signature: `include/linux/cpumask.h:216`,
  `int cpumask_next_and(int n, const struct cpumask *, const struct cpumask *)`
- Source pointer contract: x1 and x2 are `const struct cpumask *`; x0 is scalar.
- Call-safety tier: `SAFE-WITH-VALID-PTR`
- Required valid pointer args: x1 `cpumask-buffer`, x2 `cpumask-buffer`.

The target was not called with arbitrary numeric pointers. The proof requires two owned cpumask
buffers, scalar `n` values bounded to the proof table, compiled `nr_cpumask_bits=8`, and runtime
`nr_cpu_ids=8`.

## Host Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  cpumask_next_and

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_a90_repl.CallSafetyClassificationTests.test_proven_live_call_targets_stay_safe \
  tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args \
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_cpumask_next_and_passes_with_owned_cpumask_contract

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
```

Result:

- `py_compile`: pass.
- CLI classify: `SAFE-WITH-VALID-PTR`, verified by `export-recovery`, direct-BL xrefs `88`,
  non-leaf wrapper, required x1/x2 `cpumask-buffer`.
- Focused tests: static classification/source tests and the new fake-transport proof passed.
- Full `tests.test_a90_repl`: `Ran 135 tests`, `OK`.

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
  --from-native workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65 \
  --expect-readback-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65
```

Result:

- Remote pushed image SHA matched candidate SHA.
- Boot readback SHA matched candidate SHA.
- Post-flash `version/status` verification passed.
- Candidate standalone selftest returned `pass=11 warn=1 fail=0`.
- REPL selftest completed and returned `a90-repl-v2a1-selftest-pass`.

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
  --timeout 180 --dmesg-tail 80 --safe-op-retries 5 --retry-delay-sec 0.75 \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-cpumask-next-and-20260630/proof \
  cpumask_next_and
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-cpumask_next_and-pass",
  "ok": true,
  "proof_status": "trusted-under-owned-input-contract",
  "input_contract": "scalar int n + two owned cpumask buffers with compiled nr_cpumask_bits=8 and runtime nr_cpu_ids=8",
  "return_contract": "unsigned int == next CPU index greater than n that is set in both cpumasks, or runtime nr_cpu_ids when no common set CPU remains",
  "raw_runtime_values_redacted": true,
  "owned_pointer_redacted": true,
  "observed_bytes_redacted": true
}
```

Case table:

| Case | Src CPU bits | And CPU bits | n | Expected | Observed |
| --- | --- | --- | ---: | --- | --- |
| from-minus-one-skip-src-only | `1,3,6` | `3,6` | -1 | `0x3` | `0x3` |
| from-before-common | `1,3,6` | `3,6` | 2 | `0x3` | `0x3` |
| from-first-common | `1,3,6` | `3,6` | 3 | `0x6` | `0x6` |
| from-last-common | `1,3,6` | `3,6` | 6 | `0x8` | `0x8` |
| no-common-src-only | `1` | `3,6` | -1 | `0x8` | `0x8` |
| empty-src | empty | `3,6` | -1 | `0x8` | `0x8` |
| empty-and | `1,3,6` | empty | -1 | `0x8` | `0x8` |

Checks:

- `static-c1-identity`: OK, `cpumask_next_and` resolved by `export-recovery`.
- `static-source-contract`: OK, signature matches the source oracle and pointer arg indices are `[1,2]`.
- `static-call-safety-contract`: OK, tier `SAFE-WITH-VALID-PTR`, x1/x2 `cpumask-buffer`.
- `static-compiled-nr-cpumask-bits`: OK, wrapper word `0x52800101` matched compiled 8-bit mask.
- `static-find-next-bit-call`: OK, wrapper BL word `0x97aeebee` matched the pinned call target.
- `static-nr-cpu-ids-load`: OK, wrapper word `0xb940faa8` matched the runtime `nr_cpu_ids` load.
- `static-andp-word-load`: OK, wrapper word `0xf868da68` matched the x2/`andp` word load.
- `static-nr-cpu-ids-initial-value`: OK, static `nr_cpu_ids=8`.
- `runtime-nr-cpu-ids`: OK, runtime `nr_cpu_ids=8`.
- `kmalloc-owned-cpumask-next-and-src-mask`: OK, owned kernel src cpumask allocation returned sane lowmem.
- `kmalloc-owned-cpumask-next-and-and-mask`: OK, owned kernel and cpumask allocation returned sane lowmem.
- `cpumask-next-and-case-table`: OK, all 7 calls returned expected CPU indices or sentinel `8`.
- Per-case immutability: OK, src/and cpumasks and canaries stayed unchanged after every call.
- `kfree-owned-cpumask-next-and-src-mask`: OK.
- `kfree-owned-cpumask-next-and-and-mask`: OK.

Raw per-boot slide, target runtime address, runtime `nr_cpu_ids` address, owned allocation pointers,
and observed bytes were written only to private evidence and are not included in this report.

Candidate selftest after proof: `pass=11 warn=1 fail=0`.

## Rollback

Rollback command:

```sh
python3 workspace/public/src/scripts/revalidation/native_init_flash.py \
  --from-native workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img \
  --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb \
  --expect-readback-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
```

Result:

- Remote pushed image SHA matched rollback SHA.
- Boot readback SHA matched rollback SHA.
- Post-rollback `version/status` verification passed.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `cpumask_next_and` as `live-proven` only under this contract:

- Static link identity: `0xffffff80099a9e44`, `export-recovery`, direct BL xrefs `88`.
- Trusted input contract: scalar int `n`, two owned cpumask buffers with compiled
  `nr_cpumask_bits=8`, and runtime `nr_cpu_ids=8`.
- Observed result: src-only bit skip, common-bit hits after `n`, last-common sentinel,
  no-common sentinel, empty-src sentinel, and empty-and sentinel cases.
- Cleanup: `kfree-owned-cpumask-next-and-masks-ok`.

This does not authorize arbitrary cpumask pointers, wider CPU masks, other cpumask wrappers,
arbitrary iteration states, or mass calling.
