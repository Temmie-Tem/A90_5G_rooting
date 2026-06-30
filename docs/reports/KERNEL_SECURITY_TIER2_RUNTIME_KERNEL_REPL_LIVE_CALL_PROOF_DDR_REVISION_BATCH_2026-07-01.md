# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: DDR Revision Batch

Date: 2026-07-01

## Scope

- Targets: `get_ddr_revision_id_1`, `get_ddr_revision_id_2`.
- Device action: yes, boot partition only through
  `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`.
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`.
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Private evidence:
  `workspace/private/runs/kernel/live-call-proof-ddr-revision-batch-20260630T224417Z/`.

This unit supersedes the earlier one-target `get_ddr_revision_id_1` failure by using the
current-image raw return contract shown by disassembly: the REPL captures the raw x0 value, while the
source-level `uint8_t` revision is the low byte of that stable raw value.

## Static Gate

Host validation passed before live call:

- `py_compile` for `workspace/public/src/scripts/revalidation/a90_repl.py` and `tests/test_a90_repl.py`.
- Focused classifier/source/seed/fake-batch tests: `Ran 4 tests`, `OK`.
- Full `tests/test_a90_repl.py`: `Ran 170 tests`, `OK`.
- Classifier CLI over the selected targets: both `get_ddr_revision_id_1` and
  `get_ddr_revision_id_2` are `SAFE-SCALAR`.
- `git diff --check`: clean.

Static identities:

| Target | Link VA | Method | Xrefs | Boundary | Source Contract |
| --- | ---: | --- | ---: | --- | --- |
| `get_ddr_revision_id_1` | `0xffffff80086ef82c` | `disasm-signature+xref+map` | `1` | `get_ddr_revision_id_2 +0xc0` | `extern uint8_t get_ddr_revision_id_1(void)` |
| `get_ddr_revision_id_2` | `0xffffff80086ef8ec` | `disasm-signature+xref+map` | `1` | `get_ddr_total_density +0xb8` | `extern uint8_t get_ddr_revision_id_2(void)` |

Both targets have no pointer arguments and no pre-call argument pointer dereferences. The proof gates
the current-image SMEM getter body words, including the `qcom_smem_get` BL, field load, null-return
path, return instruction, and next-symbol guard. `get_ddr_revision_id_1` additionally gates the
`lsr/ubfx` style return transform that explains the earlier raw `0x60106` value.

## Live Proof

Passing command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/a90_repl.py call-proof-batch \
  --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
  --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
  --timeout 180 \
  --dmesg-tail 80 \
  --safe-op-retries 5 \
  --retry-delay-sec 0.75 \
  --evidence-dir workspace/private/runs/kernel/live-call-proof-ddr-revision-batch-20260630T224417Z/proof_batch \
  get_ddr_revision_id_1 get_ddr_revision_id_2
```

Public batch result:

```json
{
  "decision": "a90-repl-live-call-proof-batch-pass",
  "ok": true,
  "target_count": 2,
  "completed_targets": ["get_ddr_revision_id_1", "get_ddr_revision_id_2"],
  "host_batch_single_repl_session": true,
  "raw_runtime_values_redacted": true
}
```

Case table:

| Target | Case | Expected | Observed raw | Source-level low8 | Result |
| --- | --- | --- | ---: | ---: | --- |
| `get_ddr_revision_id_1` | read 1 | stable nonzero 24-bit shifted SMEM revision word | `0x60106` | `0x6` | PASS |
| `get_ddr_revision_id_1` | read 2 | same raw value and same low byte | `0x60106` | `0x6` | PASS |
| `get_ddr_revision_id_2` | read 1 | stable nonzero 16-bit SMEM revision halfword | `0x601` | `0x1` | PASS |
| `get_ddr_revision_id_2` | read 2 | same raw value and same low byte | `0x601` | `0x1` | PASS |

The private evidence includes per-boot slide and runtime target addresses. These raw runtime values
are intentionally absent from this public report.

## Timing

Timeline source:

- `workspace/private/runs/kernel/live-call-proof-ddr-revision-batch-20260630T224417Z/timeline.json`.

Wrapper timeline:

| Phase | Elapsed |
| --- | ---: |
| candidate flash start to helper done | `64.221s` |
| candidate flash start to explicit boot ready | `64.669s` |
| candidate explicit health command total | `1.156s` |
| REPL selftest | `185.924s` |
| live batch proof | `9.265s` |
| live session total | `195.194s` |
| rollback flash start to helper done | `64.849s` |
| rollback flash start to explicit boot ready | `65.257s` |
| final explicit health command total | `1.089s` |
| candidate start to rollback ready | `325.836s` |

Candidate helper phase timings:

| Phase | Elapsed |
| --- | ---: |
| `inspect_local_image` | `0.034s` |
| `native_to_recovery` | `0.303s` |
| `wait_recovery_adb` | `28.126s` |
| `adb_push` | `0.852s` |
| `remote_sha256` | `0.106s` |
| `boot_dd_write` | `0.442s` |
| `boot_readback_sha256` | `0.345s` |
| `flash_boot_image` | `1.745s` |
| `reboot_twrp_to_system` | `2.355s` |
| `verify_native_init` | `31.549s` |
| `total` | `64.171s` |

Rollback helper phase timings:

| Phase | Elapsed |
| --- | ---: |
| `inspect_local_image` | `0.057s` |
| `native_to_recovery` | `0.303s` |
| `wait_recovery_adb` | `28.132s` |
| `adb_push` | `0.842s` |
| `remote_sha256` | `0.107s` |
| `boot_dd_write` | `0.441s` |
| `boot_readback_sha256` | `0.353s` |
| `flash_boot_image` | `1.743s` |
| `reboot_twrp_to_system` | `2.329s` |
| `verify_native_init` | `32.179s` |
| `total` | `64.803s` |

## Rollback And End State

Rollback to v2321 was performed through `native_init_flash.py` with pinned SHA and matching readback
SHA. Final explicit bridge checks passed:

- `a90ctl.py version`: `v2321-usb-clean-identity-rodata`.
- `a90ctl.py selftest`: `pass=11 warn=1 fail=0`.
- `a90ctl.py status`: completed with `selftest pass=11 warn=1 fail=0`.

## Function Map Entries

```json
[
  {
    "symbol": "get_ddr_revision_id_1",
    "status": "live-proven",
    "trusted_input_contract": "no arguments; Samsung SMEM DDR revision info is read-only; no returned pointer is dereferenced or freed",
    "return_contract": "current-image raw return is a stable nonzero 24-bit shifted SMEM revision word; the source-level uint8_t revision id is the stable low byte of that raw return",
    "observed_return_value": "repeated calls returned stable raw shifted-smem-revision-word 0x60106; source-level low8 revision byte 0x6",
    "cleanup": "n/a-scalar-smem-read-only",
    "auto_call_policy": "same-session-batch-proof-only-not-mass-call"
  },
  {
    "symbol": "get_ddr_revision_id_2",
    "status": "live-proven",
    "trusted_input_contract": "no arguments; Samsung SMEM DDR revision info is read-only; no returned pointer is dereferenced or freed",
    "return_contract": "current-image raw return is a stable nonzero 16-bit SMEM revision halfword; the source-level uint8_t revision id is the stable low byte of that raw return",
    "observed_return_value": "repeated calls returned stable raw smem-revision-halfword 0x601; source-level low8 revision byte 0x1",
    "cleanup": "n/a-scalar-smem-read-only",
    "auto_call_policy": "same-session-batch-proof-only-not-mass-call"
  }
]
```
