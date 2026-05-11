# v201 Plan: Host Evidence Helper Consolidation

## Summary

v201 consolidates the private-output helper path for the v197-v200 kernel
capability tools. The goal is to keep the newer kernel collectors on a single
symlink-safe evidence writer before adding more Wi-Fi/network-facing evidence.

## Scope

- Reuse `scripts/revalidation/a90harness/evidence.py` from
  `scripts/revalidation/a90_kernel_tools.py`.
- Keep `a90_kernel_tools.py` as the kernel-specific bridge/config parser layer.
- Preserve v197-v200 command behavior and output formats.
- Re-run v197-v200 live collectors against the current v159 device.

## Non-Goals

- Do not rewrite every legacy validator in one pass.
- Do not change native-init PID1 or boot images.
- Do not change bridge, NCM, Wi-Fi, mount, tracefs, or pstore state.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_kernel_tools.py \
  scripts/revalidation/kernel_config_decode.py \
  scripts/revalidation/netfilter_inventory.py \
  scripts/revalidation/cgroup_psi_inventory.py \
  scripts/revalidation/debug_observability_plan.py
```

```bash
python3 scripts/revalidation/kernel_config_decode.py \
  --out tmp/kernel-config/v201-kernel-config.md \
  --json-out tmp/kernel-config/v201-kernel-config.json

python3 scripts/revalidation/netfilter_inventory.py \
  --out tmp/netfilter/v201-netfilter.md \
  --json-out tmp/netfilter/v201-netfilter.json

python3 scripts/revalidation/cgroup_psi_inventory.py \
  --out tmp/cgroup-psi/v201-cgroup-psi.md \
  --json-out tmp/cgroup-psi/v201-cgroup-psi.json

python3 scripts/revalidation/debug_observability_plan.py \
  --out tmp/debug-observability/v201-debug-observability.md \
  --json-out tmp/debug-observability/v201-debug-observability.json
```

## Acceptance

- v197-v200 scripts still compile.
- v197-v200 live collectors still PASS.
- `a90_kernel_tools.py` no longer owns a duplicate private writer
  implementation.
