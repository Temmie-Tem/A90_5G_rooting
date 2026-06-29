# KERNEL SECURITY Tier-2 Runtime Kernel REPL U3 Gate-2 Source Oracle Fix

Date: 2026-06-29

Scope: host-only correction to the U3 advisory `call-safety-sweep` source oracle and candidate filtering. No device action, no live calls, no flash, no boot-image change, no network dependency.

## Gate-2 Findings Addressed

1. Source candidate orchestration now prioritizes relevant declarations.
   - `_source_candidate_files()` still records all matching source files, but sorts subsystem declarations first.
   - `lookup_source_signature()` records `found`, `has_pointer_arg`, top-level `pointer_arg_indices`, `candidate_file_count`, and `candidate_files_sample` for debugging.
   - `ksize` now resolves to `include/linux/slab.h:153`, `size_t ksize(const void *)`, with `found=true` and `has_pointer_arg=true`.

2. Source `__init` / `__exit` annotations are danger flags.
   - `kmem_cache_init` resolves to `include/linux/slab.h:121`, `void __init kmem_cache_init(void)`.
   - Advisory flags include `source-__init-annotation`.
   - `candidate_safe=false`.

3. Non-seeded arg-memory-flow consumers are no longer advisory candidates without a vetted gate pointer contract.
   - `kfree_skb_partial` has `arg_memory_base_use_count=3`.
   - It is non-seeded and has no gate pointer contract.
   - Advisory flags include `unseeded-arg-memory-flow-without-gate-pointer-contract`.
   - `candidate_safe=false`.

## Re-sweep Evidence

Allocator family:

- Command: `call-safety-sweep --family allocator --limit 80 --no-objdump`
- Result: `decision=a90-repl-u3-call-safety-sweep-host-pass`
- Rows: 28
- `candidate_safe_count=3`
- `host_only=true`, `device_action=false`, `network_dependency=false`
- `ksize`: source found, pointer arg detected, selected `include/linux/slab.h:153`, advisory `SAFE-WITH-VALID-PTR`
- `kmem_cache_init`: source found, `source-__init-annotation`, `candidate_safe=false`
- `kfree_skb_partial`: source found, `arg_memory_base_use_count=3`, `unseeded-arg-memory-flow-without-gate-pointer-contract`, `candidate_safe=false`

Read-I/O family:

- Command: `call-safety-sweep --family read-io --limit 40 --no-objdump`
- Result: `decision=a90-repl-u3-call-safety-sweep-host-pass`
- Rows: 40
- `candidate_safe_count=10`
- `host_only=true`, `device_action=false`, `network_dependency=false`
- Seeded pointer-contract examples `kernel_read` and `filp_open` retain source evidence from `include/linux/fs.h`.

## Validation

Commands run:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl.CallSafetyClassificationTests
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-sweep --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel --no-objdump --family allocator --limit 80
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-sweep --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel --no-objdump --family read-io --limit 40
```

Results:

- `py_compile`: PASS
- `CallSafetyClassificationTests`: 12/12 PASS
- Full `tests.test_a90_repl`: 62/62 PASS
- Allocator re-sweep: PASS
- Read-I/O re-sweep: PASS

## Safety Notes

The firewall remains intact: sweep output is advisory, does not mutate `CALL_SAFETY_SEEDS`, and does not widen the runtime `call` gate. No device, bridge, flash helper, boot image, live call, or network path was touched.
