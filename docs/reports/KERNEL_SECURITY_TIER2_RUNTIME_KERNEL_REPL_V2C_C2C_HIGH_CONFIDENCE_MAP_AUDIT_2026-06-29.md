# Kernel Security Tier-2 Runtime Kernel REPL v2c C2C - High-Confidence Map Audit

- Date: 2026-06-29
- Unit: `v2c C2C`
- Decision: `a90-repl-v2c-c2c-high-confidence-map-audit-host-pass`
- Device action: no
- Boot image changed: no
- Public code: `workspace/public/src/scripts/revalidation/a90_repl.py`
- Tests: `tests/test_a90_repl.py`, `tests/test_a90_stock_kallsyms_extract.py`

## Objective

Correct the C2A audit oracle after operator review proved the broad string-reference
`map-audit` was noisy. The fixed audit must not treat string-reference recovery as
global truth. It must reproduce the known anchors:

- `printk`: map-match at `0xffffff800813d8cc`.
- `__kmalloc`: map-mismatch, truth `0xffffff800826ae34`.
- `kfree`: map-mismatch, truth `0xffffff800826b354`.

## Implementation

`a90_repl.py map-audit` now runs a high-confidence anchor audit:

- `printk` is accepted only when the Stage-C plain-`printk` semantic signature,
  C1 `resolve_verified(...)`, and the map address all agree. The noisy string-ref
  candidates are recorded but not promoted.
- `__kmalloc` and `kfree` become map-mismatch only when there is exactly one
  passing export candidate, the candidate is a JOPP entry, has no pre-call `x0`
  dereference, has high direct-`bl` xrefs, and the map address is independently
  refuted by low xrefs and the wrong pre-call `x0` dereference shape.
- The historical C2A whole-map string-ref scanner is retained as
  `run_string_ref_map_audit(...)`, but it is not the default oracle and must not
  drive a decoder rewrite.

## Host Evidence

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_repl.py map-audit \
    --map workspace/private/runs/kernel/v2a1-repl-driver/System.map \
    --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
    --row-limit 3
```

Observed summary:

- `audited_symbol_count`: `3`
- `map_match`: `1`
- `map_mismatch`: `2`
- `unknown`: `0`
- `anchor_failures`: `[]`

Anchor rows:

- `printk`: `map-match`; truth `0xffffff800813d8cc`; map
  `0xffffff800813d8cc`; string-ref candidates include false candidates
  `0xffffff800813adfc` and `0xffffff80081b8eac`, and are not promoted.
- `__kmalloc`: `map-mismatch`; truth `0xffffff800826ae34`; map
  `0xffffff80082724bc`; selected direct-`bl` xrefs `1765`; map direct-`bl`
  xrefs `0`; map pre-call `x0` deref `+0x38/imm=0x48/word=0xf9402417`.
- `kfree`: `map-mismatch`; truth `0xffffff800826b354`; map
  `0xffffff800827276c`; selected direct-`bl` xrefs `10596`; map direct-`bl`
  xrefs `0`; map pre-call `x0` deref `+0x38/imm=0x78/word=0xf9403c08`.

Validation:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_a90_repl tests.test_a90_stock_kallsyms_extract
```

Results:

- `py_compile`: pass
- `tests.test_a90_repl` + `tests.test_a90_stock_kallsyms_extract`: `56/56` pass

## Conclusion

C2C fixes the immediate audit oracle: it reproduces the known `printk`,
`__kmalloc`, and `kfree` anchors without claiming the whole map is drifted. A broad
drift map still requires a real `__ksymtab` / `__ksymtab_strings` section parse or
another equally grounded oracle. Until that exists, `call`/`poke` remain gated by
C1 verified resolution and only high-confidence map-audit rows should be trusted.
