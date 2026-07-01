# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: slab_is_available

Date: 2026-07-01

- Decision: `a90-repl-live-call-proof-slab_is_available-pass`
- Scope: bounded live-call proof using `call-proof-batch`; boot partition only; rollback to `v2321`
- Target: `slab_is_available(void)`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-slab-is-available-20260701T091812Z/proof/a90_repl_evidence.json`
- Private result: `workspace/private/runs/kernel/live-call-proof-slab-is-available-20260701T091812Z/result.json`
- Private timeline: `workspace/private/runs/kernel/live-call-proof-slab-is-available-20260701T091812Z/timeline.json`

## Target Selection

The next post-steer unit followed the batch rule first. A slab-family sweep
checked adjacent candidates (`slab_*`, `kmem_cache_*`, `kfree_*`, `ksize`,
`kzfree`). The only read-only no-argument allocator-state candidate was
`slab_is_available()`. The nearby `kmem_cache_*` and `kfree_*` symbols are
allocation/free/init/RCU or pointer-mutating helpers and stayed out of the
proof. Therefore this run used the batch CLI with one safe target rather than
forcing an unsafe slab partner into the same boot session.

Trusted contract:

- No arguments.
- The target is the pinned leaf that reads global slab allocator state and
  compares it to the current image's availability threshold.
- Return is a bool value, exactly `0` or `1`.
- Repeated values must stay stable in the short proof window.
- No returned pointer is dereferenced or freed.

## Static Gate

- Address: `slab_is_available=0xffffff800823839c`.
- Resolution: `exact-leaf-map+xref+word-boundary`, verified true.
- Export candidate count: `0`.
- Direct BL xrefs: `16`.
- JOPP entry: yes.
- Source declaration: `bool slab_is_available(void)` at
  `include/linux/slab.h:122`.
- C1 safety tier after target-limited seeding: `SAFE-SCALAR`.
- Required valid pointer args: none.
- Next-symbol boundary: `kmalloc_slab` at `+0x18`.

Static word checks pinned the full body and guard:

`0xb0016968 0xb94ca908 0x7100091f 0x1a9f97e0 0xd65f03c0 0x00be7bad`

The generic 64-byte classifier scan includes `kmalloc_slab` after the boundary,
so the proof pins the 0x18-byte body directly rather than treating that broad
scan as the function body.

## Live Run

Flash gate:

- Rollback image `v2321`, deeper fallback `v2237`, final fallback `v48`, and
  TWRP recovery artifacts were present before candidate flash.
- Baseline v2321 `version/status/selftest` passed before candidate flash.
- Candidate flash used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the candidate SHA.
- Candidate helper `version/status` verification passed after reboot.
- The first explicit candidate `selftest` attempt hit serial `AT` echo / END
  marker loss. After bridge restart, candidate `selftest` passed with
  `pass=11 warn=1 fail=0`.
- REPL selftest returned `a90-repl-v2a1-selftest-pass`.

Observed public values:

| Read | Return | Result |
| --- | ---: | --- |
| 1 | `0x1` | PASS |
| 2 | `0x1` | PASS |

Both returns were bool values and stable. Raw runtime values and the KASLR
slide are private-only and not committed.

Health and rollback:

- Post-proof candidate `selftest` passed with `pass=11 warn=1 fail=0`.
- Rollback to `v2321` used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the v2321 SHA.
- Rollback helper `version/status` verification passed.
- The first standalone final `selftest` attempt hit serial END marker loss.
  After bridge restart, final v2321 standalone `selftest` passed with
  `pass=11 warn=1 fail=0`.
- Final bridge status was `connected-no-immediate-error`.

## Timing

Timing was recorded in:

- `workspace/private/runs/kernel/live-call-proof-slab-is-available-20260701T091812Z/timeline.json`.

The live proof started at `2026-07-01T09:18:12Z`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper total | `64.726s` |
| candidate selftest first attempt | marker loss at `10.062s` |
| candidate bridge restart | `2.315s` |
| candidate selftest retry | `0.294s` host-observed |
| REPL selftest | `5.852s` host-observed |
| live proof batch | `5.082s` host-observed |
| post-proof candidate selftest | `0.296s` host-observed |
| rollback flash helper total | `65.318s` |
| final selftest first attempt | marker loss at `10.085s` |
| final bridge restart + selftest + bridge status | `2.756s` host-observed |

The helper total rows are retained for compatibility with prior reports and
are not additive. All serial bridge operations in the accepted live path were
run sequentially.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 tests/test_a90_repl.py CallSafetyClassificationTests SelftestIntegrationTests.test_call_proof_slab_is_available_passes_with_allocator_availability_contract`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --no-objdump slab_is_available`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-proof-batch --help`

Live validation:

- Candidate flash passed with matching candidate readback SHA.
- Candidate `selftest` retry and REPL selftest passed.
- `call-proof-batch slab_is_available` passed in one REPL session.
- Post-proof health passed.
- Rollback to v2321 passed with matching rollback readback SHA.
- Final v2321 standalone `selftest` retry and bridge status passed.

## Function Map Entry

`slab_is_available` is live-proven only under this contract:

- Input: no arguments.
- Static body: pinned global-load/compare slab allocator availability leaf; ret
  before `kmalloc_slab`.
- Return: bool value, exactly `0` or `1`, stable across the short repeated
  proof.
- Observed live result: `0x1`, `0x1`.
- Auto-call policy: one-target proof only; no safe slab batch partner was
  available in this unit.
