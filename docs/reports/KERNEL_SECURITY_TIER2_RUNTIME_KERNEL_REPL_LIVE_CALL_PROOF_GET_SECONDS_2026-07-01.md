# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: get_seconds

Date: 2026-07-01

## Scope

- Target: `get_seconds`
- Device action: yes, boot partition only through `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence: `workspace/private/runs/kernel/live-call-proof-get-seconds-20260701/`.

## Static Gate

Host validation passed before live call:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and `tests/test_a90_repl.py`.
- Focused tests: classifier, source-signature, and fake live proof (`Ran 3 tests`, `OK`).
- Full `tests/test_a90_repl.py`: `Ran 168 tests`, `OK`.
- Classifier CLI over selected/parked candidates: `get_seconds` is `SAFE-SCALAR`; `get_host_os_type` and `get_pkey_press` remain `DENY`.

Static identity:

- `get_seconds=0xffffff800816185c`.
- Resolution method: `export-recovery`.
- Direct BL xrefs: `51`.
- Next symbol: `__current_kernel_time` at `+0x18`.
- Exact 6-word body match:
  `b0016fe8 912c0108 f9403500 d65f03c0 d503201f 00be7bad`.
- Source signature: `unsigned long get_seconds(void)` from `include/linux/timekeeping.h:26`.
- No pointer args, no pre-call argument pointer derefs, no returned pointer is dereferenced or freed.

## Live Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel \
  --timeout 90 \
  --dmesg-tail 80 \
  --safe-op-retries 5 \
  --retry-delay-sec 0.75 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-get-seconds-20260701/proof \
  get_seconds
```

Public result:

```json
{
  "decision": "a90-repl-live-call-proof-get_seconds-pass",
  "ok": true,
  "proof_status": "trusted-under-kernel-wall-clock-seconds-read-only-contract",
  "observed_return_value": "0x5a51e676",
  "repeat_count": 2,
  "all_returns_nondecreasing": true,
  "bounded_forward_deltas": true,
  "max_observed_delta": "0x1",
  "raw_runtime_values_redacted": true
}
```

Case table:

| Case | Expected | Observed | Delta | Result |
| --- | --- | ---: | ---: | --- |
| `get_seconds-read-1` | unsigned long seconds | `0x5a51e676` | `n/a` | PASS |
| `get_seconds-read-2` | nondecreasing, delta <= 2 seconds | `0x5a51e677` | `0x1` | PASS |

The private evidence includes the per-boot slide and runtime target address. These raw runtime values are intentionally absent from this public report.

## Timing

Timeline source: `workspace/private/runs/kernel/live-call-proof-get-seconds-20260701/result.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper | `63.673s` |
| candidate flash start to boot ready | `84.795s` |
| candidate boot/health to ready | `21.122s` |
| live proof session | `5.820s` |
| rollback flash helper | `65.264s` |
| rollback flash start to boot ready | `87.284s` |
| rollback boot/health to ready | `22.020s` |
| total candidate-start to rollback-ready | `178.345s` |

## Rollback And End State

Rollback to v2321 was performed through `native_init_flash.py` with pinned SHA and matching readback SHA. Final explicit bridge checks passed:

- `a90ctl.py --timeout 30 version`: v2321 clean identity baseline.
- `a90ctl.py --timeout 30 selftest`: `pass=11 warn=1 fail=0`.
- `a90ctl.py --timeout 30 status`: completed with `selftest fail=0`.

## Function Map Entry

```json
{
  "symbol": "get_seconds",
  "status": "live-proven",
  "trusted_input_contract": "no arguments; kernel timekeeping wall-clock seconds are read-only; no returned pointer is dereferenced or freed",
  "return_contract": "unsigned long seconds value is nondecreasing across immediate repeated proof calls and advances by at most 2 seconds",
  "observed_return_value": "repeated no-argument calls returned nondecreasing kernel wall-clock seconds starting at 0x5a51e676 with max short-run delta 0x1",
  "cleanup": "n/a-scalar-read-only",
  "auto_call_policy": "one-target-proof-only-not-mass-call"
}
```
