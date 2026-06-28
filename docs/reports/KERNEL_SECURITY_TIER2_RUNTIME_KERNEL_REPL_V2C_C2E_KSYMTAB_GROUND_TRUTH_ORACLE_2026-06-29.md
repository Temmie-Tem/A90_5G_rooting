# Kernel Security Tier-2 Runtime Kernel REPL v2c C2E - Ksymtab Ground-Truth Oracle

- Date: 2026-06-29
- Unit: `v2c C2E`
- Decision: `a90-repl-v2c-c2e-ksymtab-ground-truth-oracle-host-pass`
- Device action: no
- Boot image changed: no
- Public code: `workspace/public/src/scripts/revalidation/a90_repl.py`
- Tests: `tests/test_a90_repl.py`, `tests/test_a90_stock_kallsyms_extract.py`

## Objective

Build a sound, at-scale export oracle that does not rely on the old C2A
name-string-reference heuristic. Use it to produce a real drift report, localize
the kallsyms decoder divergence, and decide whether to rewrite the extractor.

## Oracle Structure

The raw source-ABI `__ksymtab` rows are zero in the boot image, but the image
contains one large 24-byte `0x403` relocation record table. Each relocation
record is:

```text
u64 flags = 0x403
u64 value_to_apply
u64 target_vaddr
```

For exported symbols, two adjacent relocations reconstruct the zeroed
16-byte source row:

```text
target + 0: value pointer
target + 8: name pointer
```

`a90_repl.py ksymtab-ground-truth` now reconstructs these rows by structure:

- finds the 24-byte `0x403` relocation run;
- groups records by `target_vaddr`;
- accepts only zeroed 16-byte source rows with a valid identifier C-string name;
- selects high-density export-label target runs;
- emits a relocated `__ksymtab` oracle and drift report.

This is not the C2A name-string-ref heuristic. The name string alone never
selects an address; the authoritative row is selected by relocation target pair
and zeroed source-row structure.

## Host Evidence

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_repl.py ksymtab-ground-truth \
    --map workspace/private/runs/kernel/v2a1-repl-driver/System.map \
    --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img \
    --compare-map c2b-padding=workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map
```

Observed oracle:

- layout: `24-byte-0x403-relocation-records-reconstruct-zeroed-16-byte-ksymtab-pairs`
- selected exported rows: `12518`
- unique exported names: `12518`
- selected target range: `0xffffff800a562d60..0xffffff800a594270`
- name raw range: `0x25207d8..0x255fbfb`
- selected high-density runs: `103`

Anchor results:

- `__kmalloc`: relocated ksymtab match at `0xffffff800826ae34`.
- `kfree`: relocated ksymtab match at `0xffffff800826b354`.
- `kgsl_pwrctrl_force_no_nap_store`: not exported; semantic/map anchor match at
  `0xffffff80089273b4`.
- `printk`: semantic live-call anchor match at `0xffffff800813d8cc`; relocated
  export row points at `0xffffff800813adfc`. This conflict is explicit and is
  the reason the extractor is not rewritten in this unit.

Drift against current v2a1 map:

- audited exported rows: `12518`
- `map_match`: `0`
- `map_mismatch`: `12518`
- `missing_map_symbol`: `0`

Drift against the prior C2B padding-fix candidate map:

- audited exported rows: `12518`
- `map_match`: `12514`
- `map_mismatch`: `4`
- `missing_map_symbol`: `0`
- residual mismatches: `printk`, `ehci_reset`,
  `iio_read_channel_ext_info`, `iio_write_channel_ext_info`

## Decoder Localization

The structural oracle validates the C2B diagnosis that the current v2a1 map is
offset-index drifted for exported rows. The prior C2B padding-fix map, which
skipped the 95 zero u32 padding entries before `kallsyms_relative_base`, matches
`12514/12518` relocated export rows. That strongly localizes the main decoder
divergence to the address-offset table start, not to export string scanning.

The remaining `4` mismatches matter:

- `printk` is a semantic conflict: the relocated export row points at the normal
  export thunk, while the live-proven callable target is the Stage-C semantic
  wrapper.
- The three local-symbol residuals require separate disasm review before any
  regenerated map is promoted.

## Root-Fix Decision

Do not change `a90_stock_kallsyms_extract.py` in C2E. The padding fix is strongly
supported, but it is not yet a regression-free promoted decoder fix because:

- the `printk` export row conflicts with the live-call semantic anchor;
- the residual local-symbol mismatches need operator disasm review;
- the GOAL gate requires operator-disasm verification before replacing the map.

The safe C2E output is therefore a trust-region fence:

- exported symbols inside the relocated ksymtab scope can use this oracle for
  drift reports;
- live `call`/`poke` still require C1 fail-closed verified resolution;
- non-exported symbols remain map-only and `verified=false` unless independently
  proven;
- extractor rewrite remains gated on a later operator-verified promotion.

## Validation

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
- `tests.test_a90_repl` + `tests.test_a90_stock_kallsyms_extract`: `63/63` pass

## Conclusion

C2E now has a real relocated `__ksymtab` ground-truth oracle and an authoritative
drift report. It proves the current v2a1 map is unusable for relocated exported
rows, validates the old padding-fix hypothesis at scale, and documents why the
extractor is not rewritten in this unit. C1 fail-closed remains the live safety
boundary.
