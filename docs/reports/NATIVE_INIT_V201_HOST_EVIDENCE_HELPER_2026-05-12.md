# v201 Host Evidence Helper Consolidation

## Summary

v201 consolidates the private evidence output path used by v197-v200 kernel
capability tooling. `a90_kernel_tools.py` now delegates private writes to the
existing harness evidence helper and remains focused on bridge capture, kernel
config parsing, and report utilities.

## Changes

- Updated `scripts/revalidation/a90_kernel_tools.py` to import private output
  helpers from `scripts/revalidation/a90harness/evidence.py`.
- Preserved v197-v200 CLI behavior and output formats.
- Deferred legacy v154-v159 collector migration because those scripts have older
  report schemas and default-version assumptions.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_kernel_tools.py \
  scripts/revalidation/kernel_config_decode.py \
  scripts/revalidation/netfilter_inventory.py \
  scripts/revalidation/cgroup_psi_inventory.py \
  scripts/revalidation/debug_observability_plan.py
```

Result: PASS.

Live collector reruns:

- `tmp/kernel-config/v201-kernel-config.json` — PASS, version match true, CONFIG entries `5724`
- `tmp/netfilter/v201-netfilter.json` — PASS, decision `legacy-iptables-runtime-present`
- `tmp/cgroup-psi/v201-cgroup-psi.json` — PASS, decision `supported-unmounted-psi-present`
- `tmp/debug-observability/v201-debug-observability.json` — PASS, version match true

## Acceptance

- Newer kernel capability collectors use the shared private evidence helper path.
- The symlink-safe/no-follow output policy remains centralized in
  `a90harness.evidence`.
- No device state or native boot image was changed.

## Next

v202 should add a single kernel capability summary view combining config,
netfilter, cgroup/PSI, tracefs/pstore, and Wi-Fi gate evidence.
