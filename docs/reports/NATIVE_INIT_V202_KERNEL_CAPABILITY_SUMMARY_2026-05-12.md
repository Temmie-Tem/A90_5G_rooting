# v202 Kernel Capability Summary View

## Summary

v202 adds a single host-side kernel capability summary report. It merges v197
through v200 evidence with the live Wi-Fi gate, while keeping the operation
read-only.

## Changes

- Added `scripts/revalidation/kernel_capability_summary.py`.
- Added summary matrix for:
  - kernel config
  - netfilter exposure
  - cgroup/PSI
  - tracefs/pstore
  - Wi-Fi gate
- Added `--refresh` mode to regenerate v197-v200 source JSON before summarizing.

## Validation

```bash
python3 -m py_compile scripts/revalidation/kernel_capability_summary.py
```

Result: PASS.

```bash
python3 scripts/revalidation/kernel_capability_summary.py \
  --out tmp/kernel-capability/v202-kernel-capability.md \
  --json-out tmp/kernel-capability/v202-kernel-capability.json
```

Result: PASS.

```bash
python3 scripts/revalidation/kernel_capability_summary.py \
  --refresh \
  --config-json tmp/kernel-config/v202-kernel-config.json \
  --netfilter-json tmp/netfilter/v202-netfilter.json \
  --cgroup-json tmp/cgroup-psi/v202-cgroup-psi.json \
  --debug-json tmp/debug-observability/v202-debug-observability.json \
  --out tmp/kernel-capability/v202-kernel-capability-refresh.md \
  --json-out tmp/kernel-capability/v202-kernel-capability-refresh.json
```

Result: PASS.

Evidence:

- `tmp/kernel-capability/v202-kernel-capability.md`
- `tmp/kernel-capability/v202-kernel-capability.json`
- `tmp/kernel-capability/v202-kernel-capability-refresh.md`
- `tmp/kernel-capability/v202-kernel-capability-refresh.json`

Summary:

- Kernel config: PASS, CONFIG entries `5724`
- Netfilter exposure: `legacy-iptables-runtime-present`
- Cgroup/PSI: `supported-unmounted-psi-present`
- Tracefs/pstore: supported, both unmounted
- Wi-Fi gate: `baseline-required`

## Acceptance

- One report now summarizes the kernel/network/debug capability state.
- `--refresh` mode confirms the report is reproducible from live device evidence.
- No Wi-Fi, firewall, cgroup, tracefs, pstore, PID1, or boot-image state changed.

## Next

Next work can proceed to a read-only Wi-Fi baseline refresh, using the v202
summary as the preflight gate.
