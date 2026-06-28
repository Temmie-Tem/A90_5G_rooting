# Kernel Security Tier-2 Runtime Kernel REPL v2c C2 - Map Audit

- Date: 2026-06-29
- Unit: `v2c C2A`
- Decision: `a90-repl-v2c-c2-map-audit-host-pass`
- Device action: no
- Boot image changed: no
- Public code: `workspace/public/src/scripts/revalidation/a90_repl.py`
- Tests: `tests/test_a90_repl.py`

## Objective

Stage the C2 map-trust audit before attempting the decoder root-fix. The audit must
cross-check `System.map` against export-record ground truth at scale, quantify drift,
and identify whether the map can be treated as globally trustworthy.

## Implementation

Added `a90_repl.py map-audit`:

- Extracts exported symbol names from `__ksymtab_*` entries in the current
  `System.map`.
- Scans the raw v1-repl image once for NUL-terminated exported-name strings.
- Scans aligned qwords once to find references to those strings.
- Recovers export-record candidate values using the observed record layout where
  the value qword is `24` bytes before the name-reference qword.
- For function exports, filters recovered values to JOPP-shaped entries to reduce
  false positives.
- Emits counts for map matches, mismatches, ambiguous recoveries, missing recovery,
  and mismatch region buckets.
- Includes focus rows for `__kmalloc`, `kfree`, and `printk`.

This is an audit/fencing unit only. It does not claim to fix
`a90_stock_kallsyms_extract.py`.

## Host Evidence

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_repl.py map-audit \
    --map workspace/private/runs/kernel/v2a1-repl-driver/System.map \
    --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
    --row-limit 5
```

Observed summary:

- `export_symbol_count`: `12628`
- `recovered_candidate_symbol_count`: `12490`
- `map_match`: `0`
- `map_mismatch`: `12479`
- `ambiguous`: `11`
- `missing_recovery`: `138`
- `missing_map_symbol`: `0`
- `map_match_rate`: `0.0`

Focus rows:

- `__kmalloc`: `map-mismatch`; map `0xffffff80082724bc`, recovered
  `0xffffff800826ae34`; delta `30344`.
- `kfree`: `map-mismatch`; map `0xffffff800827276c`, recovered
  `0xffffff800826b354`; delta `29720`.
- `printk`: `ambiguous`; recovered export candidates include
  `0xffffff800813adfc` and `0xffffff80081b8eac`, so the audit does not promote
  either as a replacement for the live-proven call address.

Top mismatch buckets include:

- `0xffffff8008500000`: `1409`
- `0xffffff8009700000`: `1178`
- `0xffffff8008200000`: `898`
- `0xffffff8008700000`: `844`
- `0xffffff8009600000`: `703`

Validation commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_a90_repl
```

Results:

- `py_compile`: pass
- `tests.test_a90_repl`: `37/37` pass in `26.318s`

## Conclusion

C2A audit is host-complete. The current regenerated `System.map` is not globally
trustworthy for exported function addresses. The known mm/slab drift is part of a
broader export-address drift pattern, not an isolated allocator-region problem.
The next C2 step is to fix the kallsyms decoder root cause or fence the map into
explicitly trusted regions. Until then, v2c C1's verified resolver remains the
safety boundary for `call`/`poke`.
