# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: is_sde_rsc_available

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-is_sde_rsc_available-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-is-sde-rsc-available-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit selected `is_sde_rsc_available` from a host-only scalar candidate pass after the already
proven `CALL_PROOF_TARGETS` set was saturated. The contract was deliberately narrowed to
`SDE_RSC_INDEX` `0` only: no arbitrary indices, no adjacent display-RSC getters, no mutation, and no
use of any returned pointer capability.

Rejected candidates in the same pass:

- `is_scm_armv8`: rejected because the disassembly includes an SMC/cache-miss path and a static write,
  so it is not a clean read-only scalar proof target.
- `is_current_pgrp_orphaned`: rejected because it takes locks and traverses process state.
- `find_vpid`: rejected despite export/C1 visibility because it is a broader borrowed-pid lookup
  surface and needs a separate RCU/lifetime contract.

## Static Gate

Target:

- `is_sde_rsc_available`: `0xffffff8008861b04`
- Resolution method: `export-recovery`
- Direct BL xrefs: `1`
- Next symbol boundary: `get_sde_rsc_primary_crtc` at `+0x78`
- Source declaration: `include/linux/sde_rsc.h:282`,
  `bool is_sde_rsc_available(int rsc_index)`
- Source pointer contract: no pointer arguments.
- Call-safety tier: `SAFE-SCALAR`
- Required valid pointer args: none.
- Fixed input: `SDE_RSC_INDEX` `0`.
- Static word checks:
  - `0xca1103d0` JOPP entry.
  - `0xa9bf43fd` stack setup.
  - `0x2a0003e3` move scalar index into the checked register.
  - `0x7100141f` compare index against the valid upper bound.
  - `0x540000ab` branch to the valid-index path.
  - `0x90014348` display-RSC table page setup.
  - `0x91014108` display-RSC table address setup.
  - `0xf863d908` indexed table load.
  - `0xb40000a8` NULL branch.
  - `0x52800020` true return value.
  - `0x97e364a7` false-path `printk`.
  - `0x2a1f03e0` false return value.
  - `0xd65f03c0` return.
  - `0xd503201f` padding NOP.
  - `0x00be7bad` next-entry guard before `get_sde_rsc_primary_crtc`.

## Host Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_a90_repl.CallSafetyClassificationTests.test_proven_live_call_targets_stay_safe \
  tests.test_a90_repl.CallSafetyClassificationTests.test_seed_inventory_summary_counts_tiers \
  tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args \
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_is_sde_rsc_available_passes_with_index0_bool_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  is_sde_rsc_available

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl

git diff --check
```

Result:

- `py_compile`: pass.
- Focused tests: `Ran 4 tests`, `OK`.
- CLI classify: `SAFE-SCALAR`, verified by `export-recovery`, no required pointer args.
- Full `tests.test_a90_repl`: `Ran 148 tests`, `OK`.
- `git diff --check`: pass.

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
- A transient serial parse fragment was cleared by restarting the serial bridge.
- Candidate standalone selftest returned `pass=11 warn=1 fail=0`.
- REPL selftest completed and returned `a90-repl-v2a1-selftest-pass`.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof is_sde_rsc_available \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-is-sde-rsc-available-20260630/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-is_sde_rsc_available-pass",
  "ok": true,
  "proof_status": "trusted-under-sde-rsc-index0-bool-contract",
  "input_contract": "scalar rsc_index fixed to SDE_RSC_INDEX 0; display RSC table is read-only; no returned pointer is dereferenced or freed",
  "return_contract": "bool availability value is either 0 or 1 and stable across repeated proof calls",
  "all_returns_bool": true,
  "all_returns_stable": true,
  "repeat_count": 2,
  "observed_return_value": "0x1",
  "raw_runtime_values_redacted": true
}
```

Case table:

| Case | Input | Expected | Observed |
| --- | --- | --- | --- |
| sde-rsc-index0-available-1 | `0` | stable bool | `0x1` |
| sde-rsc-index0-available-2 | `0` | stable bool matching first call | `0x1` |

Checks:

- `static-c1-identity`: OK, `is_sde_rsc_available` resolved by `export-recovery`.
- `static-next-symbol-boundary`: OK, next symbol at `+0x78`.
- `static-source-contract`: OK, scalar-only `bool is_sde_rsc_available(int rsc_index)` source
  declaration selected from `include/linux/sde_rsc.h`.
- `static-call-safety-contract`: OK, tier `SAFE-SCALAR`.
- Static word checks: OK for index bound check, display-RSC table address/load, NULL branch, true
  return, false-path `printk`, false return, RETs, padding, and next guard.
- Repeated bool table: OK; both calls used index `0`, both returns were bool values, and both
  matched at `0x1`.
- Cleanup: not applicable. No owned resource was created, and no returned pointer exists.

Raw per-boot slide and target runtime address were written only to private evidence and are not
included in this report.

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
- A transient final serial parse fragment was cleared by restarting the serial bridge.
- Final standalone `version` confirmed `v2321-usb-clean-identity-rodata`.
- Final standalone `status` returned OK.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `is_sde_rsc_available` as `live-proven` only under this contract:

- Static link identity: `0xffffff8008861b04`, `export-recovery`, direct BL xrefs `1`,
  `0x78`-byte body before `get_sde_rsc_primary_crtc`.
- Trusted input contract: scalar `rsc_index` fixed to `SDE_RSC_INDEX` `0`; display RSC table is
  read-only; no returned pointer is dereferenced or freed.
- Observed result: two repeated calls returned stable bool `0x1`.
- Cleanup: `n/a-scalar-read-only`.

This does not authorize negative or arbitrary indices, adjacent display-RSC getters, display/RSC
mutation, or mass calling.
