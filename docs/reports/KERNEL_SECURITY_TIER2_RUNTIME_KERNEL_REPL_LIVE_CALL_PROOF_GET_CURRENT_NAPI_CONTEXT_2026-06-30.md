# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: get_current_napi_context

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-get_current_napi_context-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-get-current-napi-context-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit continued the scalar/no-pointer `get_*` sweep after `get_cpu_device` and selected
`get_current_napi_context` because it has no arguments, C1 recovered exactly one export candidate,
the verified System.map agreed with it, the source declaration is no-arg, and the expected REPL
process-context result is externally clear: no active NAPI poll context, so NULL.

Rejected alternatives in this pass:

- `get_debug_reset_header`: no arguments, but the body allocates, reads a debug partition, logs, and
  frees; the result contract is weaker and less isolated.
- `get_ddr_revision_id_1`, `get_ddr_revision_id_2`, `get_ddr_total_density`, and
  `get_ddr_vendor_name`: no arguments, but they call SMEM/logging paths and return device-specific
  hardware values; useful later, but weaker for a simple proof step.
- `get_boot_stat_time`: scalar/no-arg, but it calls logging machinery and has a weaker externally
  checkable return contract.

## Static Gate

Target:

- `get_current_napi_context`: `0xffffff800971f284`
- Resolution method: `export-recovery`
- Direct BL xrefs: `10`
- Next symbol boundary: `netdev_has_upper_dev` at `+0x20`
- Source signature: `include/linux/netdevice.h:3327`,
  `extern struct napi_struct * get_current_napi_context(void)`
- Source pointer contract: no arguments.
- Call-safety tier: `SAFE-SCALAR`
- Required valid pointer args: none.
- Static word checks:
  - `0xd0007fc9` ADRP for the per-CPU softnet-data region.
  - `0xd538d088` `mrs x8, tpidr_el1`.
  - `0x910c0129` softnet-data offset add.
  - `0x8b090108` per-CPU base add.
  - `0xf9400900` current-NAPI pointer load.
  - `0xd65f03c0` return.
  - `0xd503201f` padding NOP.
  - `0x00be7bad` next-entry guard before `netdev_has_upper_dev`.

The generic classifier scans 64 bytes and therefore sees the next function's first BL in its signal
sample; this proof gates the actual `0x20`-byte function boundary explicitly.

## Host Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_a90_repl.CallSafetyClassificationTests.test_proven_live_call_targets_stay_safe \
  tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args \
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_get_current_napi_context_passes_with_process_context_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  get_current_napi_context

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
```

Result:

- `py_compile`: pass.
- Focused tests: static classification, source signature, and fake-transport no-arg proof passed
  (`Ran 3 tests`, `OK`).
- CLI classify: `SAFE-SCALAR`, verified by `export-recovery`, direct-BL xrefs `10`, no required
  pointer args.
- Full `tests.test_a90_repl`: `Ran 144 tests`, `OK`.

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
- A transient candidate standalone selftest parse miss was cleared by restarting the serial bridge.
- Candidate standalone selftest returned `pass=11 warn=1 fail=0`.
- REPL selftest completed and returned `a90-repl-v2a1-selftest-pass`.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof get_current_napi_context \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-get-current-napi-context-20260630/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-get_current_napi_context-pass",
  "ok": true,
  "proof_status": "trusted-under-process-context-null-contract",
  "input_contract": "no arguments; called from REPL process context outside NAPI poll/softirq; returned pointer, if any, is borrowed/read-only and is not dereferenced or freed",
  "return_contract": "struct napi_struct * == NULL for the REPL process-context proof call",
  "all_returns_null": true,
  "repeat_count": 2,
  "raw_runtime_values_redacted": true,
  "borrowed_pointer_redacted": true
}
```

Case table:

| Case | Expected | Observed |
| --- | --- | --- |
| process-context-null-1 | NULL | `0x0` |
| process-context-null-2 | NULL | `0x0` |

Checks:

- `static-c1-identity`: OK, `get_current_napi_context` resolved by `export-recovery`.
- `static-next-symbol-boundary`: OK, next symbol at `+0x20`.
- `static-source-contract`: OK, no-arg source signature selected from `include/linux/netdevice.h`.
- `static-call-safety-contract`: OK, tier `SAFE-SCALAR`.
- Static word checks: OK for per-CPU base read, current-NAPI pointer load, return, padding, and next
  guard.
- Process-context NULL repeat table: OK.
- Cleanup: not applicable. No owned resource was created, and no pointer was returned.

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
- A transient final standalone `version` parse miss was cleared by restarting the serial bridge.
- Final standalone `version` confirmed `v2321-usb-clean-identity-rodata`.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `get_current_napi_context` as `live-proven` only under this contract:

- Static link identity: `0xffffff800971f284`, `export-recovery`, direct BL xrefs `10`, `0x20`-byte
  function body ending before `netdev_has_upper_dev`.
- Trusted input contract: no arguments; called from REPL process context outside NAPI poll/softirq;
  any non-NULL pointer would be borrowed/read-only and must not be dereferenced or freed.
- Observed result: two process-context calls returned NULL.
- Cleanup: `n/a-null-return-no-owned-resource`.

This does not authorize NAPI poll-context calls, dereferencing any future non-NULL returned pointer,
freeing the returned pointer, changing network state, or mass calling.
