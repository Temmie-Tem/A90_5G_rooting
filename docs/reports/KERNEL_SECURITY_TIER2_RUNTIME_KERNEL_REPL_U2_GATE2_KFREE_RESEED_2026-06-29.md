# Kernel Security Tier-2 Runtime Kernel REPL U2 Gate-2 - kfree Reseed

- Date: 2026-06-29
- Unit: `REPL U2 Gate-2 correction`
- Decision: `a90-repl-u2-gate2-kfree-reseed-host-pass`
- Device action: no
- Boot image changed: no
- Public code:
  - `workspace/public/src/scripts/revalidation/a90_repl.py`
  - `tests/test_a90_repl.py`

## Objective

Apply the operator Gate-2 correction for U2 call safety: `kfree` is not
`SAFE-SCALAR`. A non-zero garbage scalar can fault because `kfree` consumes x0
as a pointer after aliasing it through the function body.

## Changes

- Reseeded `kfree` as `SAFE-WITH-VALID-PTR`.
- Declared required pointer arg `x0=kmalloc-object-or-NULL`.
- Strengthened `SAFE-SCALAR` from "no early `[xN]` arg deref" to a positive
  taint-flow proof: x0..x7 aliases are tracked through objdump disassembly, BL
  clears caller-clobbered aliases, and any arg-derived register used as a memory
  base invalidates `SAFE-SCALAR`.
- Kept `__kmalloc` as `SAFE-SCALAR`; its scalar x0 flow does not reach a memory
  base in the scanned body after BL return clobbers are modeled.
- Added regression coverage so `call kfree 0x1234` is refused before any
  transport operation.

## Classifier Evidence

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify \
    --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
    --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
    --no-objdump
```

Observed tier counts:

- `SAFE-SCALAR`: `1`
- `SAFE-WITH-VALID-PTR`: `8`
- `BEHAVIOR-CHANGING`: `4`
- `DENY`: `1`

Key rows:

- `__kmalloc` -> `SAFE-SCALAR`, arg-taint memory-base uses `0`
- `kfree` -> `SAFE-WITH-VALID-PTR`, required args `{"0": "kmalloc-object-or-NULL"}`
- `kfree` arg-taint memory-base uses: `43`
- first observed `kfree` tainted memory-base event:
  `0xffffff800826b444: ldr x9, [x9]`, source arg `x0`

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=tests \
  python3 -m unittest tests.test_a90_repl

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=tests \
  python3 -m unittest \
    tests.test_a90_stock_kallsyms_extract \
    tests.test_kernel_tier2_stage_c_direct_bl_printk \
    tests.test_kernel_tier2_repl_v1_repl \
    tests.test_kernel_tier2_kasan_lite_reclaim_dump
```

Results:

- `py_compile`: pass
- `tests.test_a90_repl`: `59/59` pass
- focused companion suite: `24/24` pass

## Boundary

This unit is host-only. It performs no live call-proof, no device action, and no
boot-image change.
