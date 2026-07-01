# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: cpu_mitigations_off

Date: 2026-07-01

- Decision: `a90-repl-live-call-proof-cpu_mitigations_off-pass`
- Scope: one-target live-call proof; boot partition only; rollback to `v2321`
- Target: `cpu_mitigations_off(void)`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-cpu-mitigations-off-20260701T082237Z/proof/a90_repl_evidence.json`
- Private timeline: `workspace/private/runs/kernel/live-call-proof-cpu-mitigations-off-20260701T082237Z/timeline.json`

## Target Selection

`cpu_mitigations_off` was selected from the remaining no-argument `cpu_*`
advisory candidates after excluding hotplug, teardown, startup, and
behavior-changing helpers. It is a CPU mitigation policy getter, not a CPU
state transition helper.

Trusted contract:

- No arguments.
- The target is the pinned leaf implementation that reads the global CPU
  mitigation policy enum and compares it with `0`.
- Return is a bool value, exactly `0` or `1`.
- Repeated values must stay stable in the short proof window.
- No returned pointer is dereferenced or freed.

## Static Gate

- Address: `cpu_mitigations_off=0xffffff80080b5cbc`.
- Resolution: `export-recovery`, C1 verified; map agrees with recovered export.
- Export candidate count: `1`.
- Direct BL xrefs: `4`.
- JOPP entry: yes.
- Leaf: yes; no in-body BL.
- Source declaration: `extern bool cpu_mitigations_off(void)` at
  `include/linux/cpu.h:216`.
- Note: the Samsung source drop exposes the declaration, while the live
  implementation identity is pinned by static disassembly and word checks.
- C1 safety tier after seeding: `SAFE-SCALAR`.
- Required valid pointer args: none.
- Next-symbol boundary: `cpu_mitigations_auto_nosmt` at `+0x18`.

Static word checks pinned the full leaf body and guard:

`0xb0012468 0xb9453108 0x7100011f 0x1a9f17e0 0xd65f03c0 0x00be7bad`

This decodes to the expected global-load, compare-with-zero, `cset w0, eq`,
and `ret` shape. The adjacent function begins at the pinned `+0x18`
boundary.

## Live Run

Flash gate:

- Rollback image `v2321`, deeper fallback `v2237`, final fallback `v48`, and
  TWRP recovery artifacts were present with expected SHA256 values before
  candidate flash.
- Baseline v2321 `version/status/selftest` passed before candidate flash.
- Candidate flash used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the candidate SHA.
- Candidate helper `version/status` verification passed after reboot.
- Candidate standalone `selftest` passed with `pass=11 warn=1 fail=0`.
- REPL selftest returned `a90-repl-v2a1-selftest-pass`.

Observed public values:

| Read | Return | Result |
| --- | ---: | --- |
| 1 | `0x0` | PASS |
| 2 | `0x0` | PASS |

Both returns were bool values and stable. Raw runtime values and the KASLR
slide are private-only and not committed.

Health and rollback:

- Post-proof candidate `selftest` passed with `pass=11 warn=1 fail=0`.
- Rollback to `v2321` used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the v2321 SHA.
- Rollback helper `version/status` verification passed.
- Final v2321 `version` reported `v2321-usb-clean-identity-rodata`.
- A first combined final health capture had serial echo noise during the
  selftest command. The standalone final v2321 `selftest` retry passed cleanly
  with `pass=11 warn=1 fail=0`.

## Timing

Timing was recorded in:

- `workspace/private/runs/kernel/live-call-proof-cpu-mitigations-off-20260701T082237Z/timeline.json`.

The timeline was finalized at `2026-07-01T08:27:10Z`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper total | `64.756s` |
| REPL selftest | `5.992s` |
| live proof | `5.642s` |
| rollback flash helper total | `63.699s` |

The helper total rows are retained for compatibility with prior reports and
are not additive. All serial bridge commands in this unit were run
sequentially except for a non-device host bridge-status check that overlapped
one final health capture and caused only the noted serial echo noise.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 tests/test_a90_repl.py CallSafetyClassificationTests SelftestIntegrationTests.test_call_proof_cpu_mitigations_off_passes_with_policy_bool_contract`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 tests/test_a90_repl.py SelftestIntegrationTests.test_call_proof_get_state_synchronize_rcu_passes_with_read_only_state_contract SelftestIntegrationTests.test_call_proof_cpu_mitigations_off_passes_with_policy_bool_contract SelftestIntegrationTests.test_call_proof_is_vmalloc_addr_passes_with_boundary_table_contract`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --no-objdump cpu_mitigations_off`
- `git diff --check`

Live validation:

- Candidate flash passed with matching candidate readback SHA.
- Candidate `selftest` and REPL selftest passed.
- `cpu_mitigations_off` live proof passed under the read-only CPU mitigation
  policy bool contract.
- Post-proof health passed.
- Rollback to v2321 passed with matching rollback readback SHA.
- Final v2321 `version` and standalone `selftest` passed.

## Function Map Entry

`cpu_mitigations_off` is live-proven only under this contract:

- Input: no arguments.
- Static body: pinned leaf global-load policy check, no BL before return.
- Return: bool value, exactly `0` or `1`, stable across the short repeated
  proof.
- Observed live result: `0x0`, `0x0`.
- Auto-call policy: proof target only, not a mass-call permission.
