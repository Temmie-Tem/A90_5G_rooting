# Kernel Security Tier-2 Runtime Kernel REPL v2c C1 - Fail-Closed Resolution

- Date: 2026-06-29
- Unit: `v2c C1`
- Decision: `a90-repl-v2c-c1-fail-closed-resolution-host-pass`
- Device action: no
- Boot image changed: no
- Public code: `workspace/public/src/scripts/revalidation/a90_repl.py`
- Tests: `tests/test_a90_repl.py`

## Objective

Make `System.map` untrusted by default for any `call` or `poke` target. The v2a2 live
failure proved that a name can map to a plausible JOPP-shaped function entry while still
being the wrong function. C1 therefore requires a verified resolution layer before any
dangerous live op can be dispatched.

## Implementation

Added `VerifiedResolution` and `resolve_verified(symbol, purpose=...)`:

- `purpose=call|poke` requires `verified=True` before use.
- `purpose=peek` may use `System.map`, but the result is surfaced as
  `verified=false` with method `System.map-read-only-unverified`.
- Verified allocator calls use the v2a2R' recovered-export ground truth for
  `__kmalloc` and `kfree`, not the drifted map labels.
- Other call targets must pass static map-address sanity:
  JOPP entry marker, no pre-first-`BL` `x0` dereference, at least one direct `BL`
  xref, and no known unsafe live-call marker.
- `kallsyms_lookup_name` is explicitly fail-closed because v2a1 live validation
  showed it can reboot the device.
- `run_selftest` now verifies its call target before any transport op.
- `run_poke_roundtrip` now resolves `__kmalloc`/`kfree` through the verified layer
  and rejects caller-supplied allocator address overrides that do not match verified
  ground truth.
- Repeated static image, export-candidate, and direct-`BL` xref scans are cached so
  the resolver is usable in tests and operator workflows.

## Host Evidence

Focused tests now cover the fail-closed cases:

- `__kmalloc` resolves to recovered export `0xffffff800826ae34`, verified by
  method `export-recovery`; map agreement is false.
- `kfree` resolves to recovered export `0xffffff800826b354`, verified by
  method `export-recovery`; map agreement is false.
- `printk` remains verified at the live-proven map address
  `0xffffff800813d8cc` by method `disasm-signature+xref+map`.
- `kallsyms_lookup_name` resolves as `verified=false`, method
  `blocked-known-unsafe`, and is rejected before transport.
- `kgsl_pwrctrl_force_no_nap_store` under `purpose=peek` resolves as
  `verified=false`, method `System.map-read-only-unverified`.
- A map-derived allocator override for `poke-roundtrip` is rejected before any
  REPL op reaches the fake transport.

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
- `tests.test_a90_repl`: `36/36` pass in `16.692s`

Representative CLI checks:

- `resolve printk`: `verified=true`, method `disasm-signature+xref+map`
- `resolve __kmalloc`: `verified=true`, method `export-recovery`
- `resolve kallsyms_lookup_name`: `verified=false`, method `blocked-known-unsafe`
- `resolve --purpose peek kgsl_pwrctrl_force_no_nap_store`: `verified=false`,
  method `System.map-read-only-unverified`

## Conclusion

C1 is host-complete. Dangerous named execution targets now fail closed unless the
resolver can attach verification evidence. This structurally prevents the v2a2
class where a mislabeled `System.map` allocator entry is called as if it were the
real function. v2c is not complete: C2 map-audit/decoder fencing, S1 transport
stability, U1 arbitrary-length read/call CLI surface, and bounded live
re-validation remain.
