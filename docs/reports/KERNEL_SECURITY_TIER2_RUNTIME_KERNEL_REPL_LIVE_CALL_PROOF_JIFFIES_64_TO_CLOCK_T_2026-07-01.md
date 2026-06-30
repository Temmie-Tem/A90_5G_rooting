# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: jiffies_64_to_clock_t

- Date: 2026-07-01
- Decision: `a90-repl-live-call-proof-jiffies_64_to_clock_t-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-jiffies64-to-clock-20260701/proof/a90_repl_evidence.json`

## Candidate Selection

This unit selected `jiffies_64_to_clock_t` from the host-only time/jiffies scalar sweep. The sweep
also surfaced `jiffies_to_clock_t`, `jiffies_to_msecs`, `jiffies_to_usecs`, `ktime_add_safe`,
`ktime_get_seconds`, `ktime_get_real_seconds`, `nsecs_to_jiffies64`, and `nsecs_to_jiffies`.

`jiffies_64_to_clock_t` was chosen because it is scalar-only, C1-verified by `export-recovery`, and
the current image compiles it to a two-word identity leaf: `ret` followed by the next-entry guard. The
trusted contract is intentionally narrow: fixed u64 inputs are expected to return unchanged on this
image. Adjacent conversion helpers and non-identity build configurations remain unpromoted until
separate contracts are proven.

## Static Gate

Target:

- `jiffies_64_to_clock_t`: `0xffffff800815858c`
- Resolution method: `export-recovery`
- Direct BL xrefs: `3`
- Next symbol boundary: `nsec_to_clock_t` at `+0x8`
- Source declaration: `include/linux/jiffies.h:451`,
  `extern u64 jiffies_64_to_clock_t(u64 x)`
- Source pointer contract: no pointer arguments.
- Call-safety tier: `SAFE-SCALAR`
- Required valid pointer args: none.
- Static word checks:
  - `0xd65f03c0` identity `ret`.
  - `0x00be7bad` next-entry guard before `nsec_to_clock_t`.

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
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_jiffies_64_to_clock_t_passes_with_identity_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  jiffies_64_to_clock_t

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl

git diff --check
```

Result:

- `py_compile`: pass.
- Focused tests: `Ran 4 tests`, `OK`.
- CLI classify: `SAFE-SCALAR`, verified by `export-recovery`, direct BL xrefs `3`, no required
  pointer args, first words `0xd65f03c0` and `0x00be7bad`.
- Full `tests.test_a90_repl`: `Ran 149 tests`, `OK`.
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
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof jiffies_64_to_clock_t \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-jiffies64-to-clock-20260701/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-jiffies_64_to_clock_t-pass",
  "ok": true,
  "proof_status": "trusted-under-fixed-u64-identity-contract",
  "input_contract": "scalar u64 jiffies value; no pointer args; current image leaf body is identity conversion",
  "return_contract": "u64 clock_t value equals the scalar input for fixed proof cases",
  "all_returns_match_input": true,
  "case_count": 3,
  "raw_runtime_values_redacted": true
}
```

Case table:

| Case | Input | Expected | Observed |
| --- | --- | --- | --- |
| jiffies64-to-clock-identity-zero | `0x0` | `0x0` | `0x0` |
| jiffies64-to-clock-identity-one | `0x1` | `0x1` | `0x1` |
| jiffies64-to-clock-identity-mixed-u64 | `0x123456789abcdef0` | `0x123456789abcdef0` | `0x123456789abcdef0` |

Checks:

- `static-c1-identity`: OK, `jiffies_64_to_clock_t` resolved by `export-recovery`.
- `static-next-symbol-boundary`: OK, next symbol at `+0x8`.
- `static-source-contract`: OK, scalar-only `extern u64 jiffies_64_to_clock_t(u64 x)` source
  declaration selected from `include/linux/jiffies.h`.
- `static-call-safety-contract`: OK, tier `SAFE-SCALAR`.
- Static word checks: OK for identity `ret` and next guard.
- Fixed u64 identity cases: OK; all three returns matched their scalar input exactly.
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
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Function Map Update

Add `jiffies_64_to_clock_t` as `live-proven` only under this contract:

- Static link identity: `0xffffff800815858c`, `export-recovery`, direct BL xrefs `3`, `0x8`-byte
  identity leaf before `nsec_to_clock_t`.
- Trusted input contract: scalar `u64` jiffies value; current image leaf body is identity conversion;
  no pointer args.
- Observed result: fixed cases `0x0`, `0x1`, and `0x123456789abcdef0` returned unchanged.
- Cleanup: `n/a-scalar-only`.

This does not authorize adjacent conversion helpers, timer rounding helpers, non-identity build
configurations, or mass calling.
