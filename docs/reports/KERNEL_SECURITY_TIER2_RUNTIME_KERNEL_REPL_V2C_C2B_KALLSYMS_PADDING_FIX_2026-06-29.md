# Kernel Security Tier-2 Runtime Kernel REPL v2c C2B - Kallsyms Padding Fix

- Date: 2026-06-29
- Unit: `v2c C2B`
- Decision: `a90-repl-v2c-c2b-kallsyms-padding-fix-host-pass`
- Device action: no
- Boot image changed: no
- Public code: `workspace/public/src/scripts/revalidation/a90_stock_kallsyms_extract.py`
- Tests: `tests/test_a90_stock_kallsyms_extract.py`, `tests/test_a90_repl.py`
- Regenerated private map: `workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map`
- Regenerated private metadata: `workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/stock-kallsyms.json`

## Objective

Fix the C2A map-audit root cause if it is a decoder bug, or otherwise fence the drift.
C2A showed the current v2a1 `System.map` had `0` matches and `12479` mismatches against
recovered export-record values, including the live-proven allocator symbols.

## Root Cause

The extractor computed:

```text
offsets_start = relative_base_pos - 4 * num_syms
```

That is wrong for this A90 image because `kallsyms_offsets` is followed by `95` zero
u32 padding entries before `kallsyms_relative_base`. The current formula starts the
address table `95` entries too late. The symptom was a stable name/address index drift:
for most exported symbols, the correct name index was `address_index + 95`.

Example from the old map:

- recovered `__kmalloc` address `0xffffff800826ae34` was named
  `__delete_from_swap_cache`.
- recovered `kfree` address `0xffffff800826b354` was named
  `free_page_and_swap_cache`.
- recovered `LZ4_compress_default` address `0xffffff800857a354` was named
  `pcim_iounmap_regions`.

## Fix

`find_address_table()` now counts zero u32 padding immediately before
`relative_base_pos` and subtracts it from `offsets_start`. On the v2321/v1-repl image:

- old `offsets_start`: `0x1e8087c`
- padding before relative base: `380` bytes (`95` u32 entries)
- fixed `offsets_start`: `0x1e80700`
- `text_offset`: `0x0`

The KGSL local-run repair is now a fallback only. If the corrected base-relative address
already lands on a ROPP entry and carries the expected `num_pwrlevels` marker, the
extractor leaves the base-relative decode intact. The `printk` variadic-wrapper
signature override remains necessary and unchanged.

## Host Evidence

Regenerated map command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 workspace/public/src/scripts/revalidation/a90_stock_kallsyms_extract.py \
    --kernel workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img \
    --out-map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
    --out-json workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/stock-kallsyms.json
```

Extractor summary:

- `offsets_start`: `0x1e80700`
- `padding_before_relative_base`: `380`
- `decode_sources`: `base-relative=147294`, `plain-printk-variadic-wrapper-signature=1`
- semantic cross-checks still pass for:
  - `kgsl_pwrctrl_force_no_nap_show=0xffffff8008927344`
  - `kgsl_pwrctrl_force_no_nap_store=0xffffff80089273b4`
  - `printk=0xffffff800813d8cc`

Map audit on the regenerated map:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_repl.py map-audit \
    --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map \
    --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
    --row-limit 5
```

Observed summary:

- `export_symbol_count`: `12628`
- `recovered_candidate_symbol_count`: `12490`
- `map_match`: `12480`
- `map_mismatch`: `9`
- `ambiguous`: `1`
- `missing_recovery`: `138`
- `missing_map_symbol`: `0`
- `map_match_rate`: `0.9882800126702566`

Focus rows:

- `__kmalloc`: `map-match`, map and recovered address both `0xffffff800826ae34`.
- `kfree`: `map-match`, map and recovered address both `0xffffff800826b354`.
- `printk`: still `ambiguous` under export-record recovery, so the extractor keeps the
  live-proven signature address `0xffffff800813d8cc` and the v2c resolver does not
  auto-promote either export candidate.

Validation commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_stock_kallsyms_extract.py \
  tests/test_a90_stock_kallsyms_extract.py \
  workspace/public/src/scripts/revalidation/a90_repl.py \
  tests/test_a90_repl.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_a90_stock_kallsyms_extract tests.test_a90_repl
```

Results:

- `py_compile`: pass
- `tests.test_a90_stock_kallsyms_extract` + `tests.test_a90_repl`: `53/53` pass in
  `18.984s`

## Conclusion

C2B fixes the known mm/slab name/address drift at the extractor root cause. The map is
not claimed to be perfect: `9` exported symbols still mismatch recovered candidates,
`1` is ambiguous, and `138` have no recovered candidate in this audit. Those residuals
remain fenced by v2c C1's verified resolver for dangerous `call`/`poke` targets. The
next v2c units are S1 transport stability and U1 first-class `call`/bulk `read` CLI,
followed by bounded live re-validation and rollback.
