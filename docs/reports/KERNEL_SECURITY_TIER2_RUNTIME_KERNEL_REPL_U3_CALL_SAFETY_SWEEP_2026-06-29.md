# KERNEL SECURITY Tier-2 Runtime Kernel REPL U3 Call-Safety Sweep

Date: 2026-06-29

Scope: host-only static/source analysis for the existing v1-repl host tooling. No device action, no flash, no boot-image change, no network dependency.

## Result

Implemented `call-safety-sweep` in `workspace/public/src/scripts/revalidation/a90_repl.py`.

The sweep is advisory only. It selects bounded symbol sets by family, prefix, regex, or explicit names; runs the existing U2/C1 identity and disasm/taint path; cross-references local stock kernel source signatures from `workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel`; emits danger flags, advisory tiers, and a ranked `advisory-not-auto-callable` candidate list.

The runtime `call` gate is unchanged. Sweep results do not mutate `CALL_SAFETY_SEEDS`, do not widen `auto_call_allowed`, and do not make unseeded symbols callable.

## Source Oracle Behavior

- Pointer-typed source args never become `SAFE-SCALAR`.
- Missing or ambiguous source downgrades toward `DENY`.
- `__user`, lock/sleep annotations, and disasm context-sensitive calls become danger flags.
- Source signatures are evidence records with file, line, signature, parsed args, and pointer arg indices.

Smoke example:

- `strlcpy`: source found, advisory `SAFE-WITH-VALID-PTR`, candidate tagged `advisory-not-auto-callable`; gate tier remains `DENY`.
- `kgsl_pwrctrl_force_no_nap_store`: source missing, advisory `DENY`, danger flags include `source-missing`.

Three-family sweep smoke:

- Selector: `--family allocator --family string --family read-io --limit 20`
- Result: `decision=a90-repl-u3-call-safety-sweep-host-pass`, `host_only=true`, `device_action=false`, `network_dependency=false`
- Rows: 20 swept, 7 advisory candidates
- Gate counts: `DENY=15`, `SAFE-SCALAR=1`, `SAFE-WITH-VALID-PTR=4`
- Advisory counts: `CONTEXT-SENSITIVE=5`, `DENY=8`, `SAFE-WITH-VALID-PTR=7`

## Validation

Commands run:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl.CallSafetyClassificationTests
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_a90_repl
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-sweep --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel --no-objdump --limit 0 strlcpy kgsl_pwrctrl_force_no_nap_store
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-sweep --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --source-root workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel --no-objdump --family allocator --family string --family read-io --limit 20
```

Results:

- `py_compile`: PASS
- `CallSafetyClassificationTests`: 11/11 PASS
- Full `tests.test_a90_repl`: 61/61 PASS
- Explicit-symbol CLI smoke: PASS, `decision=a90-repl-u3-call-safety-sweep-host-pass`, `host_only=true`, `device_action=false`, `network_dependency=false`, `candidate_safe_count=1`
- Three-family CLI smoke: PASS, `families=allocator,string,read-io`, `swept_symbol_count=20`, `candidate_safe_count=7`, `host_only=true`, `device_action=false`, `network_dependency=false`

## Safety Notes

No live calls were made. No bridge, device, flash helper, boot image, or rollback path was touched. The only artifacts changed are public host tooling, tests, this report, and `GOAL.md` status.
