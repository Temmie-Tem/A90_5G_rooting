# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: get_boot_stat_time

- Date: 2026-06-30
- Decision: `a90-repl-live-call-proof-get_boot_stat_time-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-get-boot-stat-time-20260630/proof/a90_repl_evidence.json`

## Candidate Selection

This unit selected `get_boot_stat_time` from the host-only `get_` prefix sweep. It was the only new
advisory `SAFE-SCALAR` candidate in that sweep, but it was not promoted directly from sweep output:
the contract was narrowed to a no-argument read-only MMIO counter proof, with the implementation body
and disassembly shape gated before any live call.

The adjacent `get_boot_stat_freq` remains unpromoted because C1 still marks its tiny leaf body as
unverified (`map-target-no-helper-call-before-return-or-scan-limit`). `get_boot_stat_time` is stronger
for this unit because C1 resolves it by `disasm-signature+xref+map` and the body has a helper call
anchor before returning.

## Static Gate

Target:

- `get_boot_stat_time`: `0xffffff80086979e4`
- Resolution method: `disasm-signature+xref+map`
- Direct BL xrefs: `4`
- Next symbol boundary: `get_boot_stat_freq` at `+0x60`
- Source declaration: `include/soc/qcom/boot_stats.h:39`,
  `extern unsigned int get_boot_stat_time(void)`
- Source implementation: `drivers/soc/qcom/boot_stats.c`,
  `unsigned int get_boot_stat_time(void) { return readl_relaxed(mpm_counter_base); }`
- Source pointer contract: no arguments.
- Call-safety tier: `SAFE-SCALAR`
- Required valid pointer args: none.
- Static word checks:
  - `0xa9be43fd` stack allocation.
  - `0xf9000bf3` x19 save.
  - `0xd0015088` counter-base page setup.
  - `0x52800020` `uncached_logk` mode argument.
  - `0xf9401d13` counter-base load.
  - `0xaa1303e1` counter-base argument setup.
  - `0x97ecd440` call to `uncached_logk`.
  - `0x34000120` branch on `uncached_logk` zero result.
  - `0xb9400260` counter load on both read paths.
  - `0xd5033f9f` / `0xd5033fdf` barrier path.
  - `0xf9400bf3` x19 restore.
  - `0xd65f03c0` return.
  - `0x00be7bad` next-entry guard before `get_boot_stat_freq`.

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
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_get_boot_stat_time_passes_with_bounded_counter_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  get_boot_stat_time

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl

git diff --check
```

Result:

- `py_compile`: pass.
- Focused tests: `Ran 4 tests`, `OK`.
- CLI classify: `SAFE-SCALAR`, verified by `disasm-signature+xref+map`, direct-BL xrefs `4`, no
  required pointer args, and first BL resolved to `uncached_logk`.
- Full `tests.test_a90_repl`: `Ran 147 tests`, `OK`.
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
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof get_boot_stat_time \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-get-boot-stat-time-20260630/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-get_boot_stat_time-pass",
  "ok": true,
  "proof_status": "trusted-under-boot-stat-time-read-only-counter-contract",
  "input_contract": "no arguments; Qualcomm boot-stat timer MMIO is read-only; no returned pointer is dereferenced or freed",
  "return_contract": "unsigned int boot-stat timer value is nonzero uint32_t and advances by a bounded short-run delta across repeated proof calls",
  "all_returns_nonzero_uint32": true,
  "bounded_forward_deltas": true,
  "has_positive_delta": true,
  "repeat_count": 3,
  "observed_return_value": "0x29eb84",
  "max_observed_delta": "0x4254",
  "raw_runtime_values_redacted": true
}
```

Case table:

| Case | Expected | Observed | Delta |
| --- | --- | --- | --- |
| boot-stat-time-read-1 | nonzero uint32 bounded counter | `0x29eb84` | n/a |
| boot-stat-time-read-2 | nonzero uint32 bounded counter | `0x2a2dac` | `0x4228` |
| boot-stat-time-read-3 | nonzero uint32 bounded counter | `0x2a7000` | `0x4254` |

Checks:

- `static-c1-identity`: OK, `get_boot_stat_time` resolved by `disasm-signature+xref+map`.
- `static-next-symbol-boundary`: OK, next symbol at `+0x60`.
- `static-source-contract`: OK, no-arg `unsigned int` source declaration selected from
  `include/soc/qcom/boot_stats.h`.
- `static-source-implementation`: OK, implementation returns `readl_relaxed(mpm_counter_base)`.
- `static-call-safety-contract`: OK, tier `SAFE-SCALAR`.
- Static word checks: OK for counter-base setup, `uncached_logk`, both counter loads, barriers,
  restore, RET, and next guard.
- Repeated counter table: OK; all returns were nonzero uint32 values, all deltas were below
  `10000000` ticks, and at least one positive delta was observed.
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

Add `get_boot_stat_time` as `live-proven` only under this contract:

- Static link identity: `0xffffff80086979e4`, `disasm-signature+xref+map`, direct BL xrefs `4`,
  `0x60`-byte body before `get_boot_stat_freq`.
- Trusted input contract: no arguments; Qualcomm boot-stat timer MMIO is read-only; no returned
  pointer is dereferenced or freed.
- Observed result: three repeated calls returned nonzero uint32 counter values starting at
  `0x29eb84`, with max short-run delta `0x4254`.
- Cleanup: `n/a-scalar-mmio-read-only`.

This does not authorize arbitrary MMIO reads, changing boot-stat state, adjacent tiny-leaf
`get_boot_stat_freq`, or mass calling.
