# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: jiffies_to_usecs

- Date: 2026-07-01
- Decision: `a90-repl-live-call-proof-jiffies_to_usecs-pass`
- Scope: separately gated one-target live-call proof after the REPL epic close.
- Device action: yes, boot partition only through `native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-jiffies-to-usecs-20260701/proof/a90_repl_evidence.json`

## Candidate Selection

This unit selected `jiffies_to_usecs` from the host-only time/jiffies scalar sweep. The adjacent
`jiffies_to_msecs` helper is also arithmetically simple, but the current source-signature oracle
selected it with nearby macro text attached, so it stayed parked until that source contract can be
made cleaner. `jiffies_to_usecs` had a clean scalar-only declaration and a small, auditable current
image body.

The trusted contract is intentionally narrow: bounded unsigned long inputs whose product
`j * 10000` fits in unsigned int should return exactly that unsigned int value on this image.

## Static Gate

Target:

- `jiffies_to_usecs`: `0xffffff8008158164`
- Resolution method: `export-recovery`
- Direct BL xrefs: `25`
- Next symbol boundary: `timespec_trunc` at `+0x10`
- Source declaration: `include/linux/jiffies.h:292`,
  `extern unsigned int jiffies_to_usecs(const unsigned long j)`
- Source pointer contract: no pointer arguments.
- Call-safety tier: `SAFE-SCALAR`
- Required valid pointer args: none.
- Static word checks:
  - `0x5284e208`: load multiplier `10000`.
  - `0x1b087c00`: multiply into `w0`.
  - `0xd65f03c0`: return.
  - `0x00be7bad`: next-entry guard before `timespec_trunc`.

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
  tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_jiffies_to_usecs_passes_with_bounded_multiply_contract

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --no-objdump \
  jiffies_to_usecs

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl

git diff --check
```

Result:

- `py_compile`: pass.
- Focused tests: `Ran 4 tests`, `OK`.
- CLI classify: `SAFE-SCALAR`, verified by `export-recovery`, direct BL xrefs `25`, no required
  pointer args, first words `0x5284e208`, `0x1b087c00`, `0xd65f03c0`, and `0x00be7bad`.
- Full `tests.test_a90_repl`: `Ran 151 tests`, `OK`.
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
- Baseline before flash: v2321 `version` OK, `status` OK, `selftest pass=11 warn=1 fail=0`.

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
- First REPL selftest attempt hit a serial parse miss while setting `panic_on_oops`; the bounded
  retry completed and returned `a90-repl-v2a1-selftest-pass`.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof jiffies_to_usecs \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-jiffies-to-usecs-20260701/proof
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-jiffies_to_usecs-pass",
  "ok": true,
  "proof_status": "trusted-under-bounded-unsigned-long-multiply-by-10000-contract",
  "input_contract": "scalar unsigned long jiffies value bounded so j * 10000 fits in unsigned int; no pointer args",
  "return_contract": "unsigned int usec value equals j * 10000 for fixed proof cases",
  "all_returns_match_expected": true,
  "case_count": 4,
  "raw_runtime_values_redacted": true
}
```

Case table:

| Case | Input | Expected | Observed |
| --- | --- | --- | --- |
| jiffies-to-usecs-mul10000-zero | `0x0` | `0x0` | `0x0` |
| jiffies-to-usecs-mul10000-one | `0x1` | `0x2710` | `0x2710` |
| jiffies-to-usecs-mul10000-small-123 | `0x7b` | `0x12c4b0` | `0x12c4b0` |
| jiffies-to-usecs-mul10000-uint-boundary | `0x68db8` | `0xffffe380` | `0xffffe380` |

Checks:

- `static-c1-identity`: OK, `jiffies_to_usecs` resolved by `export-recovery`.
- `static-next-symbol-boundary`: OK, next symbol `timespec_trunc` at `+0x10`.
- `static-source-contract`: OK, scalar-only `extern unsigned int jiffies_to_usecs(const unsigned long j)`
  source declaration selected from `include/linux/jiffies.h`.
- `static-call-safety-contract`: OK, tier `SAFE-SCALAR`.
- Static word checks: OK for multiplier load, multiply, return, and next guard.
- Fixed bounded multiply cases: OK; all four returns matched `j * 10000`.
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

- Remote pushed rollback image SHA matched rollback SHA.
- Boot readback SHA matched rollback SHA.
- Helper `version/status` verification passed after reboot.
- First final standalone selftest read hit a serial parse miss after printing `pass=11 warn=1 fail=0`;
  the sequential retry captured the END marker and confirmed `pass=11 warn=1 fail=0`.

## Trust Boundary

`jiffies_to_usecs` is trusted only under the current-image bounded unsigned long multiply-by-10000
contract. This does not authorize `jiffies_to_msecs`, `nsecs_to_jiffies*`, overflow cases, alternate
timer configurations where the conversion body differs, or mass calling.
